from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from typing import Literal


class EntityBase(BaseModel):
    external_id: Optional[str] = None
    source: str
    name: str
    slug: str
    summary: Optional[str] = None
    description: Optional[str] = None
    entity_type: str = "Product"
    status: Literal["PENDING", "VALIDATED", "DUPLICATE_CANDIDATE", "ARCHIVED"] = "PENDING"


class EntityCreate(EntityBase):
    raw_json: Optional[dict] = None


class EntityResponse(EntityBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EntityAttributeBase(BaseModel):
    key: str
    value: str
    datatype: Literal["STRING", "NUMBER", "BOOLEAN", "DATE", "URL", "EMAIL"] = "STRING"
    source: str


class EntityAttributeCreate(EntityAttributeBase):
    entity_id: str


class BackgroundJobBase(BaseModel):
    job_type: Literal["ingest", "dedup", "quality", "export"]
    status: Literal["queued", "running", "done", "failed"] = "queued"
    payload: Optional[dict] = None


class BackgroundJobCreate(BackgroundJobBase):
    pass


class BackgroundJobResponse(BackgroundJobBase):
    id: str
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class IngestSourceRequest(BaseModel):
    sources: list[str] = Field(default_factory=lambda: ["internal_mysql"])


class HealthResponse(BaseModel):
    status: str
    last_ingest: Optional[str] = None