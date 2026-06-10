from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.approval import ApprovalAction, ApprovalInstanceStatus, ApprovalStep
from app.models.expense import Expense
from app.models.user import User
from app.schemas.expense import ExpenseResponse
from app.services.approval_engine import ApprovalEngine


def build_expense_response(db: Session, expense: Expense) -> ExpenseResponse:
    response = ExpenseResponse.model_validate(expense)
    instance = expense.approval_instance
    owner = db.get(User, expense.owner_id)
    last_action = db.scalars(
        select(ApprovalAction)
        .where(ApprovalAction.instance_id == instance.id)
        .order_by(ApprovalAction.acted_at.desc())
        .limit(1)
    ).first() if instance else None
    last_actor = db.get(User, last_action.actor_user_id) if last_action else None

    update: dict[str, object | None | list[str]] = {
        "owner_name": owner.full_name if owner else None,
        "last_action_type": last_action.action.value if last_action else None,
        "last_action_comment": last_action.comment if last_action else None,
        "last_action_actor_name": last_actor.full_name if last_actor else None,
    }

    if instance and instance.status == ApprovalInstanceStatus.STEP_ACTIVE:
        step = db.scalars(
            select(ApprovalStep).where(
                ApprovalStep.sequence_id == instance.sequence_id,
                ApprovalStep.step_order == instance.current_step_order,
            )
        ).first()
        if step:
            approver_ids = ApprovalEngine(db).resolve_approver_ids(step, expense)
            approvers = (
                db.scalars(select(User).where(User.id.in_(approver_ids))).all()
                if approver_ids
                else []
            )
            user_by_id = {user.id: user for user in approvers}
            update["current_approval_role_code"] = step.role_code
            update["current_approver_names"] = [
                user_by_id[user_id].full_name
                for user_id in approver_ids
                if user_id in user_by_id
            ]

    return response.model_copy(update=update)
