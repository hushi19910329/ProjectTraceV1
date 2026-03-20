from sqlalchemy import text, select
from sqlalchemy.orm import Session

from app.db.postgres import Base, engine
from app.models import Permission, Role, User
from app.services.auth_service import auth_service


PERMISSIONS = [
    ("dashboard", "工作台"),
    ("project", "项目管理"),
    ("requirement", "需求管理"),
    ("task", "任务管理"),
    ("test", "测试缺陷"),
    ("collaboration", "工时协同"),
    ("okr-report", "OKR与报表"),
    ("system", "系统管理"),
]

ROLES = [
    ("admin", "系统管理员", [item[0] for item in PERMISSIONS]),
    ("project-manager", "项目经理", ["dashboard", "project", "requirement", "task", "test", "collaboration", "okr-report"]),
    ("developer", "开发人员", ["dashboard", "project", "task", "test", "collaboration"]),
]


def init_database() -> None:
    Base.metadata.create_all(bind=engine)
    try:
        with engine.begin() as conn:
            # Lightweight migration for new columns in development mode.
            conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS tags VARCHAR(255) DEFAULT ''"))
            conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS project_type VARCHAR(16) DEFAULT 'work'"))
    except Exception:
        # Column may already exist on subsequent startup.
        pass

    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500) DEFAULT ''"))
    except Exception:
        pass

    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_projects_priority ON projects(priority)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_projects_project_type ON projects(project_type)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at DESC)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_parent_task_id ON tasks(parent_task_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_assignee_id ON tasks(assignee_id)"))
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_project_members_project_user ON project_members(project_id, user_id)")
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_project_watchers_project_user ON project_watchers(project_id, user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_task_watchers_task_user ON task_watchers(task_id, user_id)"))
    except Exception:
        pass

    with Session(engine) as db:
        existing_permissions = {item.code: item for item in db.scalars(select(Permission)).all()}
        for code, label in PERMISSIONS:
            if code not in existing_permissions:
                permission = Permission(code=code, label=label)
                db.add(permission)
        db.commit()

        permission_map = {item.code: item for item in db.scalars(select(Permission)).all()}
        existing_roles = {item.code: item for item in db.scalars(select(Role)).all()}
        for code, label, permission_codes in ROLES:
            role = existing_roles.get(code)
            if not role:
                role = Role(code=code, label=label)
                db.add(role)
                db.flush()
            role.label = label
            role.permissions = [permission_map[item] for item in permission_codes]
        db.commit()

        admin_user = db.scalar(select(User).where(User.username == "admin"))
        if not admin_user:
            admin_role = db.scalar(select(Role).where(Role.code == "admin"))
            admin_user = User(
                username="admin",
                real_name="系统管理员",
                mobile="13800000000",
                password_hash=auth_service.hash_password("admin123"),
                status="active",
                is_superuser=True,
                roles=[admin_role] if admin_role else [],
            )
            db.add(admin_user)

        pm_user = db.scalar(select(User).where(User.username == "pm01"))
        if not pm_user:
            pm_role = db.scalar(select(Role).where(Role.code == "project-manager"))
            pm_user = User(
                username="pm01",
                real_name="项目经理",
                mobile="13900000000",
                password_hash=auth_service.hash_password("pm123456"),
                status="active",
                is_superuser=False,
                roles=[pm_role] if pm_role else [],
            )
            db.add(pm_user)

        db.commit()
