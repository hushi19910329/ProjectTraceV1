from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    real_name: str = Field(min_length=1, max_length=32)
    mobile: str = Field(min_length=11, max_length=20)
    password: str = Field(min_length=1, max_length=128)
    status: str = "active"
    role_ids: list[int] = Field(default_factory=list)

    @field_validator("username", "real_name", "mobile")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    real_name: str | None = Field(default=None, min_length=1, max_length=32)
    mobile: str | None = Field(default=None, min_length=11, max_length=20)
    password: str | None = Field(default=None, min_length=1, max_length=128)
    status: str | None = None
    role_ids: list[int] | None = None

    @field_validator("real_name", "mobile")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class UserResponse(BaseModel):
    id: int
    username: str
    real_name: str
    mobile: str
    status: str
    role_ids: list[int]
    roles: list[dict]
    module_permissions: list[str]


class UserListResponse(BaseModel):
    items: list[UserResponse]
