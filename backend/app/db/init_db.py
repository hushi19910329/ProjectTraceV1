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
            # Lightweight SQLite migration for new columns in development mode.
            conn.execute(text("ALTER TABLE tasks ADD COLUMN tags VARCHAR(255) DEFAULT ''"))
    except Exception:
        # Column may already exist on subsequent startup.
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
