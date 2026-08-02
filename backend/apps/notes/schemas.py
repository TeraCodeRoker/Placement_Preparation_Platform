"""Notes request/response contracts."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NoteCreate(BaseModel):
    title: str
    subject: str = ""
    content_or_url: str
    approved: bool = False


class NoteUpdate(BaseModel):
    title: str | None = None
    subject: str | None = None
    content_or_url: str | None = None
    approved: bool | None = None


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    subject: str
    content_or_url: str
    approved: bool
    created_at: datetime
