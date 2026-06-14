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

class EntityTypeBase(BaseModel):
    id: str
    name_en: str
    name_ru: str
    name_he: str

class EntityTypeCreate(EntityTypeBase):
    pass

class EntityTypeResponse(EntityTypeBase):
    class Config:
        from_attributes = True

class PoliticalEntityBase(BaseModel):
    id: str
    name_en: str
    name_ru: str
    name_he: str
    entity_type_id: Optional[str] = None

class PoliticalEntityCreate(PoliticalEntityBase):
    pass

class PoliticalEntityResponse(PoliticalEntityBase):
    status: ApprovalStatus
    local_storage_folder: Optional[str] = None
    created_at: datetime
    doc_count: int = 0
    last_updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    axis_id: str
    text_en: str
    text_ru: str
    text_he: str
    questionnaire_version: str = "v2.0"

class QuestionCreate(QuestionBase):
    pass

class QuestionResponse(QuestionBase):
    id: int
    status: ApprovalStatus
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
