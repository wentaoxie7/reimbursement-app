from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_page_access
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import PageAccessResponse, PageAccessUpdate
from app.schemas.common import MessageResponse
from app.services.page_access import PageAccessService

router = APIRouter(prefix="/admin", tags=["admin-page-access"])


@router.get("/page-access", response_model=list[PageAccessResponse])
def list_page_access(
    user: User = Depends(require_page_access("ADMIN_PAGE_ACCESS")),
    db: Session = Depends(get_db),
) -> list[PageAccessResponse]:
    return [PageAccessResponse(**page) for page in PageAccessService(db).list_pages_with_roles()]


@router.put("/page-access/{page_key}", response_model=MessageResponse)
def update_page_access(
    page_key: str,
    body: PageAccessUpdate,
    user: User = Depends(require_page_access("ADMIN_PAGE_ACCESS")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    try:
        PageAccessService(db).replace_assignments(page_key, body.role_ids)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return MessageResponse(message="Page access updated")
