from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models import TaskAttachment


class ProjectAttachmentService:
    def upload_attachment(
        self,
        svc,
        db: Session,
        project_id: int,
        task_id: int | None,
        upload_file: UploadFile,
        current_user: dict,
    ) -> TaskAttachment:
        project = svc.get_project(db, project_id, current_user)
        svc._ensure_project_member(project, current_user)
        task = None
        if task_id is not None:
            task = svc.get_task(db, project_id, task_id, current_user)

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
        svc._log(
            db,
            project_id,
            current_user["id"],
            "attachment_uploaded",
            f"上传附件 {attachment.file_name}",
            task.id if task else None,
        )
        db.commit()
        return db.scalar(select(TaskAttachment).options(joinedload(TaskAttachment.uploader)).where(TaskAttachment.id == attachment.id))

    def get_attachment(self, svc, db: Session, project_id: int, attachment_id: int, current_user: dict) -> TaskAttachment:
        project = svc.get_project(db, project_id, current_user)
        svc._ensure_project_member(project, current_user)
        attachment = db.scalar(
            select(TaskAttachment)
            .options(joinedload(TaskAttachment.uploader))
            .where(TaskAttachment.project_id == project_id, TaskAttachment.id == attachment_id)
        )
        if not attachment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="附件不存在")
        return attachment

    def increase_attachment_download(self, svc, db: Session, attachment: TaskAttachment, current_user: dict) -> None:
        attachment.download_count += 1
        svc._log(
            db,
            attachment.project_id,
            current_user["id"],
            "attachment_downloaded",
            f"下载附件 {attachment.file_name}",
            attachment.task_id,
        )
        db.commit()
