from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_page_access
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import (
    ExpenseTypeCreate,
    ExpenseTypeResponse,
    ExpenseTypeUpdate,
    FieldDefinitionCreate,
    FieldDefinitionResponse,
    FieldDefinitionUpdate,
    FieldReorderRequest,
)
from app.schemas.common import MessageResponse
from app.services.field_schema import FieldSchemaService

router = APIRouter(prefix="/admin", tags=["admin-fields"])


@router.get("/expense-types", response_model=list[ExpenseTypeResponse])
def list_expense_types(
    user: User = Depends(require_page_access("ADMIN_FIELDS")),
    db: Session = Depends(get_db),
) -> list[ExpenseTypeResponse]:
    items = FieldSchemaService(db, user.org_id).list_expense_types()
    return [ExpenseTypeResponse.model_validate(item) for item in items]


@router.post("/expense-types", response_model=ExpenseTypeResponse, status_code=status.HTTP_201_CREATED)
def create_expense_type(
    body: ExpenseTypeCreate,
    user: User = Depends(require_page_access("ADMIN_FIELDS")),
    db: Session = Depends(get_db),
) -> ExpenseTypeResponse:
    expense_type = FieldSchemaService(db, user.org_id).create_expense_type(body)
    return ExpenseTypeResponse.model_validate(expense_type)


@router.put("/expense-types/{expense_type_id}", response_model=ExpenseTypeResponse)
def update_expense_type(
    expense_type_id: str,
    body: ExpenseTypeUpdate,
    user: User = Depends(require_page_access("ADMIN_FIELDS")),
    db: Session = Depends(get_db),
) -> ExpenseTypeResponse:
    try:
        expense_type = FieldSchemaService(db, user.org_id).update_expense_type(expense_type_id, body)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return ExpenseTypeResponse.model_validate(expense_type)


@router.delete("/expense-types/{expense_type_id}", response_model=MessageResponse)
def delete_expense_type(
    expense_type_id: str,
    user: User = Depends(require_page_access("ADMIN_FIELDS")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    try:
        FieldSchemaService(db, user.org_id).delete_expense_type(expense_type_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return MessageResponse(message="Expense type deleted")


@router.get("/fields", response_model=list[FieldDefinitionResponse])
def list_fields(
    expense_type_id: str | None = Query(None),
    user: User = Depends(require_page_access("ADMIN_FIELDS")),
    db: Session = Depends(get_db),
) -> list[FieldDefinitionResponse]:
    fields = FieldSchemaService(db, user.org_id).list_fields(expense_type_id)
    return [FieldDefinitionResponse.model_validate(field) for field in fields]


@router.post("/fields", response_model=FieldDefinitionResponse, status_code=status.HTTP_201_CREATED)
def create_field(
    body: FieldDefinitionCreate,
    user: User = Depends(require_page_access("ADMIN_FIELDS")),
    db: Session = Depends(get_db),
) -> FieldDefinitionResponse:
    try:
        field = FieldSchemaService(db, user.org_id).create_field(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return FieldDefinitionResponse.model_validate(field)


@router.put("/fields/{field_id}", response_model=FieldDefinitionResponse)
def update_field(
    field_id: str,
    body: FieldDefinitionUpdate,
    user: User = Depends(require_page_access("ADMIN_FIELDS")),
    db: Session = Depends(get_db),
) -> FieldDefinitionResponse:
    try:
        field = FieldSchemaService(db, user.org_id).update_field(field_id, body)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return FieldDefinitionResponse.model_validate(field)


@router.delete("/fields/{field_id}", response_model=MessageResponse)
def delete_field(
    field_id: str,
    user: User = Depends(require_page_access("ADMIN_FIELDS")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    try:
        FieldSchemaService(db, user.org_id).delete_field(field_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return MessageResponse(message="Field deleted")


@router.patch("/fields/reorder", response_model=MessageResponse)
def reorder_fields(
    body: FieldReorderRequest,
    user: User = Depends(require_page_access("ADMIN_FIELDS")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    FieldSchemaService(db, user.org_id).reorder(body.ordered_ids, body.expense_type_id)
    return MessageResponse(message="Reordered")


@router.post("/fields/publish", response_model=MessageResponse)
def publish_schema(
    user: User = Depends(require_page_access("ADMIN_FIELDS")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    version = FieldSchemaService(db, user.org_id).publish(user.id)
    return MessageResponse(message=f"Published schema v{version.version}")
