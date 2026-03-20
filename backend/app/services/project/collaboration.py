from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import Notification, OperationLog, Task, TaskComment, User
from app.schemas.project_management import CommentCreate, ReminderCreate
from app.services.user_service import user_service


class ProjectCollaborationService:
    def add_comment(self, svc, db: Session, project_id: int, task_id: int, payload: CommentCreate, current_user: dict) -> TaskComment:
        task = svc.get_task(db, project_id, task_id, current_user)
        member_ids = svc.get_project_members(task.project)
        if any(user_id not in member_ids for user_id in payload.mentioned_user_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="@用户必须是项目成员")
        mentioned_users = svc._ensure_users(db, payload.mentioned_user_ids)
        comment = TaskComment(
            task_id=task.id,
            content=payload.content,
            author_id=current_user["id"],
            mentioned_users=mentioned_users,
        )
        db.add(comment)
        db.flush()
        for user in mentioned_users:
            if user.id != current_user["id"]:
                svc._notify(
                    db,
                    user.id,
                    project_id,
                    task.id,
                    "comment_mention",
                    "你被任务评论@了",
                    f"任务：{task.title}",
                )
        svc._log(db, project_id, current_user["id"], "comment_added", f"在任务 {task.title} 下发表评论", task.id)
        db.commit()
        return db.scalar(
            select(TaskComment)
            .options(joinedload(TaskComment.author), selectinload(TaskComment.mentioned_users))
            .where(TaskComment.id == comment.id)
        )

    def list_notifications(self, db: Session, current_user: dict) -> list[Notification]:
        stmt = select(Notification).where(Notification.user_id == current_user["id"]).order_by(Notification.id.desc())
        return list(db.scalars(stmt).all())

    def mark_notification_read(self, db: Session, notification_id: int, current_user: dict) -> Notification:
        notification = db.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == current_user["id"],
            )
        )
        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="通知不存在")
        notification.is_read = True
        db.commit()
        return notification

    def mark_all_notifications_read(self, db: Session, current_user: dict) -> int:
        notifications = list(
            db.scalars(select(Notification).where(Notification.user_id == current_user["id"], Notification.is_read.is_(False))).all()
        )
        for notification in notifications:
            notification.is_read = True
        db.commit()
        return len(notifications)

    def follow_project(self, svc, db: Session, project_id: int, current_user: dict) -> None:
        project = svc.get_project(db, project_id, current_user)
        user = user_service.get_user_by_id(db, current_user["id"])
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        if user not in project.watchers:
            project.watchers.append(user)
            svc._log(db, project_id, current_user["id"], "project_followed", f"关注项目 {project.name}")
            db.commit()

    def unfollow_project(self, svc, db: Session, project_id: int, current_user: dict) -> None:
        project = svc.get_project(db, project_id, current_user)
        user = user_service.get_user_by_id(db, current_user["id"])
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        if user in project.watchers:
            project.watchers.remove(user)
            svc._log(db, project_id, current_user["id"], "project_unfollowed", f"取消关注项目 {project.name}")
            db.commit()

    def follow_task(self, svc, db: Session, project_id: int, task_id: int, current_user: dict) -> None:
        task = svc.get_task(db, project_id, task_id, current_user)
        user = user_service.get_user_by_id(db, current_user["id"])
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        if user not in task.watchers:
            task.watchers.append(user)
            svc._log(db, project_id, current_user["id"], "task_followed", f"关注任务 {task.title}", task.id)
            db.commit()

    def unfollow_task(self, svc, db: Session, project_id: int, task_id: int, current_user: dict) -> None:
        task = svc.get_task(db, project_id, task_id, current_user)
        user = user_service.get_user_by_id(db, current_user["id"])
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        if user in task.watchers:
            task.watchers.remove(user)
            svc._log(db, project_id, current_user["id"], "task_unfollowed", f"取消关注任务 {task.title}", task.id)
            db.commit()

    def create_reminder(self, svc, db: Session, project_id: int, task_id: int, payload: ReminderCreate, current_user: dict) -> None:
        task = svc.get_task(db, project_id, task_id, current_user)
        member_ids = svc.get_project_members(task.project)
        if any(user_id not in member_ids for user_id in payload.user_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="提醒对象必须是项目成员")
        for user_id in payload.user_ids:
            if user_id != current_user["id"]:
                svc._notify(db, user_id, project_id, task_id, "manual_reminder", "任务提醒", payload.content)
        svc._log(db, project_id, current_user["id"], "task_reminded", f"提醒协作成员关注任务 {task.title}", task.id)
        db.commit()

    def list_logs(self, svc, db: Session, project_id: int, current_user: dict) -> list[OperationLog]:
        project = svc.get_project(db, project_id, current_user)
        svc._ensure_project_member(project, current_user)
        stmt = (
            select(OperationLog)
            .options(joinedload(OperationLog.operator))
            .where(OperationLog.project_id == project_id)
            .order_by(OperationLog.id.desc())
        )
        return list(db.scalars(stmt).all())
