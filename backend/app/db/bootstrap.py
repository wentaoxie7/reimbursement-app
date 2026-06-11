from sqlalchemy import inspect, text

from app.db.base import Base
from app.db.session import engine
from app.models import (  # noqa: F401
    ApprovalAction,
    ApprovalInstance,
    ApprovalSequence,
    ApprovalStep,
    ArchiveRecord,
    ConfigAuditLog,
    Expense,
    ExpenseFieldDefinition,
    ExpenseType,
    FieldSchemaVersion,
    Organization,
    Permission,
    Receipt,
    Role,
    RolePageAccess,
    RolePermission,
    User,
    UserRoleAssignment,
)


def ensure_database_schema() -> None:
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    field_columns = {column["name"] for column in inspector.get_columns("expense_field_definitions")}
    expense_columns = {column["name"] for column in inspector.get_columns("expenses")}

    with engine.begin() as connection:
        if "expense_type_id" not in field_columns:
            connection.execute(text("ALTER TABLE expense_field_definitions ADD COLUMN expense_type_id VARCHAR(36)"))
        if "expense_type_id" not in expense_columns:
            connection.execute(text("ALTER TABLE expenses ADD COLUMN expense_type_id VARCHAR(36)"))
