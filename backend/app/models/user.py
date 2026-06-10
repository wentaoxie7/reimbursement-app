from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    manager_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    organization: Mapped["Organization"] = relationship(back_populates="users")  # noqa: F821
    role_assignments: Mapped[list["UserRoleAssignment"]] = relationship(back_populates="user")  # noqa: F821
    expenses: Mapped[list["Expense"]] = relationship(back_populates="owner")  # noqa: F821
