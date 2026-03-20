from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.rbac_service import build_menus_from_permissions
from app.services.user_service import user_service

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class AuthService:
    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        return pwd_context.verify(plain_password, password_hash)

    def hash_password(self, plain_password: str) -> str:
        return pwd_context.hash(plain_password)

    def create_access_token(self, subject: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        payload = {"sub": subject, "exp": expire}
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    def decode_token(self, token: str) -> dict | None:
        try:
            return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        except JWTError:
            return None

    def authenticate(self, db: Session, account: str, password: str) -> dict | None:
        user = user_service.get_user_by_account(db, account)
        if not user or user.status != "active":
            return None
        if not self.verify_password(password, user.password_hash):
            return None

        serialized = user_service.serialize_user(user)
        access_token = self.create_access_token(str(user.id))
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": serialized,
            "menus": build_menus_from_permissions(serialized["module_permissions"]),
        }

    def get_user_by_token(self, db: Session, token: str) -> dict | None:
        payload = self.decode_token(token)
        if not payload or "sub" not in payload:
            return None
        user = user_service.get_user_by_id(db, int(payload["sub"]))
        return user_service.serialize_user(user) if user else None


auth_service = AuthService()
