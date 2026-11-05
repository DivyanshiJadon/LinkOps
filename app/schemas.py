from datetime import datetime
from pydantic import BaseModel, HttpUrl, ConfigDict, Field


class LinkCreate(BaseModel):
    long_url: HttpUrl
    expires_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    custom_code: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$"
    )

class LinkResponse(BaseModel):
    id: int
    code: str
    short_url: str
    long_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRegister(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
