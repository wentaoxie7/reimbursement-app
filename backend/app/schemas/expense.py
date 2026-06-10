from datetime import datetime

from pydantic import BaseModel

from app.models.expense import ExpenseStatus
from app.schemas.common import ORMBase


class ExpenseCreate(BaseModel):
    field_values: dict


class ExpenseUpdate(BaseModel):
    field_values: dict


class ExpenseResponse(ORMBase):
    id: str
    owner_id: str
    owner_name: str | None = None
    status: ExpenseStatus
    field_values: dict
    schema_version_id: str | None
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime
    current_approval_role_code: str | None = None
    current_approver_names: list[str] = []
    last_action_type: str | None = None
    last_action_comment: str | None = None
    last_action_actor_name: str | None = None


class FieldSchemaResponse(BaseModel):
    version_id: str | None
    version: int | None
    fields: list[dict]
