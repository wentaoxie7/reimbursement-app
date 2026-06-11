from pydantic import BaseModel

from app.models.config import FieldType
from app.models.approval import ApproverRule
from app.schemas.common import ORMBase


class FieldDefinitionCreate(BaseModel):
    expense_type_id: str | None = None
    is_global: bool = False
    show_in_lists: bool = False
    field_key: str
    label: str
    field_type: FieldType
    required: bool = False
    display_order: int = 0
    options: dict | None = None
    validation: dict | None = None


class FieldDefinitionUpdate(BaseModel):
    is_global: bool | None = None
    show_in_lists: bool | None = None
    field_key: str | None = None
    label: str | None = None
    field_type: FieldType | None = None
    required: bool | None = None
    display_order: int | None = None
    enabled: bool | None = None
    options: dict | None = None
    validation: dict | None = None


class FieldDefinitionResponse(ORMBase):
    id: str
    expense_type_id: str | None
    is_global: bool
    show_in_lists: bool
    field_key: str
    label: str
    field_type: FieldType
    required: bool
    display_order: int
    enabled: bool


class FieldReorderRequest(BaseModel):
    expense_type_id: str | None = None
    is_global: bool | None = None
    ordered_ids: list[str]


class ExpenseTypeCreate(BaseModel):
    code: str
    name: str
    display_order: int = 0
    active: bool = True


class ExpenseTypeUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    display_order: int | None = None
    active: bool | None = None


class ExpenseTypeResponse(ORMBase):
    id: str
    code: str
    name: str
    active: bool
    display_order: int


class UserResponse(ORMBase):
    id: str
    email: str
    full_name: str
    active: bool
    role_codes: list[str] = []


class RoleResponse(ORMBase):
    id: str
    code: str
    name: str


class PageAccessResponse(BaseModel):
    key: str
    label: str
    portal: str
    role_codes: list[str]
    role_ids: list[str]


class PageAccessUpdate(BaseModel):
    role_ids: list[str]


class UserRolesUpdate(BaseModel):
    role_ids: list[str]


class ApprovalStepCreate(BaseModel):
    step_order: int
    approver_rule: ApproverRule
    fixed_user_id: str | None = None
    role_code: str | None = None


class ApprovalSequenceCreate(BaseModel):
    name: str
    steps: list[ApprovalStepCreate] = []


class ApprovalStepResponse(ORMBase):
    id: str
    step_order: int
    approver_rule: ApproverRule
    fixed_user_id: str | None = None
    role_code: str | None = None


class ApprovalSequenceResponse(ORMBase):
    id: str
    name: str
    is_default: bool
    active: bool
    steps: list[ApprovalStepResponse] = []
