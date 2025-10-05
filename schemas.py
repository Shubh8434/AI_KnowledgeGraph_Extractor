from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class NodeSchema(BaseModel):
    id: str
    label: str
    type: str


class EdgeSchema(BaseModel):
    source: str
    target: str
    relationship: str


class GraphResponse(BaseModel):
    document_id: str
    version: int
    nodes: List[dict]
    edges: List[dict]


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    upload_date: datetime
    status: str
    message: Optional[str] = None


class VersionInfo(BaseModel):
    version_number: int
    created_at: datetime


class VersionListResponse(BaseModel):
    document_id: int
    versions: List[dict]