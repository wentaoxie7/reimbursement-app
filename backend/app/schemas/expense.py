from datetime import datetime

from pydantic import BaseModel

from app.models.expense import ExpenseStatus
from app.schemas.common import ORMBase


class ExpenseCreate(BaseModel):
    expense_type_id: str | None = None
    field_values: dict


class ExpenseUpdate(BaseModel):
    expense_type_id: str | None = None
    field_values: dict


class ExpenseTypeOptionResponse(BaseModel):
    id: str
    code: str
    name: str


class PublishedFieldResponse(BaseModel):
    field_key: str
    label: str
    field_type: str
    required: bool
    display_order: int
    options: dict | None = None
    validation: dict | None = None
    is_global: bool = False
    show_in_lists: bool = False


class ReceiptResponse(BaseModel):
    id: str
    file_url: str
    mime_type: str | None = None


class ExpenseResponse(ORMBase):
    id: str
    owner_id: str
    owner_name: str | None = None
    expense_type_id: str | None = None
    expense_type_name: str | None = None
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
    receipts: list[ReceiptResponse] = []


class FieldSchemaResponse(BaseModel):
    version_id: str | None
    version: int | None
    expense_types: list[ExpenseTypeOptionResponse] = []
    selected_expense_type_id: str | None = None
    list_fields: list[PublishedFieldResponse] = []
    fields: list[PublishedFieldResponse]
