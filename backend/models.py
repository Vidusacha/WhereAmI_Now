from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()

class ApprovalStatus(enum.Enum):
    PENDING_AI_PROPOSAL = "pending_ai_proposal"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"

class Axis(Base):
    __tablename__ = "axes"
    id = Column(String, primary_key=True) # e.g., "economy"
    name_en = Column(String, nullable=False)
    name_ru = Column(String, nullable=False)
    name_he = Column(String, nullable=False)
    description = Column(Text)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING_AI_PROPOSAL)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = relationship("Question", back_populates="axis")
    party_scores = relationship("PartyScore", back_populates="axis")

class Party(Base):
    __tablename__ = "parties"
    id = Column(String, primary_key=True)
    name_en = Column(String, nullable=False, unique=True)
    name_ru = Column(String, nullable=False, unique=True)
    name_he = Column(String, nullable=False, unique=True)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING_AI_PROPOSAL)
    
    # NEW: Offline Storage Path (Ready for S3)
    local_storage_folder = Column(String, nullable=True) # e.g., "/data/parties/likud/"
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    scores = relationship("PartyScore", back_populates="party")
    documents = relationship("ScrapedDocument", back_populates="party")

class StaticSource(Base):
    __tablename__ = "static_sources"
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    last_scraped_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ScrapedDocument(Base):
    __tablename__ = "scraped_documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    party_id = Column(String, ForeignKey("parties.id"), nullable=True)
    axis_id = Column(String, ForeignKey("axes.id"), nullable=True)
    static_source_id = Column(Integer, ForeignKey("static_sources.id"), nullable=True) # If it came from a static source
    source_url = Column(String, nullable=False)
    file_path = Column(String, nullable=False) # Local or S3 path to the PDF/HTML
    scraped_at = Column(DateTime, default=datetime.utcnow)
    
    party = relationship("Party", back_populates="documents")
    static_source = relationship("StaticSource")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    questionnaire_version = Column(String, default="v2.0")
    axis_id = Column(String, ForeignKey("axes.id"))
    text_en = Column(String, nullable=False)
    text_ru = Column(String, nullable=False)
    text_he = Column(String, nullable=False)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING_AI_PROPOSAL)
    
    axis = relationship("Axis", back_populates="questions")

class PartyScore(Base):
    __tablename__ = "party_scores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    party_id = Column(String, ForeignKey("parties.id"))
    axis_id = Column(String, ForeignKey("axes.id"))
    score = Column(Float, nullable=False) # e.g., -1.0 to 1.0
    confidence = Column(Float, nullable=True) # How confident AI is based on documents
    justification_en = Column(Text) # AI reasoning
    
    party = relationship("Party", back_populates="scores")
    axis = relationship("Axis", back_populates="party_scores")
