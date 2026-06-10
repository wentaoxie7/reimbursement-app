from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.approval import ApprovalInstance, ApprovalInstanceStatus, ApprovalStep
from app.models.expense import Expense, ExpenseStatus
from app.models.user import User
from app.schemas.expense import ExpenseResponse
from app.services.approval_engine import ApprovalEngine
from app.services.expense_response import build_expense_response

router = APIRouter(prefix="/user", tags=["user-approval"])


class RejectBody(BaseModel):
    comment: str


class ApprovalActionBody(BaseModel):
    comment: str


@router.get("/approval-tasks", response_model=list[ExpenseResponse])
def list_approval_tasks(
    user: User = Depends(require_permission("APPROVAL_ACT")),
    db: Session = Depends(get_db),
) -> list[ExpenseResponse]:
    engine = ApprovalEngine(db)
    expenses = db.scalars(
        select(Expense)
        .join(ApprovalInstance, ApprovalInstance.expense_id == Expense.id)
        .where(
            ApprovalInstance.status == ApprovalInstanceStatus.STEP_ACTIVE,
            Expense.status.in_([ExpenseStatus.IN_APPROVAL, ExpenseStatus.SUBMITTED]),
        )
    ).all()
    result: list[Expense] = []
    for expense in expenses:
        instance = expense.approval_instance
        if not instance or instance.status != ApprovalInstanceStatus.STEP_ACTIVE:
            continue
        step = db.scalars(
            select(ApprovalStep).where(
                ApprovalStep.sequence_id == instance.sequence_id,
                ApprovalStep.step_order == instance.current_step_order,
            )
        ).first()
        if step and user.id in engine.resolve_approver_ids(step, expense):
            result.append(expense)
    return [build_expense_response(db, e) for e in result]


@router.post("/approval-tasks/{expense_id}/approve", response_model=ExpenseResponse)
def approve_task(
    expense_id: str,
    body: ApprovalActionBody,
    user: User = Depends(require_permission("APPROVAL_ACT")),
    db: Session = Depends(get_db),
) -> ExpenseResponse:
    expense = db.get(Expense, expense_id)
    if not expense or not expense.approval_instance:
        raise HTTPException(status_code=404, detail="Not found")
    instance = expense.approval_instance
    comment = body.comment.strip()
    if not comment:
        raise HTTPException(status_code=400, detail="Comment is required")
    ApprovalEngine(db).approve(instance, user.id, comment)
    db.refresh(expense)
    return build_expense_response(db, expense)


@router.post("/approval-tasks/{expense_id}/reject", response_model=ExpenseResponse)
def reject_task(
    expense_id: str,
    body: RejectBody,
    user: User = Depends(require_permission("APPROVAL_ACT")),
    db: Session = Depends(get_db),
) -> ExpenseResponse:
    expense = db.get(Expense, expense_id)
    if not expense or not expense.approval_instance:
        raise HTTPException(status_code=404, detail="Not found")
    comment = body.comment.strip()
    if not comment:
        raise HTTPException(status_code=400, detail="Comment is required")
    ApprovalEngine(db).reject(expense.approval_instance, user.id, comment)
    db.refresh(expense)
    return build_expense_response(db, expense)
