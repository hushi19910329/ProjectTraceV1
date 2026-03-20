from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_superuser
from app.db.session import get_db
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
from app.services.project_service import project_service

router = APIRouter()


@router.get("")
def list_projects(
    keyword: str | None = Query(default=None),
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    owner_id: int | None = Query(default=None),
    tag: str | None = Query(default=None),
    followed: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    filters = {
        "keyword": keyword,
        "status": status,
        "priority": priority,
        "owner_id": owner_id,
        "tag": tag,
        "followed": followed,
    }
    page_items, total = project_service.list_projects_with_filters(
        db,
        user,
        filters,
        page=page,
        page_size=page_size,
    )
    items = [project_service.serialize_project(item) for item in page_items]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/meta/tags")
def list_project_tags(
    keyword: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    items, total = project_service.list_project_tags(db, user, keyword=keyword, limit=limit)
    return {"items": items, "total": total, "has_more": total > len(items)}


@router.post("")
def create_project(
    payload: ProjectCreate,
    user: dict = Depends(require_superuser),
    db: Session = Depends(get_db),
) -> dict:
    project = project_service.create_project(db, payload, user)
    return project_service.serialize_project(project)


@router.get("/{project_id}")
def get_project(project_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    project = project_service.get_project(db, project_id, user)
    return project_service.serialize_project(project)


@router.put("/{project_id}")
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    user: dict = Depends(require_superuser),
    db: Session = Depends(get_db),
) -> dict:
    project = project_service.update_project(db, project_id, payload, user)
    return project_service.serialize_project(project)


@router.get("/{project_id}/tasks")
def list_tasks(project_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    items = [project_service.serialize_task(item) for item in project_service.list_tasks(db, project_id, user)]
    return {"items": items}


@router.get("/tasks/all")
def list_all_tasks(
    keyword: str | None = Query(default=None),
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    assignee_id: int | None = Query(default=None),
    tag: str | None = Query(default=None),
    followed: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    filters = {
        "keyword": keyword,
        "status": status,
        "priority": priority,
        "assignee_id": assignee_id,
        "tag": tag,
        "followed": followed,
    }
    task_items, total = project_service.list_all_tasks_with_filters(
        db,
        user,
        filters,
        page=page,
        page_size=page_size,
    )
    items = [project_service.serialize_task(item) for item in task_items]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/{project_id}/tasks")
def create_task(
    project_id: int,
    payload: TaskCreate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    task = project_service.create_task(db, project_id, payload, user)
    return project_service.serialize_task(task)


@router.get("/{project_id}/tasks/{task_id}")
def get_task(project_id: int, task_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    task = project_service.get_task(db, project_id, task_id, user)
    return project_service.serialize_task(task)


@router.put("/{project_id}/tasks/{task_id}")
def update_task(
    project_id: int,
    task_id: int,
    payload: TaskUpdate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    task = project_service.update_task(db, project_id, task_id, payload, user)
    return project_service.serialize_task(task)


@router.post("/{project_id}/tasks/{task_id}/abandon")
def abandon_task(
    project_id: int,
    task_id: int,
    payload: TaskAbandonPayload,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    task = project_service.abandon_task(db, project_id, task_id, payload, user)
    return project_service.serialize_task(task)


@router.post("/{project_id}/tasks/{task_id}/comments")
def add_comment(
    project_id: int,
    task_id: int,
    payload: CommentCreate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    comment = project_service.add_comment(db, project_id, task_id, payload, user)
    return {
        "id": comment.id,
        "content": comment.content,
        "author": project_service._serialize_user(comment.author),
        "mentioned_users": [project_service._serialize_user(item) for item in comment.mentioned_users],
        "created_at": comment.created_at.isoformat(),
    }


@router.post("/{project_id}/tasks/{task_id}/status-updates")
def add_task_status_update(
    project_id: int,
    task_id: int,
    payload: TaskStatusUpdateCreate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    task = project_service.add_task_status_update(db, project_id, task_id, payload, user)
    return project_service.serialize_task(task)


@router.post("/{project_id}/tasks/{task_id}/attachments")
def upload_task_attachment(
    project_id: int,
    task_id: int,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    attachment = project_service.upload_attachment(db, project_id, task_id, file, user)
    return {
        "id": attachment.id,
        "file_name": attachment.file_name,
        "file_type": attachment.file_type,
        "file_size": attachment.file_size,
        "download_count": attachment.download_count,
        "uploader": project_service._serialize_user(attachment.uploader),
        "created_at": attachment.created_at.isoformat(),
    }


@router.get("/{project_id}/attachments/{attachment_id}/download")
def download_attachment(
    project_id: int,
    attachment_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    attachment = project_service.get_attachment(db, project_id, attachment_id, user)
    project_service.increase_attachment_download(db, attachment, user)
    return FileResponse(
        path=Path(attachment.file_path),
        filename=attachment.file_name,
        media_type=attachment.file_type,
    )


@router.post("/{project_id}/tasks/{task_id}/reminders")
def create_reminder(
    project_id: int,
    task_id: int,
    payload: ReminderCreate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    project_service.create_reminder(db, project_id, task_id, payload, user)
    return {"message": "提醒已发送"}


@router.get("/{project_id}/logs")
def list_logs(project_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    items = [
        {
            "id": item.id,
            "action": item.action,
            "detail": item.detail,
            "task_id": item.task_id,
            "operator": project_service._serialize_user(item.operator),
            "created_at": item.created_at.isoformat(),
        }
        for item in project_service.list_logs(db, project_id, user)
    ]
    return {"items": items}


@router.get("/notifications/me")
def list_notifications(user: dict = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    items = [
        {
            "id": item.id,
            "project_id": item.project_id,
            "task_id": item.task_id,
            "notification_type": item.notification_type,
            "title": item.title,
            "content": item.content,
            "is_read": item.is_read,
            "created_at": item.created_at.isoformat(),
        }
        for item in project_service.list_notifications(db, user)
    ]
    return {"items": items}


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    item = project_service.mark_notification_read(db, notification_id, user)
    return {"id": item.id, "is_read": item.is_read}


@router.post("/notifications/read-all")
def mark_all_notifications_read(user: dict = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    count = project_service.mark_all_notifications_read(db, user)
    return {"message": "全部已读", "count": count}


@router.post("/{project_id}/follow")
def follow_project(project_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    project_service.follow_project(db, project_id, user)
    return {"message": "已关注项目"}


@router.delete("/{project_id}/follow")
def unfollow_project(project_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    project_service.unfollow_project(db, project_id, user)
    return {"message": "已取消关注项目"}


@router.post("/{project_id}/tasks/{task_id}/follow")
def follow_task(project_id: int, task_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    project_service.follow_task(db, project_id, task_id, user)
    return {"message": "已关注任务"}


@router.delete("/{project_id}/tasks/{task_id}/follow")
def unfollow_task(project_id: int, task_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    project_service.unfollow_task(db, project_id, task_id, user)
    return {"message": "已取消关注任务"}
