from pathlib import Path
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.init_db import init_database
from app.db.postgres import engine
from app.models import Role, User
from app.services.auth_service import auth_service


DEFAULT_PASSWORD = "Project@123"


def role_by_code(db: Session, code: str) -> Role:
    role = db.scalar(select(Role).where(Role.code == code))
    if not role:
        raise RuntimeError(f"role not found: {code}")
    return role


def create_user_if_missing(
    db: Session,
    *,
    username: str,
    real_name: str,
    mobile: str,
    role: Role,
    is_superuser: bool = False,
) -> tuple[str, str]:
    exists = db.scalar(select(User).where((User.username == username) | (User.mobile == mobile)))
    if exists:
        return username, "exists"

    user = User(
        username=username,
        real_name=real_name,
        mobile=mobile,
        password_hash=auth_service.hash_password(DEFAULT_PASSWORD),
        status="active",
        is_superuser=is_superuser,
        roles=[role],
    )
    db.add(user)
    return username, "created"


def build_accounts() -> list[dict]:
    items: list[dict] = []
    mobile_base = 13920000000

    def add(group: str, count: int, username_prefix: str, name_prefix: str, role_code: str, is_superuser: bool = False):
        nonlocal mobile_base
        for i in range(1, count + 1):
            items.append(
                {
                    "group": group,
                    "username": f"{username_prefix}{i:02d}",
                    "real_name": f"{name_prefix}{i}",
                    "mobile": str(mobile_base),
                    "role_code": role_code,
                    "is_superuser": is_superuser,
                }
            )
            mobile_base += 1

    add("公司领导", 2, "leader", "公司领导", "admin", True)
    add("项目经理", 4, "pm", "项目经理", "project-manager")
    add("前端开发", 4, "fe", "前端开发", "developer")
    add("后端开发", 4, "be", "后端开发", "developer")
    add("算法", 2, "algo", "算法工程师", "developer")
    add("测试", 2, "qa", "测试工程师", "developer")
    add("UI设计师", 2, "ui", "UI设计师", "developer")
    add("运维工程师", 2, "ops", "运维工程师", "developer")
    add("商务经理", 1, "biz", "商务经理", "project-manager")
    return items


def main() -> None:
    init_database()
    plan = build_accounts()

    with Session(engine) as db:
        roles = {
            "admin": role_by_code(db, "admin"),
            "project-manager": role_by_code(db, "project-manager"),
            "developer": role_by_code(db, "developer"),
        }

        created = 0
        exists = 0
        print(f"Default password: {DEFAULT_PASSWORD}")
        print("-----")
        for item in plan:
            username, status = create_user_if_missing(
                db,
                username=item["username"],
                real_name=item["real_name"],
                mobile=item["mobile"],
                role=roles[item["role_code"]],
                is_superuser=item["is_superuser"],
            )
            print(f"{item['group']} | {username} | {item['mobile']} | {item['role_code']} | {status}")
            if status == "created":
                created += 1
            else:
                exists += 1

        db.commit()
        print("-----")
        print(f"created: {created}, exists: {exists}, total-plan: {len(plan)}")


if __name__ == "__main__":
    main()
