import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.approval import (
    ActionType,
    ApprovalAction,
    ApprovalInstance,
    ApprovalInstanceStatus,
    ApprovalSequence,
    ApprovalStep,
    ApproverRule,
)
from app.models.expense import Expense, ExpenseStatus
from app.models.permission import Role, UserRoleAssignment
from app.models.user import User


class ApprovalEngine:
    def __init__(self, db: Session):
        self.db = db

    def get_default_sequence(self, org_id: str) -> ApprovalSequence | None:
        stmt = select(ApprovalSequence).where(
            ApprovalSequence.org_id == org_id,
            ApprovalSequence.is_default == True,  # noqa: E712
            ApprovalSequence.active == True,  # noqa: E712
        )
        return self.db.scalars(stmt).first()

    def start_instance(self, expense: Expense, sequence: ApprovalSequence) -> ApprovalInstance:
        instance = expense.approval_instance
        if instance:
            instance.sequence_id = sequence.id
            instance.current_step_order = 1
            instance.status = ApprovalInstanceStatus.STEP_ACTIVE
        else:
            instance = ApprovalInstance(
                id=str(uuid.uuid4()),
                expense_id=expense.id,
                sequence_id=sequence.id,
                current_step_order=1,
                status=ApprovalInstanceStatus.STEP_ACTIVE,
            )
            self.db.add(instance)
        expense.status = ExpenseStatus.IN_APPROVAL
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def withdraw(self, instance: ApprovalInstance) -> None:
        instance.current_step_order = 1
        instance.status = ApprovalInstanceStatus.PENDING
        self.db.commit()

    def resolve_approver_ids(self, step: ApprovalStep, expense: Expense) -> list[str]:
        owner = self.db.get(User, expense.owner_id)
        if not owner:
            return []
        if step.approver_rule == ApproverRule.FIXED_USER and step.fixed_user_id:
            return [step.fixed_user_id]
        if step.approver_rule == ApproverRule.SUBMITTER_MANAGER and owner.manager_id:
            return [owner.manager_id]
        if step.approver_rule == ApproverRule.ROLE and step.role_code:
            role = self.db.scalars(select(Role).where(Role.code == step.role_code)).first()
            if not role:
                return []
            stmt = select(UserRoleAssignment.user_id).where(UserRoleAssignment.role_id == role.id)
            return list(self.db.scalars(stmt).all())
        return []

    def approve(self, instance: ApprovalInstance, actor_id: str, comment: str | None = None) -> ApprovalInstance:
        action = ApprovalAction(
            id=str(uuid.uuid4()),
            instance_id=instance.id,
            step_order=instance.current_step_order,
            actor_user_id=actor_id,
            action=ActionType.APPROVE,
            comment=comment,
        )
        self.db.add(action)

        steps = list(
            self.db.scalars(
                select(ApprovalStep)
                .where(ApprovalStep.sequence_id == instance.sequence_id)
                .order_by(ApprovalStep.step_order)
            ).all()
        )
        max_step = max((s.step_order for s in steps), default=1)

        if instance.current_step_order >= max_step:
            instance.status = ApprovalInstanceStatus.COMPLETED
            expense = self.db.get(Expense, instance.expense_id)
            if expense:
                expense.status = ExpenseStatus.APPROVED
        else:
            instance.current_step_order += 1

        self.db.commit()
        self.db.refresh(instance)
        return instance

    def reject(self, instance: ApprovalInstance, actor_id: str, comment: str) -> ApprovalInstance:
        action = ApprovalAction(
            id=str(uuid.uuid4()),
            instance_id=instance.id,
            step_order=instance.current_step_order,
            actor_user_id=actor_id,
            action=ActionType.REJECT,
            comment=comment,
        )
        self.db.add(action)
        instance.status = ApprovalInstanceStatus.REJECTED
        expense = self.db.get(Expense, instance.expense_id)
        if expense:
            expense.status = ExpenseStatus.REJECTED
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def reset_on_resubmit(self, instance: ApprovalInstance) -> None:
        instance.current_step_order = 1
        instance.status = ApprovalInstanceStatus.STEP_ACTIVE
        self.db.commit()
