from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_page_access
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import (
    FieldDefinitionCreate,
    FieldDefinitionResponse,
    FieldDefinitionUpdate,
    FieldReorderRequest,
)
from app.schemas.common import MessageResponse
from app.services.field_schema import FieldSchemaService

router = APIRouter(prefix="/admin", tags=["admin-fields"])


@router.get("/fields", response_model=list[FieldDefinitionResponse])
def list_fields(
    user: User = Depends(require_page_access("ADMIN_FIELDS")),
    db: Session = Depends(get_db),
) -> list[FieldDefinitionResponse]:
    fields = FieldSchemaService(db, user.org_id).list_fields()
    return [FieldDefinitionResponse.model_validate(field) for field in fields]


@router.post("/fields", response_model=FieldDefinitionResponse, status_code=status.HTTP_201_CREATED)
def create_field(
    body: FieldDefinitionCreate,
    user: User = Depends(require_page_access("ADMIN_FIELDS")),
    db: Session = Depends(get_db),
) -> FieldDefinitionResponse:
    field = FieldSchemaService(db, user.org_id).create_field(body)
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
    FieldSchemaService(db, user.org_id).reorder(body.ordered_ids)
    return MessageResponse(message="Reordered")


@router.post("/fields/publish", response_model=MessageResponse)
def publish_schema(
    user: User = Depends(require_page_access("ADMIN_FIELDS")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    version = FieldSchemaService(db, user.org_id).publish(user.id)
    return MessageResponse(message=f"Published schema v{version.version}")
