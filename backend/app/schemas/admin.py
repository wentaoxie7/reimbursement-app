from pydantic import BaseModel

from app.models.config import FieldType
from app.models.approval import ApproverRule
from app.schemas.common import ORMBase


class FieldDefinitionCreate(BaseModel):
    field_key: str
    label: str
    field_type: FieldType
    required: bool = False
    display_order: int = 0
    options: dict | None = None
    validation: dict | None = None


class FieldDefinitionUpdate(BaseModel):
    label: str | None = None
    required: bool | None = None
    display_order: int | None = None
    enabled: bool | None = None
    options: dict | None = None
    validation: dict | None = None


class FieldDefinitionResponse(ORMBase):
    id: str
    field_key: str
    label: str
    field_type: FieldType
    required: bool
    display_order: int
    enabled: bool


class FieldReorderRequest(BaseModel):
    ordered_ids: list[str]


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
