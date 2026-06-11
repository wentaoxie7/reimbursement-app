from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_page_access, require_permission
from app.db.session import get_db
from app.models.expense import Expense, ExpenseStatus
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.expense import ExpenseCreate, ExpenseResponse, ExpenseUpdate, FieldSchemaResponse
from app.services.expense import ExpenseService
from app.services.approval_engine import ApprovalEngine
from app.services.expense_response import build_expense_response
from app.services.field_schema import FieldSchemaService
from app.services.page_access import PageAccessService

router = APIRouter(prefix="/user", tags=["user-expenses"])


def _can_view_expense(user: User, expense: Expense, db: Session) -> bool:
    if expense.owner_id == user.id:
        return True
    owner = db.get(User, expense.owner_id)
    can_view_all = PageAccessService(db).has(user.id, "USER_ALL_EXPENSES")
    if can_view_all and owner and owner.org_id == user.org_id:
        return True
    if user.org_id == (owner.org_id if owner else None) and ApprovalEngine(db).is_current_approver(user.id, expense):
        return True
    return False


@router.get("/field-schema", response_model=FieldSchemaResponse)
def get_field_schema(
    expense_type_id: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FieldSchemaResponse:
    schema = FieldSchemaService(db, user.org_id).get_published_schema(expense_type_id)
    if not schema:
        return FieldSchemaResponse(
            version_id=None,
            version=None,
            expense_types=[],
            selected_expense_type_id=None,
            list_fields=[],
            fields=[],
        )
    return FieldSchemaResponse(**schema)


@router.get("/expenses", response_model=list[ExpenseResponse])
def list_expenses(
    status_filter: ExpenseStatus | None = Query(None, alias="status"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ExpenseResponse]:
    items = ExpenseService(db, user.org_id).list_by_owner(user.id, status_filter)
    return [build_expense_response(db, item) for item in items]


@router.get("/all-expenses", response_model=list[ExpenseResponse])
def list_all_expenses(
    status_filter: ExpenseStatus | None = Query(None, alias="status"),
    user: User = Depends(require_page_access("USER_ALL_EXPENSES")),
    db: Session = Depends(get_db),
) -> list[ExpenseResponse]:
    items = ExpenseService(db, user.org_id).list_all(status_filter)
    return [build_expense_response(db, item) for item in items]


@router.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    body: ExpenseCreate,
    user: User = Depends(require_permission("EXPENSE_CREATE")),
    db: Session = Depends(get_db),
) -> ExpenseResponse:
    expense = ExpenseService(db, user.org_id).create(user.id, body.expense_type_id, body.field_values)
    return build_expense_response(db, expense)


@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExpenseResponse:
    expense = db.get(Expense, expense_id)
    if not expense or not _can_view_expense(user, expense, db):
        raise HTTPException(status_code=404, detail="Expense not found")
    return build_expense_response(db, expense)


@router.post("/expenses/{expense_id}/receipts", response_model=ExpenseResponse)
def upload_receipts(
    expense_id: str,
    files: list[UploadFile] = File(...),
    user: User = Depends(require_permission("EXPENSE_CREATE")),
    db: Session = Depends(get_db),
) -> ExpenseResponse:
    try:
        expense = ExpenseService(db, user.org_id).add_receipts(expense_id, user.id, files)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return build_expense_response(db, expense)


@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: str,
    body: ExpenseUpdate,
    user: User = Depends(require_permission("EXPENSE_CREATE")),
    db: Session = Depends(get_db),
) -> ExpenseResponse:
    try:
        expense = ExpenseService(db, user.org_id).update(expense_id, user.id, body.expense_type_id, body.field_values)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return build_expense_response(db, expense)


@router.post("/expenses/{expense_id}/submit", response_model=ExpenseResponse)
def submit_expense(
    expense_id: str,
    user: User = Depends(require_permission("EXPENSE_SUBMIT")),
    db: Session = Depends(get_db),
) -> ExpenseResponse:
    try:
        expense = ExpenseService(db, user.org_id).submit(expense_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return build_expense_response(db, expense)


@router.post("/expenses/{expense_id}/resubmit", response_model=ExpenseResponse)
def resubmit_expense(
    expense_id: str,
    user: User = Depends(require_permission("EXPENSE_SUBMIT")),
    db: Session = Depends(get_db),
) -> ExpenseResponse:
    try:
        expense = ExpenseService(db, user.org_id).resubmit(expense_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return build_expense_response(db, expense)


@router.post("/expenses/{expense_id}/withdraw", response_model=ExpenseResponse)
def withdraw_expense(
    expense_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExpenseResponse:
    try:
        expense = ExpenseService(db, user.org_id).withdraw(expense_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return build_expense_response(db, expense)


@router.delete("/expenses/{expense_id}", response_model=MessageResponse)
def delete_expense(
    expense_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    try:
        ExpenseService(db, user.org_id).delete(expense_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return MessageResponse(message="Expense deleted")
