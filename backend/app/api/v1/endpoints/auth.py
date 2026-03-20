from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.auth import LoginRequest, LoginResponse
from app.core.security import get_current_user
from app.db.session import get_db
from app.services.auth_service import auth_service
from app.services.rbac_service import build_menus_from_permissions

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    result = auth_service.authenticate(db, payload.account, payload.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名/手机号或密码错误",
        )
    return result


@router.get("/me")
def current_user(user: dict = Depends(get_current_user)) -> dict:
    return {
        "user": user,
        "menus": build_menus_from_permissions(user["module_permissions"]),
    }
