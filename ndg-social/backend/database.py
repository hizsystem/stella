from sqlalchemy import (
    create_engine, Column, Integer, String, Text,
    DateTime, ForeignKey, func
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from backend.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── 모델 ──────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="editor")  # admin/editor/viewer
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, nullable=True)


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    client_name = Column(String, nullable=False, default="HIZ-NDG")
    report_month = Column(String, nullable=False)          # "2025-03"
    status = Column(String, nullable=False, default="draft")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    data_records = relationship("ReportData", back_populates="report", cascade="all, delete-orphan")
    versions = relationship("ReportVersion", back_populates="report", cascade="all, delete-orphan")
    pipeline_runs = relationship("PipelineRun", back_populates="report", cascade="all, delete-orphan")
    slide_edits = relationship("SlideEdit", back_populates="report", cascade="all, delete-orphan")


class ReportData(Base):
    __tablename__ = "report_data"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    data_type = Column(String, nullable=False)  # raw_excel / agent_a_output / ... / user_edited
    data_json = Column(Text, nullable=False)
    agent_model = Column(String, nullable=True)
    processing_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    report = relationship("Report", back_populates="data_records")


class ReportVersion(Base):
    __tablename__ = "report_versions"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    version_label = Column(String, nullable=True)          # "초안" / "1차 수정" / "최종"
    full_data_json = Column(Text, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    report = relationship("Report", back_populates="versions")


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    agent_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending/running/completed/failed/skipped
    input_data_id = Column(Integer, ForeignKey("report_data.id"), nullable=True)
    output_data_id = Column(Integer, ForeignKey("report_data.id"), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    tokens_used = Column(Integer, nullable=True)

    report = relationship("Report", back_populates="pipeline_runs")


class SlideEdit(Base):
    __tablename__ = "slide_edits"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    slide_number = Column(Integer, nullable=False)
    field_key = Column(String, nullable=False)
    original_value = Column(Text, nullable=True)
    edited_value = Column(Text, nullable=False)
    edited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    edited_at = Column(DateTime, server_default=func.now())

    report = relationship("Report", back_populates="slide_edits")


def create_tables():
    Base.metadata.create_all(bind=engine)
