from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Permission, Role, User
from app.services.rbac_service import build_effective_permissions


class UserService:
    @staticmethod
    def list_users(db: Session) -> list[User]:
        stmt = select(User).options(selectinload(User.roles).selectinload(Role.permissions)).order_by(User.id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id == user_id)
        )
        return db.scalar(stmt)

    @staticmethod
    def get_user_by_account(db: Session, account: str) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where((User.username == account) | (User.mobile == account))
        )
        return db.scalar(stmt)

    @staticmethod
    def get_user_by_username_or_mobile(db: Session, username: str, mobile: str, exclude_user_id: int | None = None) -> User | None:
        stmt = select(User).where((User.username == username) | (User.mobile == mobile))
        if exclude_user_id is not None:
            stmt = stmt.where(User.id != exclude_user_id)
        return db.scalar(stmt)

    @staticmethod
    def list_roles(db: Session) -> list[Role]:
        stmt = select(Role).options(selectinload(Role.permissions)).order_by(Role.id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_roles_by_ids(db: Session, role_ids: list[int]) -> list[Role]:
        if not role_ids:
            return []
        stmt = select(Role).options(selectinload(Role.permissions)).where(Role.id.in_(role_ids))
        return list(db.scalars(stmt).all())

    @staticmethod
    def list_permissions(db: Session) -> list[Permission]:
        stmt = select(Permission).order_by(Permission.id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def serialize_user(user: User) -> dict:
        role_codes = [role.code for role in user.roles]
        role_permission_codes = {role.code: [permission.code for permission in role.permissions] for role in user.roles}
        module_permissions = build_effective_permissions(role_codes, role_permission_codes)
        return {
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name,
            "mobile": user.mobile,
            "status": user.status,
            "is_superuser": user.is_superuser,
            "role_ids": [role.id for role in user.roles],
            "roles": [{"id": role.id, "code": role.code, "label": role.label} for role in user.roles],
            "module_permissions": module_permissions,
        }


user_service = UserService()
