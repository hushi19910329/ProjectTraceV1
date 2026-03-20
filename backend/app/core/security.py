from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.auth_service import auth_service


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已失效",
        )

    token = authorization.replace("Bearer ", "", 1).strip()
    user = auth_service.get_user_by_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的登录状态",
        )

    return user


def require_superuser(user: dict = Depends(get_current_user)) -> dict:
    if not user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可以执行该操作",
        )
    return user
