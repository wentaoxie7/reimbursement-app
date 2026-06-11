import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.approval import ApprovalAction
from app.models.expense import ArchiveRecord, Expense, ExpenseStatus, Receipt
from app.models.user import User
from app.services.approval_engine import ApprovalEngine
from app.services.field_schema import FieldSchemaService

UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_URL_PREFIX = "/api/uploads"


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

    def _get_owned_expense(self, expense_id: str, owner_id: str) -> Expense:
        expense = self.db.get(Expense, expense_id)
        if not expense or expense.owner_id != owner_id:
            raise ValueError("Expense not found")
        return expense

    def _get_editable_expense(self, expense_id: str, owner_id: str) -> Expense:
        expense = self._get_owned_expense(expense_id, owner_id)
        if expense.status not in (ExpenseStatus.DRAFT, ExpenseStatus.REJECTED):
            raise ValueError("Expense not editable")
        return expense

    def _receipt_path_from_url(self, file_url: str) -> Path | None:
        if not file_url.startswith(f"{UPLOAD_URL_PREFIX}/"):
            return None
        relative = file_url.removeprefix(f"{UPLOAD_URL_PREFIX}/")
        return UPLOAD_ROOT / relative

    def _delete_receipt_files(self, expense: Expense) -> None:
        for receipt in expense.receipts:
            file_path = self._receipt_path_from_url(receipt.file_url)
            if file_path and file_path.exists():
                file_path.unlink()
        expense_dir = UPLOAD_ROOT / expense.id
        if expense_dir.exists():
            shutil.rmtree(expense_dir, ignore_errors=True)

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
        expense = self._get_editable_expense(expense_id, owner_id)
        expense.expense_type_id = self._resolve_expense_type_id(expense_type_id)
        expense.field_values = field_values
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def add_receipts(self, expense_id: str, owner_id: str, files: list[UploadFile]) -> Expense:
        expense = self._get_editable_expense(expense_id, owner_id)
        expense_dir = UPLOAD_ROOT / expense.id
        expense_dir.mkdir(parents=True, exist_ok=True)

        for upload in files:
            content_type = upload.content_type or ""
            if not content_type.startswith("image/"):
                raise ValueError("Only image files are supported")
            extension = Path(upload.filename or "").suffix or ".bin"
            filename = f"{uuid.uuid4()}{extension}"
            file_path = expense_dir / filename
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(upload.file, buffer)

            receipt = Receipt(
                id=str(uuid.uuid4()),
                expense_id=expense.id,
                file_url=f"{UPLOAD_URL_PREFIX}/{expense.id}/{filename}",
                mime_type=content_type,
            )
            self.db.add(receipt)

        self.db.commit()
        self.db.refresh(expense)
        return expense

    def list_by_owner(self, owner_id: str, status: ExpenseStatus | None = None) -> list[Expense]:
        stmt = select(Expense).where(Expense.owner_id == owner_id)
        if status:
            stmt = stmt.where(Expense.status == status)
        return list(self.db.scalars(stmt.order_by(Expense.created_at.desc())).all())

    def list_all(self, status: ExpenseStatus | None = None) -> list[Expense]:
        stmt = select(Expense).join(Expense.owner).where(User.org_id == self.org_id)
        if status:
            stmt = stmt.where(Expense.status == status)
        return list(self.db.scalars(stmt.order_by(Expense.created_at.desc())).all())

    def submit(self, expense_id: str, owner_id: str) -> Expense:
        expense = self._get_owned_expense(expense_id, owner_id)
        expense.expense_type_id = self._resolve_expense_type_id(expense.expense_type_id)
        schema = FieldSchemaService(self.db, self.org_id).get_published_schema(expense.expense_type_id)
        if not schema or not schema["version_id"] or schema["selected_expense_type_id"] != expense.expense_type_id:
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
        expense = self._get_owned_expense(expense_id, owner_id)
        if expense.status != ExpenseStatus.REJECTED:
            raise ValueError("Only rejected expenses can be resubmitted")
        expense.expense_type_id = self._resolve_expense_type_id(expense.expense_type_id)
        schema = FieldSchemaService(self.db, self.org_id).get_published_schema(expense.expense_type_id)
        if not schema or not schema["version_id"] or schema["selected_expense_type_id"] != expense.expense_type_id:
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
        expense = self._get_owned_expense(expense_id, owner_id)
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
        expense = self._get_owned_expense(expense_id, owner_id)
        self._delete_receipt_files(expense)

        if expense.approval_instance:
            self.db.query(ApprovalAction).filter(ApprovalAction.instance_id == expense.approval_instance.id).delete()
            self.db.delete(expense.approval_instance)
        self.db.query(Receipt).filter(Receipt.expense_id == expense.id).delete()
        self.db.query(ArchiveRecord).filter(ArchiveRecord.expense_id == expense.id).delete()
        self.db.delete(expense)
        self.db.commit()
