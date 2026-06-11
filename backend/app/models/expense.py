import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExpenseStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    IN_APPROVAL = "IN_APPROVAL"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"
    ARCHIVED = "ARCHIVED"


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    expense_type_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("expense_types.id"), nullable=True)
    status: Mapped[ExpenseStatus] = mapped_column(SAEnum(ExpenseStatus), default=ExpenseStatus.DRAFT)
    field_values: Mapped[dict] = mapped_column(JSONB, default=dict)
    schema_version_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("field_schema_versions.id"))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="expenses")  # noqa: F821
    receipts: Mapped[list["Receipt"]] = relationship(back_populates="expense")
    approval_instance: Mapped["ApprovalInstance | None"] = relationship(  # noqa: F821
        back_populates="expense", uselist=False
    )


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    expense_id: Mapped[str] = mapped_column(String(36), ForeignKey("expenses.id"), nullable=False)
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(128))

    expense: Mapped["Expense"] = relationship(back_populates="receipts")


class ArchiveRecord(Base):
    __tablename__ = "archive_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    expense_id: Mapped[str] = mapped_column(String(36), ForeignKey("expenses.id"), unique=True)
    bundle_path: Mapped[str] = mapped_column(String(512), nullable=False)
    archived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
