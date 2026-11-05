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
