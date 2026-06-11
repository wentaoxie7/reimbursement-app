import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.approval import ApprovalAction
from app.models.expense import Expense, ExpenseStatus
from app.models.expense import ArchiveRecord, Receipt
from app.models.user import User
from app.services.approval_engine import ApprovalEngine
from app.services.field_schema import FieldSchemaService


class ExpenseService:
    def __init__(self, db: Session, org_id: str):
        self.db = db
        self.org_id = org_id

    def _resolve_expense_type_id(self, expense_type_id: str | None) -> str:
        service = FieldSchemaService(self.db, self.org_id)
        if expense_type_id:
            expense_type = service.get_expense_type(expense_type_id)
            if not expense_type:
                raise ValueError("Expense type not found")
            return expense_type.id

        default_type = service.get_default_expense_type()
        if not default_type:
            raise ValueError("No expense type configured")
        return default_type.id

    def create(self, owner_id: str, expense_type_id: str | None, field_values: dict) -> Expense:
        expense = Expense(
            id=str(uuid.uuid4()),
            owner_id=owner_id,
            expense_type_id=self._resolve_expense_type_id(expense_type_id),
            field_values=field_values,
            status=ExpenseStatus.DRAFT,
        )
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def update(self, expense_id: str, owner_id: str, expense_type_id: str | None, field_values: dict) -> Expense:
        expense = self.db.get(Expense, expense_id)
        if not expense or expense.owner_id != owner_id:
            raise ValueError("Expense not found")
        if expense.status not in (ExpenseStatus.DRAFT, ExpenseStatus.REJECTED):
            raise ValueError("Expense not editable")
        expense.expense_type_id = self._resolve_expense_type_id(expense_type_id)
        expense.field_values = field_values
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def list_by_owner(self, owner_id: str, status: ExpenseStatus | None = None) -> list[Expense]:
        stmt = select(Expense).where(Expense.owner_id == owner_id)
        if status:
            stmt = stmt.where(Expense.status == status)
        return list(self.db.scalars(stmt.order_by(Expense.created_at.desc())).all())

    def list_all(self, status: ExpenseStatus | None = None) -> list[Expense]:
        stmt = (
            select(Expense)
            .join(Expense.owner)
            .where(User.org_id == self.org_id)
        )
        if status:
            stmt = stmt.where(Expense.status == status)
        return list(self.db.scalars(stmt.order_by(Expense.created_at.desc())).all())

    def submit(self, expense_id: str, owner_id: str) -> Expense:
        expense = self.db.get(Expense, expense_id)
        if not expense or expense.owner_id != owner_id:
            raise ValueError("Expense not found")
        expense.expense_type_id = self._resolve_expense_type_id(expense.expense_type_id)
        schema = FieldSchemaService(self.db, self.org_id).get_published_schema(expense.expense_type_id)
        if (
            not schema
            or not schema["version_id"]
            or schema["selected_expense_type_id"] != expense.expense_type_id
        ):
            raise ValueError("No published field schema")
        expense.schema_version_id = schema["version_id"]
        expense.status = ExpenseStatus.SUBMITTED
        expense.submitted_at = datetime.now(timezone.utc)
        self.db.commit()

        sequence = ApprovalEngine(self.db).get_default_sequence(self.org_id)
        if not sequence:
            raise ValueError("No default approval sequence configured")
        ApprovalEngine(self.db).start_instance(expense, sequence)
        self.db.refresh(expense)
        return expense

    def resubmit(self, expense_id: str, owner_id: str) -> Expense:
        expense = self.db.get(Expense, expense_id)
        if not expense or expense.owner_id != owner_id:
            raise ValueError("Expense not found")
        if expense.status != ExpenseStatus.REJECTED:
            raise ValueError("Only rejected expenses can be resubmitted")
        expense.expense_type_id = self._resolve_expense_type_id(expense.expense_type_id)
        schema = FieldSchemaService(self.db, self.org_id).get_published_schema(expense.expense_type_id)
        if (
            not schema
            or not schema["version_id"]
            or schema["selected_expense_type_id"] != expense.expense_type_id
        ):
            raise ValueError("No published field schema")
        expense.schema_version_id = schema["version_id"]
        expense.status = ExpenseStatus.IN_APPROVAL
        expense.submitted_at = datetime.now(timezone.utc)
        if expense.approval_instance:
            ApprovalEngine(self.db).reset_on_resubmit(expense.approval_instance)
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def withdraw(self, expense_id: str, owner_id: str) -> Expense:
        expense = self.db.get(Expense, expense_id)
        if not expense or expense.owner_id != owner_id:
            raise ValueError("Expense not found")
        if expense.status in (ExpenseStatus.DRAFT, ExpenseStatus.ARCHIVED):
            raise ValueError("Expense cannot be withdrawn")

        expense.status = ExpenseStatus.DRAFT
        expense.submitted_at = None
        if expense.approval_instance:
            ApprovalEngine(self.db).withdraw(expense.approval_instance)
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def delete(self, expense_id: str, owner_id: str) -> None:
        expense = self.db.get(Expense, expense_id)
        if not expense or expense.owner_id != owner_id:
            raise ValueError("Expense not found")

        if expense.approval_instance:
            self.db.query(ApprovalAction).filter(
                ApprovalAction.instance_id == expense.approval_instance.id
            ).delete()
            self.db.delete(expense.approval_instance)
        self.db.query(Receipt).filter(Receipt.expense_id == expense.id).delete()
        self.db.query(ArchiveRecord).filter(ArchiveRecord.expense_id == expense.id).delete()
        self.db.delete(expense)
        self.db.commit()
