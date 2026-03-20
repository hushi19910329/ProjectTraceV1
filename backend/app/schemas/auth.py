from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    account: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("account")
    @classmethod
    def normalize_account(cls, value: str) -> str:
        return value.strip()


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    menus: list[dict]
