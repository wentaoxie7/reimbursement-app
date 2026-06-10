import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FieldType(str, enum.Enum):
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    DATE = "DATE"
    SELECT = "SELECT"
    FILE = "FILE"
    CURRENCY = "CURRENCY"


class ExpenseFieldDefinition(Base):
    __tablename__ = "expense_field_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    field_key: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    field_type: Mapped[FieldType] = mapped_column(SAEnum(FieldType), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    options: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    validation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class FieldSchemaVersion(Base):
    __tablename__ = "field_schema_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[list] = mapped_column(JSONB, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)


class ConfigAuditLog(Base):
    __tablename__ = "config_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    changed_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    diff: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
