from __future__ import annotations

from app.models import Project, Task, User


class ProjectSerializerService:
    @staticmethod
    def serialize_user(user: User | None) -> dict | None:
        if not user:
            return None
        return {
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name,
            "avatar_url": user.avatar_url,
        }

    def build_task_summary(self, tasks: list[Task]) -> dict:
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

    def serialize_project(self, project: Project) -> dict:
        return {
            "id": project.id,
            "code": project.code,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "priority": project.priority,
            "project_type": project.project_type,
            "owner": self.serialize_user(project.owner),
            "creator": self.serialize_user(project.creator),
            "start_date": project.start_date,
            "end_date": project.end_date,
            "goal": project.goal,
            "tags": [item for item in project.tags.split(",") if item],
            "members": [
                {
                    "id": member.user.id,
                    "role": member.role,
                    "user": self.serialize_user(member.user),
                }
                for member in project.members
            ],
            "watchers": [self.serialize_user(item) for item in project.watchers],
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "description": node.description,
                    "sequence": node.sequence,
                    "status": node.status,
                    "owner": self.serialize_user(node.owner),
                    "start_date": node.start_date,
                    "end_date": node.end_date,
                    "output_summary": node.output_summary,
                }
                for node in sorted(project.nodes, key=lambda item: item.sequence)
            ],
            "task_summary": self.build_task_summary(project.tasks),
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
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
            "creator": self.serialize_user(task.creator),
            "assignee": self.serialize_user(task.assignee),
            "collaborators": [self.serialize_user(item) for item in task.collaborators],
            "watchers": [self.serialize_user(item) for item in task.watchers],
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
                    "author": self.serialize_user(comment.author),
                    "mentioned_users": [self.serialize_user(item) for item in comment.mentioned_users],
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
                    "operator": self.serialize_user(item.operator),
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
                    "uploader": self.serialize_user(attachment.uploader),
                    "created_at": attachment.created_at.isoformat(),
                }
                for attachment in task.attachments
            ],
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
        }
