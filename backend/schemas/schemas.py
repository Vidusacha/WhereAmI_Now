from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models import ApprovalStatus

class AxisBase(BaseModel):
    id: str
    name_en: str
    name_ru: str
    name_he: str
    description: Optional[str] = None

class AxisCreate(AxisBase):
    pass

class AxisResponse(AxisBase):
    status: ApprovalStatus
    created_at: datetime
    class Config:
        from_attributes = True

class PartyBase(BaseModel):
    id: str
    name_en: str
    name_ru: str
    name_he: str

class PartyCreate(PartyBase):
    pass

class PartyResponse(PartyBase):
    status: ApprovalStatus
    local_storage_folder: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class StaticSourceBase(BaseModel):
    url: str
    description: Optional[str] = None

class StaticSourceCreate(StaticSourceBase):
    pass

class StaticSourceResponse(StaticSourceBase):
    id: int
    last_scraped_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True
