from pydantic import BaseModel, EmailStr
from typing import Optional, Any
from datetime import datetime


# ── Auth ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str = "editor"

class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: str
    password: str


# ── Report ────────────────────────────────────────────────────────────────────

class ReportCreate(BaseModel):
    title: str
    client_name: str = "HIZ-NDG"
    report_month: str           # "2025-03"

class ReportOut(BaseModel):
    id: int
    title: str
    client_name: str
    report_month: str
    status: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class SlideUpdateRequest(BaseModel):
    field_key: str
    new_value: str

class VersionCreate(BaseModel):
    version_label: Optional[str] = None


# ── Pipeline ──────────────────────────────────────────────────────────────────

class PipelineStatusOut(BaseModel):
    report_id: int
    status: str
    current_agent: Optional[str]
    progress_pct: int
    runs: list[dict]

class ChangeLogAcceptRequest(BaseModel):
    accept_indices: list[int]   # which change_log items to accept
    reject_indices: list[int]


# ── Export ────────────────────────────────────────────────────────────────────

class ExportStatusOut(BaseModel):
    report_id: int
    export_status: str
    download_url: Optional[str]
