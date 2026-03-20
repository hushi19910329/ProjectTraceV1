from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.services.auth_service import auth_service
from app.services.menu_service import get_available_modules
from app.services.user_service import user_service
from app.models import User

router = APIRouter(prefix="/users")


@router.get("", response_model=UserListResponse)
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    items, total = user_service.list_users_paginated(db, page=page, page_size=page_size)
    return {
        "items": [user_service.serialize_user(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=UserResponse)
def create_user(payload: UserCreate, _: dict = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    try:
        duplicate = user_service.get_user_by_username_or_mobile(db, payload.username, payload.mobile)
        if duplicate:
            raise ValueError("用户名或手机号已存在")
        roles = user_service.get_roles_by_ids(db, payload.role_ids)
        if len(roles) != len(payload.role_ids):
            raise ValueError("角色不存在或已失效")
        user = User(
            username=payload.username,
            real_name=payload.real_name,
            mobile=payload.mobile,
            avatar_url=payload.avatar_url,
            password_hash=auth_service.hash_password(payload.password),
            status=payload.status,
            is_superuser=False,
            roles=roles,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user_service.serialize_user(user_service.get_user_by_id(db, user.id))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UserUpdate, _: dict = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    try:
        user = user_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        duplicate = user_service.get_user_by_username_or_mobile(db, user.username, payload.mobile or user.mobile, exclude_user_id=user_id)
        if duplicate:
            raise ValueError("用户名或手机号已存在")
        if payload.real_name is not None:
            user.real_name = payload.real_name
        if payload.mobile is not None:
            user.mobile = payload.mobile
        if payload.avatar_url is not None:
            user.avatar_url = payload.avatar_url
        if payload.password:
            user.password_hash = auth_service.hash_password(payload.password)
        if payload.status is not None:
            user.status = payload.status
        if payload.role_ids is not None:
            roles = user_service.get_roles_by_ids(db, payload.role_ids)
            if len(roles) != len(payload.role_ids):
                raise ValueError("角色不存在或已失效")
            user.roles = roles
        db.commit()
        db.refresh(user)
        user = user_service.get_user_by_id(db, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return user_service.serialize_user(user)


@router.delete("/{user_id}")
def delete_user(user_id: int, _: dict = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    db.delete(user)
    db.commit()
    return {"message": "删除成功"}


@router.get("/meta/modules")
def list_permission_modules(_: dict = Depends(get_current_user)) -> dict:
    return {"items": get_available_modules()}


@router.get("/meta/roles")
def list_roles(_: dict = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    items = [
        {
            "id": role.id,
            "code": role.code,
            "label": role.label,
            "permission_codes": [permission.code for permission in role.permissions],
        }
        for role in user_service.list_roles(db)
    ]
    return {"items": items}
