import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ApproverRule(str, enum.Enum):
    FIXED_USER = "FIXED_USER"
    ROLE = "ROLE"
    DEPARTMENT_HEAD = "DEPARTMENT_HEAD"
    SUBMITTER_MANAGER = "SUBMITTER_MANAGER"


class ApprovalInstanceStatus(str, enum.Enum):
    PENDING = "PENDING"
    STEP_ACTIVE = "STEP_ACTIVE"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class ActionType(str, enum.Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class ApprovalSequence(Base):
    __tablename__ = "approval_sequences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_default: Mapped[bool] = mapped_column(default=False)
    active: Mapped[bool] = mapped_column(default=True)

    steps: Mapped[list["ApprovalStep"]] = relationship(back_populates="sequence", order_by="ApprovalStep.step_order")


class ApprovalStep(Base):
    __tablename__ = "approval_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    sequence_id: Mapped[str] = mapped_column(String(36), ForeignKey("approval_sequences.id"), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    approver_rule: Mapped[ApproverRule] = mapped_column(SAEnum(ApproverRule), nullable=False)
    fixed_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    role_code: Mapped[str | None] = mapped_column(String(64))

    sequence: Mapped["ApprovalSequence"] = relationship(back_populates="steps")


class ApprovalInstance(Base):
    __tablename__ = "approval_instances"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    expense_id: Mapped[str] = mapped_column(String(36), ForeignKey("expenses.id"), unique=True)
    sequence_id: Mapped[str] = mapped_column(String(36), ForeignKey("approval_sequences.id"))
    current_step_order: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[ApprovalInstanceStatus] = mapped_column(
        SAEnum(ApprovalInstanceStatus), default=ApprovalInstanceStatus.PENDING
    )

    expense: Mapped["Expense"] = relationship(back_populates="approval_instance")  # noqa: F821
    actions: Mapped[list["ApprovalAction"]] = relationship(back_populates="instance")


class ApprovalAction(Base):
    __tablename__ = "approval_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    instance_id: Mapped[str] = mapped_column(String(36), ForeignKey("approval_instances.id"))
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    action: Mapped[ActionType] = mapped_column(SAEnum(ActionType), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    acted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    instance: Mapped["ApprovalInstance"] = relationship(back_populates="actions")
