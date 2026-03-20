from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.config import settings
from app.models import (
    Notification,
    OperationLog,
    Project,
    ProjectMember,
    ProjectNode,
    project_watchers,
    Task,
    TaskAttachment,
    TaskComment,
    TaskStatusUpdate,
    User,
)
from app.schemas.project_management import (
    CommentCreate,
    ProjectCreate,
    ProjectUpdate,
    ReminderCreate,
    TaskAbandonPayload,
    TaskCreate,
    TaskStatusUpdateCreate,
    TaskUpdate,
)
from app.services.user_service import user_service


class ProjectService:
    @staticmethod
    def _serialize_user(user: User | None) -> dict | None:
        if not user:
            return None
        return {
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name,
            "avatar_url": user.avatar_url,
        }

    def _project_detail_query(self):
        return (
            select(Project)
            .options(
                joinedload(Project.owner),
                joinedload(Project.creator),
                selectinload(Project.members).joinedload(ProjectMember.user),
                selectinload(Project.nodes).joinedload(ProjectNode.owner),
                selectinload(Project.tasks),
                selectinload(Project.watchers),
            )
            .order_by(Project.id.desc())
        )

    def _project_list_query(self):
        return (
            select(Project)
            .options(
                joinedload(Project.owner),
                joinedload(Project.creator),
                selectinload(Project.tasks),
            )
            .order_by(Project.id.desc())
        )

    def _task_detail_query(self):
        return (
            select(Task)
            .options(
                joinedload(Task.creator),
                joinedload(Task.assignee),
                joinedload(Task.project),
                joinedload(Task.node),
                selectinload(Task.collaborators),
                selectinload(Task.watchers),
                selectinload(Task.comments).joinedload(TaskComment.author),
                selectinload(Task.comments).selectinload(TaskComment.mentioned_users),
                selectinload(Task.attachments).joinedload(TaskAttachment.uploader),
                selectinload(Task.status_updates).joinedload(TaskStatusUpdate.operator),
            )
            .order_by(Task.id.desc())
        )

    def _task_list_query(self):
        return (
            select(Task)
            .options(
                joinedload(Task.creator),
                joinedload(Task.assignee),
                joinedload(Task.project),
                joinedload(Task.node),
                selectinload(Task.collaborators),
                selectinload(Task.watchers),
                selectinload(Task.status_updates).joinedload(TaskStatusUpdate.operator),
            )
            .order_by(Task.id.desc())
        )

    def _apply_project_filters(self, stmt, current_user: dict, filters: dict):
        if not current_user.get("is_superuser"):
            stmt = stmt.join(Project.members).where(ProjectMember.user_id == current_user["id"])
        if filters.get("keyword"):
            keyword = f"%{filters['keyword'].strip()}%"
            stmt = stmt.where(or_(Project.name.ilike(keyword), Project.description.ilike(keyword), Project.goal.ilike(keyword)))
        if filters.get("status"):
            stmt = stmt.where(Project.status == filters["status"])
        if filters.get("priority"):
            stmt = stmt.where(Project.priority == filters["priority"])
        if filters.get("owner_id"):
            stmt = stmt.where(Project.owner_id == int(filters["owner_id"]))
        if filters.get("tag"):
            tag = str(filters["tag"]).strip()
            stmt = stmt.where(Project.tags.ilike(f"%{tag}%"))
        if filters.get("followed"):
            stmt = stmt.join(project_watchers, project_watchers.c.project_id == Project.id).where(
                project_watchers.c.user_id == current_user["id"]
            )
        return stmt

    def list_projects(self, db: Session, current_user: dict) -> list[Project]:
        items, _ = self.list_projects_with_filters(db, current_user, {}, page=1, page_size=20)
        return items

    def list_projects_with_filters(
        self,
        db: Session,
        current_user: dict,
        filters: dict,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Project], int]:
        base_stmt = self._apply_project_filters(select(Project.id), current_user, filters)
        total_stmt = select(func.count()).select_from(base_stmt.distinct().subquery())
        total = db.scalar(total_stmt) or 0
        if total == 0:
            return [], 0

        id_page_stmt = (
            base_stmt.distinct()
            .order_by(Project.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        page_ids = list(db.scalars(id_page_stmt).all())
        if not page_ids:
            return [], total

        stmt = self._project_list_query().where(Project.id.in_(page_ids))
        projects = list(db.scalars(stmt).unique().all())
        order_map = {item_id: idx for idx, item_id in enumerate(page_ids)}
        projects.sort(key=lambda item: order_map.get(item.id, len(order_map)))
        return projects, total

    def list_project_tags(
        self,
        db: Session,
        current_user: dict,
        keyword: str | None = None,
        limit: int = 20,
    ) -> tuple[list[str], int]:
        tag_stmt = self._apply_project_filters(select(Project.tags), current_user, {})
        raw_tags = db.scalars(tag_stmt).all()
        tag_set: set[str] = set()
        for value in raw_tags:
            for raw in (value or "").split(","):
                tag = raw.strip()
                if tag:
                    tag_set.add(tag)
        items = sorted(tag_set)
        if keyword:
            key = keyword.strip().lower()
            items = [item for item in items if key in item.lower()]
        total = len(items)
        return items[: max(1, limit)], total

    def get_project(self, db: Session, project_id: int, current_user: dict) -> Project:
        stmt = self._project_detail_query().where(Project.id == project_id)
        if not current_user.get("is_superuser"):
            stmt = stmt.join(Project.members).where(ProjectMember.user_id == current_user["id"])
        project = db.scalar(stmt)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在或无访问权限")
        return project

    def _ensure_users(self, db: Session, user_ids: list[int]) -> list[User]:
        unique_ids = list(dict.fromkeys(user_ids))
        if not unique_ids:
            return []
        stmt = select(User).where(User.id.in_(unique_ids))
        users = list(db.scalars(stmt).all())
        if len(users) != len(unique_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="存在无效的用户")
        return users

    def create_project(self, db: Session, payload: ProjectCreate, current_user: dict) -> Project:
        duplicate = db.scalar(select(Project).where((Project.code == payload.code) | (Project.name == payload.name)))
        if duplicate:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="项目编号或名称已存在")

        owner = user_service.get_user_by_id(db, payload.owner_id)
        if not owner:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="项目负责人不存在")

        member_ids = list(dict.fromkeys([payload.owner_id, *payload.member_ids, current_user["id"]]))
        members = self._ensure_users(db, member_ids)

        project = Project(
            code=payload.code,
            name=payload.name,
            description=payload.description,
            status=payload.status,
            priority=payload.priority,
            owner_id=payload.owner_id,
            created_by_id=current_user["id"],
            start_date=payload.start_date,
            end_date=payload.end_date,
            goal=payload.goal,
            tags=",".join(payload.tags),
        )
        db.add(project)
        db.flush()

        member_roles = {
            current_user["id"]: "manager",
            payload.owner_id: "owner",
        }
        for member in members:
            db.add(
                ProjectMember(
                    project_id=project.id,
                    user_id=member.id,
                    role=member_roles.get(member.id, "member"),
                )
            )

        nodes = payload.nodes or []
        if not nodes:
            nodes = [
                {
                    "name": "项目启动",
                    "description": "默认初始化节点",
                    "sequence": 1,
                    "status": "not_started",
                    "owner_id": payload.owner_id,
                    "start_date": payload.start_date,
                    "end_date": payload.end_date,
                    "output_summary": "",
                }
            ]
        for node in nodes:
            data = node.model_dump() if hasattr(node, "model_dump") else node
            db.add(ProjectNode(project_id=project.id, **data))

        self._log(
            db,
            project_id=project.id,
            operator_id=current_user["id"],
            action="project_created",
            detail=f"创建项目 {payload.name}",
        )
        db.commit()
        return self.get_project(db, project.id, current_user)

    def update_project(self, db: Session, project_id: int, payload: ProjectUpdate, current_user: dict) -> Project:
        project = self.get_project(db, project_id, current_user)

        if payload.owner_id is not None:
            owner = user_service.get_user_by_id(db, payload.owner_id)
            if not owner:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="项目负责人不存在")
            project.owner_id = payload.owner_id
        if payload.name is not None:
            project.name = payload.name
        if payload.description is not None:
            project.description = payload.description
        if payload.status is not None:
            project.status = payload.status
        if payload.priority is not None:
            project.priority = payload.priority
        if payload.start_date is not None:
            project.start_date = payload.start_date
        if payload.end_date is not None:
            project.end_date = payload.end_date
        if payload.goal is not None:
            project.goal = payload.goal
        if payload.tags is not None:
            project.tags = ",".join(payload.tags)
        if payload.member_ids is not None:
            member_ids = list(dict.fromkeys([project.owner_id, *payload.member_ids, current_user["id"]]))
            users = self._ensure_users(db, member_ids)
            project.members.clear()
            member_roles = {current_user["id"]: "manager", project.owner_id: "owner"}
            for user in users:
                project.members.append(ProjectMember(user_id=user.id, role=member_roles.get(user.id, "member")))
        if project.owner_id:
            owner = user_service.get_user_by_id(db, project.owner_id)
            if owner and owner not in project.watchers:
                project.watchers.append(owner)

        self._log(
            db,
            project_id=project.id,
            operator_id=current_user["id"],
            action="project_updated",
            detail=f"更新项目 {project.name}",
        )
        db.commit()
        return self.get_project(db, project.id, current_user)

    def get_project_members(self, project: Project) -> list[int]:
        return [item.user_id for item in project.members]

    def _ensure_project_member(self, project: Project, current_user: dict) -> None:
        if current_user.get("is_superuser"):
            return
        if current_user["id"] not in self.get_project_members(project):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前用户不在该项目协作范围内")

    def list_tasks(
        self,
        db: Session,
        project_id: int,
        current_user: dict,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Task], int]:
        project = self.get_project(db, project_id, current_user)
        self._ensure_project_member(project, current_user)
        total = db.scalar(select(func.count()).where(Task.project_id == project_id)) or 0
        if total == 0:
            return [], 0
        stmt = (
            self._task_list_query()
            .where(Task.project_id == project_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(db.scalars(stmt).unique().all()), total

    def _apply_task_filters(self, stmt, current_user: dict, filters: dict):
        if not current_user.get("is_superuser"):
            stmt = stmt.join(ProjectMember, ProjectMember.project_id == Task.project_id).where(
                ProjectMember.user_id == current_user["id"]
            )
        if filters.get("keyword"):
            keyword = f"%{filters['keyword'].strip()}%"
            stmt = stmt.where(or_(Task.title.ilike(keyword), Task.description.ilike(keyword)))
        if filters.get("status"):
            stmt = stmt.where(Task.status == filters["status"])
        if filters.get("priority"):
            stmt = stmt.where(Task.priority == filters["priority"])
        if filters.get("assignee_id"):
            stmt = stmt.where(Task.assignee_id == int(filters["assignee_id"]))
        if filters.get("tag"):
            stmt = stmt.where(Task.tags.ilike(f"%{str(filters['tag']).strip()}%"))
        if filters.get("followed"):
            stmt = stmt.join(Task.watchers).where(User.id == current_user["id"])
        return stmt

    def list_all_tasks_with_filters(
        self,
        db: Session,
        current_user: dict,
        filters: dict,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Task], int]:
        base_stmt = self._apply_task_filters(select(Task.id), current_user, filters)
        total_stmt = select(func.count()).select_from(base_stmt.distinct().subquery())
        total = db.scalar(total_stmt) or 0
        if total == 0:
            return [], 0

        id_page_stmt = (
            base_stmt.distinct()
            .order_by(Task.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        page_ids = list(db.scalars(id_page_stmt).all())
        if not page_ids:
            return [], total

        stmt = self._task_list_query().where(Task.id.in_(page_ids))
        tasks = list(db.scalars(stmt).unique().all())
        order_map = {item_id: idx for idx, item_id in enumerate(page_ids)}
        tasks.sort(key=lambda item: order_map.get(item.id, len(order_map)))
        return tasks, total

    def get_task(self, db: Session, project_id: int, task_id: int, current_user: dict) -> Task:
        project = self.get_project(db, project_id, current_user)
        self._ensure_project_member(project, current_user)
        task = db.scalar(self._task_detail_query().where(Task.project_id == project_id, Task.id == task_id))
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
        return task

    def create_task(self, db: Session, project_id: int, payload: TaskCreate, current_user: dict) -> Task:
        project = self.get_project(db, project_id, current_user)
        self._ensure_project_member(project, current_user)

        member_ids = self.get_project_members(project)
        if payload.node_id is not None:
            node = db.scalar(select(ProjectNode).where(ProjectNode.project_id == project_id, ProjectNode.id == payload.node_id))
            if not node:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="节点不存在")
        if payload.parent_task_id is not None:
            parent = db.scalar(select(Task).where(Task.project_id == project_id, Task.id == payload.parent_task_id))
            if not parent:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="父任务不存在")
        if payload.assignee_id is not None and payload.assignee_id not in member_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="负责人必须是项目成员")
        if any(user_id not in member_ids for user_id in payload.collaborator_ids + payload.watcher_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="协作人或关注人必须是项目成员")

        collaborators = self._ensure_users(db, payload.collaborator_ids)
        watchers = self._ensure_users(db, payload.watcher_ids)
        assignee_id = payload.assignee_id or current_user["id"]

        task = Task(
            project_id=project_id,
            node_id=payload.node_id,
            parent_task_id=payload.parent_task_id,
            title=payload.title,
            description=payload.description,
            task_type=payload.task_type,
            status=payload.status,
            priority=payload.priority,
            tags=",".join(payload.tags),
            progress=payload.progress,
            creator_id=current_user["id"],
            assignee_id=assignee_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            estimated_hours=payload.estimated_hours,
            actual_hours=payload.actual_hours,
            acceptance_criteria=payload.acceptance_criteria,
            collaborators=collaborators,
            watchers=watchers,
        )
        db.add(task)
        db.flush()
        self._append_status_update(
            db,
            task=task,
            operator_id=current_user["id"],
            status=task.status,
            progress=task.progress,
            actual_hours=task.actual_hours,
            content="任务已创建",
        )
        self._log(db, project_id, current_user["id"], "task_created", f"创建任务 {task.title}", task.id)
        if assignee_id and assignee_id != current_user["id"]:
            self._notify(db, assignee_id, project_id, task.id, "task_assigned", "收到任务分配", f"任务：{task.title}")
        db.commit()
        return self.get_task(db, project_id, task.id, current_user)

    def update_task(self, db: Session, project_id: int, task_id: int, payload: TaskUpdate, current_user: dict) -> Task:
        task = self.get_task(db, project_id, task_id, current_user)
        project = task.project
        member_ids = self.get_project_members(project)
        prev_status = task.status
        prev_progress = task.progress
        prev_actual_hours = task.actual_hours
        status_changed = False

        if payload.node_id is not None:
            node = db.scalar(select(ProjectNode).where(ProjectNode.project_id == project_id, ProjectNode.id == payload.node_id))
            if not node:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="节点不存在")
            task.node_id = payload.node_id
        if payload.title is not None:
            task.title = payload.title
        if payload.description is not None:
            task.description = payload.description
        if payload.task_type is not None:
            task.task_type = payload.task_type
        if payload.status is not None:
            task.status = payload.status
            if payload.status == "done":
                task.progress = 100
            status_changed = True
        if payload.priority is not None:
            task.priority = payload.priority
        if payload.tags is not None:
            task.tags = ",".join(payload.tags)
        if payload.assignee_id is not None:
            if payload.assignee_id not in member_ids:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="负责人必须是项目成员")
            task.assignee_id = payload.assignee_id
            if payload.assignee_id != current_user["id"]:
                self._notify(db, payload.assignee_id, project_id, task.id, "task_assigned", "任务负责人已调整", f"任务：{task.title}")
        if payload.collaborator_ids is not None:
            if any(user_id not in member_ids for user_id in payload.collaborator_ids):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="协作人必须是项目成员")
            task.collaborators = self._ensure_users(db, payload.collaborator_ids)
        if payload.watcher_ids is not None:
            if any(user_id not in member_ids for user_id in payload.watcher_ids):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="关注人必须是项目成员")
            task.watchers = self._ensure_users(db, payload.watcher_ids)
        if payload.start_date is not None:
            task.start_date = payload.start_date
        if payload.end_date is not None:
            task.end_date = payload.end_date
        if payload.estimated_hours is not None:
            task.estimated_hours = payload.estimated_hours
        if payload.actual_hours is not None:
            task.actual_hours = payload.actual_hours
            status_changed = True
        if payload.progress is not None:
            task.progress = payload.progress
            if payload.progress == 100 and task.status != "done":
                task.status = "done"
            status_changed = True
        if payload.acceptance_criteria is not None:
            task.acceptance_criteria = payload.acceptance_criteria

        if status_changed and (
            task.status != prev_status or task.progress != prev_progress or task.actual_hours != prev_actual_hours
        ):
            self._append_status_update(
                db,
                task=task,
                operator_id=current_user["id"],
                status=task.status,
                progress=task.progress,
                actual_hours=task.actual_hours,
                content="任务状态已更新",
            )

        self._log(db, project_id, current_user["id"], "task_updated", f"更新任务 {task.title}", task.id)
        db.commit()
        return self.get_task(db, project_id, task.id, current_user)

    def abandon_task(self, db: Session, project_id: int, task_id: int, payload: TaskAbandonPayload, current_user: dict) -> Task:
        task = self.get_task(db, project_id, task_id, current_user)
        task.is_abandoned = True
        task.status = "abandoned"
        task.abandoned_reason = payload.reason
        self._append_status_update(
            db,
            task=task,
            operator_id=current_user["id"],
            status=task.status,
            progress=task.progress,
            actual_hours=task.actual_hours,
            content=f"任务已废弃：{payload.reason}",
        )
        self._log(db, project_id, current_user["id"], "task_abandoned", f"废弃任务 {task.title}: {payload.reason}", task.id)
        db.commit()
        return self.get_task(db, project_id, task.id, current_user)

    def add_task_status_update(
        self,
        db: Session,
        project_id: int,
        task_id: int,
        payload: TaskStatusUpdateCreate,
        current_user: dict,
    ) -> Task:
        task = self.get_task(db, project_id, task_id, current_user)
        member_ids = self.get_project_members(task.project)

        if payload.assignee_id is not None:
            if payload.assignee_id not in member_ids:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="负责人必须是项目成员")
            task.assignee_id = payload.assignee_id
            if payload.assignee_id != current_user["id"]:
                self._notify(
                    db,
                    payload.assignee_id,
                    project_id,
                    task.id,
                    "task_assigned",
                    "任务负责人已调整",
                    f"任务：{task.title}",
                )

        task.status = payload.status
        task.progress = payload.progress
        task.actual_hours = payload.actual_hours
        if task.status == "done":
            task.progress = 100
        if task.progress == 100 and task.status != "done":
            task.status = "done"
        if task.status == "abandoned":
            task.is_abandoned = True
        elif task.is_abandoned:
            task.is_abandoned = False
            task.abandoned_reason = ""

        self._append_status_update(
            db,
            task=task,
            operator_id=current_user["id"],
            status=task.status,
            progress=task.progress,
            actual_hours=task.actual_hours,
            content=payload.content,
        )
        self._log(db, project_id, current_user["id"], "task_status_updated", f"更新任务状态 {task.title}", task.id)
        db.commit()
        return self.get_task(db, project_id, task.id, current_user)

    def add_comment(self, db: Session, project_id: int, task_id: int, payload: CommentCreate, current_user: dict) -> TaskComment:
        task = self.get_task(db, project_id, task_id, current_user)
        member_ids = self.get_project_members(task.project)
        if any(user_id not in member_ids for user_id in payload.mentioned_user_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="@用户必须是项目成员")
        mentioned_users = self._ensure_users(db, payload.mentioned_user_ids)
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
                self._notify(
                    db,
                    user.id,
                    project_id,
                    task.id,
                    "comment_mention",
                    "你被任务评论@了",
                    f"任务：{task.title}",
                )
        self._log(db, project_id, current_user["id"], "comment_added", f"在任务 {task.title} 下发表评论", task.id)
        db.commit()
        return db.scalar(
            select(TaskComment)
            .options(joinedload(TaskComment.author), selectinload(TaskComment.mentioned_users))
            .where(TaskComment.id == comment.id)
        )

    def upload_attachment(
        self,
        db: Session,
        project_id: int,
        task_id: int | None,
        upload_file: UploadFile,
        current_user: dict,
    ) -> TaskAttachment:
        project = self.get_project(db, project_id, current_user)
        self._ensure_project_member(project, current_user)
        task = None
        if task_id is not None:
            task = self.get_task(db, project_id, task_id, current_user)

        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(upload_file.filename or "attachment").suffix
        stored_name = f"{uuid4().hex}{suffix}"
        file_path = settings.upload_dir / stored_name
        content = upload_file.file.read()
        file_path.write_bytes(content)

        attachment = TaskAttachment(
            project_id=project_id,
            task_id=task.id if task else None,
            file_name=upload_file.filename or stored_name,
            stored_name=stored_name,
            file_path=str(file_path),
            file_type=upload_file.content_type or "application/octet-stream",
            file_size=len(content),
            uploaded_by_id=current_user["id"],
        )
        db.add(attachment)
        db.flush()
        self._log(
            db,
            project_id,
            current_user["id"],
            "attachment_uploaded",
            f"上传附件 {attachment.file_name}",
            task.id if task else None,
        )
        db.commit()
        return db.scalar(select(TaskAttachment).options(joinedload(TaskAttachment.uploader)).where(TaskAttachment.id == attachment.id))

    def get_attachment(self, db: Session, project_id: int, attachment_id: int, current_user: dict) -> TaskAttachment:
        project = self.get_project(db, project_id, current_user)
        self._ensure_project_member(project, current_user)
        attachment = db.scalar(
            select(TaskAttachment)
            .options(joinedload(TaskAttachment.uploader))
            .where(TaskAttachment.project_id == project_id, TaskAttachment.id == attachment_id)
        )
        if not attachment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="附件不存在")
        return attachment

    def increase_attachment_download(self, db: Session, attachment: TaskAttachment, current_user: dict) -> None:
        attachment.download_count += 1
        self._log(
            db,
            attachment.project_id,
            current_user["id"],
            "attachment_downloaded",
            f"下载附件 {attachment.file_name}",
            attachment.task_id,
        )
        db.commit()

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

    def follow_project(self, db: Session, project_id: int, current_user: dict) -> None:
        project = self.get_project(db, project_id, current_user)
        user = user_service.get_user_by_id(db, current_user["id"])
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        if user not in project.watchers:
            project.watchers.append(user)
            self._log(db, project_id, current_user["id"], "project_followed", f"关注项目 {project.name}")
            db.commit()

    def unfollow_project(self, db: Session, project_id: int, current_user: dict) -> None:
        project = self.get_project(db, project_id, current_user)
        user = user_service.get_user_by_id(db, current_user["id"])
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        if user in project.watchers:
            project.watchers.remove(user)
            self._log(db, project_id, current_user["id"], "project_unfollowed", f"取消关注项目 {project.name}")
            db.commit()

    def follow_task(self, db: Session, project_id: int, task_id: int, current_user: dict) -> None:
        task = self.get_task(db, project_id, task_id, current_user)
        user = user_service.get_user_by_id(db, current_user["id"])
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        if user not in task.watchers:
            task.watchers.append(user)
            self._log(db, project_id, current_user["id"], "task_followed", f"关注任务 {task.title}", task.id)
            db.commit()

    def unfollow_task(self, db: Session, project_id: int, task_id: int, current_user: dict) -> None:
        task = self.get_task(db, project_id, task_id, current_user)
        user = user_service.get_user_by_id(db, current_user["id"])
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        if user in task.watchers:
            task.watchers.remove(user)
            self._log(db, project_id, current_user["id"], "task_unfollowed", f"取消关注任务 {task.title}", task.id)
            db.commit()

    def create_reminder(self, db: Session, project_id: int, task_id: int, payload: ReminderCreate, current_user: dict) -> None:
        task = self.get_task(db, project_id, task_id, current_user)
        member_ids = self.get_project_members(task.project)
        if any(user_id not in member_ids for user_id in payload.user_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="提醒对象必须是项目成员")
        for user_id in payload.user_ids:
            if user_id != current_user["id"]:
                self._notify(db, user_id, project_id, task_id, "manual_reminder", "任务提醒", payload.content)
        self._log(db, project_id, current_user["id"], "task_reminded", f"提醒协作成员关注任务 {task.title}", task.id)
        db.commit()

    def list_logs(self, db: Session, project_id: int, current_user: dict) -> list[OperationLog]:
        project = self.get_project(db, project_id, current_user)
        self._ensure_project_member(project, current_user)
        stmt = (
            select(OperationLog)
            .options(joinedload(OperationLog.operator))
            .where(OperationLog.project_id == project_id)
            .order_by(OperationLog.id.desc())
        )
        return list(db.scalars(stmt).all())

    def _notify(
        self,
        db: Session,
        user_id: int,
        project_id: int,
        task_id: int | None,
        notification_type: str,
        title: str,
        content: str,
    ) -> None:
        db.add(
            Notification(
                user_id=user_id,
                project_id=project_id,
                task_id=task_id,
                notification_type=notification_type,
                title=title,
                content=content,
            )
        )

    def _log(
        self,
        db: Session,
        project_id: int,
        operator_id: int,
        action: str,
        detail: str,
        task_id: int | None = None,
    ) -> None:
        db.add(
            OperationLog(
                project_id=project_id,
                task_id=task_id,
                operator_id=operator_id,
                action=action,
                detail=detail,
            )
        )

    def serialize_project(self, project: Project) -> dict:
        return {
            "id": project.id,
            "code": project.code,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "priority": project.priority,
            "owner": self._serialize_user(project.owner),
            "creator": self._serialize_user(project.creator),
            "start_date": project.start_date,
            "end_date": project.end_date,
            "goal": project.goal,
            "tags": [item for item in project.tags.split(",") if item],
            "members": [
                {
                    "id": member.user.id,
                    "role": member.role,
                    "user": self._serialize_user(member.user),
                }
                for member in project.members
            ],
            "watchers": [self._serialize_user(item) for item in project.watchers],
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "description": node.description,
                    "sequence": node.sequence,
                    "status": node.status,
                    "owner": self._serialize_user(node.owner),
                    "start_date": node.start_date,
                    "end_date": node.end_date,
                    "output_summary": node.output_summary,
                }
                for node in sorted(project.nodes, key=lambda item: item.sequence)
            ],
            "task_summary": self._build_task_summary(project.tasks),
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
        }

    def _build_task_summary(self, tasks: list[Task]) -> dict:
        total = len(tasks)
        done = len([item for item in tasks if item.status == "done"])
        abandoned = len([item for item in tasks if item.is_abandoned or item.status == "abandoned"])
        blocked = len([item for item in tasks if item.status == "blocked"])
        return {
            "total": total,
            "done": done,
            "abandoned": abandoned,
            "blocked": blocked,
            "progress": 0 if total == 0 else round(sum(item.progress for item in tasks) / total, 2),
        }

    def serialize_task(self, task: Task) -> dict:
        return {
            "id": task.id,
            "project_id": task.project_id,
            "project_name": task.project.name if task.project else "",
            "node_id": task.node_id,
            "parent_task_id": task.parent_task_id,
            "title": task.title,
            "description": task.description,
            "task_type": task.task_type,
            "status": task.status,
            "priority": task.priority,
            "tags": [item for item in task.tags.split(",") if item],
            "progress": task.progress,
            "creator": self._serialize_user(task.creator),
            "assignee": self._serialize_user(task.assignee),
            "collaborators": [self._serialize_user(item) for item in task.collaborators],
            "watchers": [self._serialize_user(item) for item in task.watchers],
            "node": None if not task.node else {"id": task.node.id, "name": task.node.name},
            "start_date": task.start_date,
            "end_date": task.end_date,
            "estimated_hours": task.estimated_hours,
            "actual_hours": task.actual_hours,
            "acceptance_criteria": task.acceptance_criteria,
            "is_abandoned": task.is_abandoned,
            "abandoned_reason": task.abandoned_reason,
            "comments": [
                {
                    "id": comment.id,
                    "content": comment.content,
                    "author": self._serialize_user(comment.author),
                    "mentioned_users": [self._serialize_user(item) for item in comment.mentioned_users],
                    "created_at": comment.created_at.isoformat(),
                }
                for comment in task.comments
            ],
            "status_updates": [
                {
                    "id": item.id,
                    "status": item.status,
                    "progress": item.progress,
                    "actual_hours": item.actual_hours,
                    "content": item.content,
                    "operator": self._serialize_user(item.operator),
                    "created_at": item.created_at.isoformat(),
                }
                for item in sorted(task.status_updates, key=lambda value: value.id, reverse=True)
            ],
            "attachments": [
                {
                    "id": attachment.id,
                    "file_name": attachment.file_name,
                    "file_type": attachment.file_type,
                    "file_size": attachment.file_size,
                    "download_count": attachment.download_count,
                    "uploader": self._serialize_user(attachment.uploader),
                    "created_at": attachment.created_at.isoformat(),
                }
                for attachment in task.attachments
            ],
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
        }

    def _append_status_update(
        self,
        db: Session,
        *,
        task: Task,
        operator_id: int,
        status: str,
        progress: int,
        actual_hours: int,
        content: str,
    ) -> None:
        db.add(
            TaskStatusUpdate(
                task_id=task.id,
                status=status,
                progress=progress,
                actual_hours=actual_hours,
                content=content,
                operator_id=operator_id,
            )
        )


project_service = ProjectService()
