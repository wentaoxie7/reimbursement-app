import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.config import ExpenseFieldDefinition, ExpenseType, FieldSchemaVersion
from app.schemas.admin import (
    ExpenseTypeCreate,
    ExpenseTypeUpdate,
    FieldDefinitionCreate,
    FieldDefinitionUpdate,
)


class FieldSchemaService:
    def __init__(self, db: Session, org_id: str):
        self.db = db
        self.org_id = org_id

    def list_expense_types(self, active_only: bool = False) -> list[ExpenseType]:
        stmt = (
            select(ExpenseType)
            .where(ExpenseType.org_id == self.org_id)
            .order_by(ExpenseType.display_order, ExpenseType.name)
        )
        if active_only:
            stmt = stmt.where(ExpenseType.active == True)  # noqa: E712
        return list(self.db.scalars(stmt).all())

    def get_default_expense_type(self) -> ExpenseType | None:
        active_types = self.list_expense_types(active_only=True)
        if active_types:
            return active_types[0]
        all_types = self.list_expense_types(active_only=False)
        return all_types[0] if all_types else None

    def get_expense_type(self, expense_type_id: str) -> ExpenseType | None:
        expense_type = self.db.get(ExpenseType, expense_type_id)
        if not expense_type or expense_type.org_id != self.org_id:
            return None
        return expense_type

    def create_expense_type(self, dto: ExpenseTypeCreate) -> ExpenseType:
        expense_type = ExpenseType(
            id=str(uuid.uuid4()),
            org_id=self.org_id,
            code=dto.code.strip().upper(),
            name=dto.name.strip(),
            display_order=dto.display_order,
            active=dto.active,
        )
        self.db.add(expense_type)
        self.db.commit()
        self.db.refresh(expense_type)
        return expense_type

    def update_expense_type(self, expense_type_id: str, dto: ExpenseTypeUpdate) -> ExpenseType:
        expense_type = self.get_expense_type(expense_type_id)
        if not expense_type:
            raise ValueError("Expense type not found")

        updates = dto.model_dump(exclude_unset=True)
        if "code" in updates and updates["code"] is not None:
            updates["code"] = updates["code"].strip().upper()
        if "name" in updates and updates["name"] is not None:
            updates["name"] = updates["name"].strip()
        for key, value in updates.items():
            setattr(expense_type, key, value)
        self.db.commit()
        self.db.refresh(expense_type)
        return expense_type

    def delete_expense_type(self, expense_type_id: str) -> None:
        expense_type = self.get_expense_type(expense_type_id)
        if not expense_type:
            raise ValueError("Expense type not found")
        field_count = self.db.scalars(
            select(ExpenseFieldDefinition.id).where(
                ExpenseFieldDefinition.org_id == self.org_id,
                ExpenseFieldDefinition.expense_type_id == expense_type_id,
                ExpenseFieldDefinition.is_global == False,  # noqa: E712
            )
        ).first()
        if field_count:
            raise ValueError("Delete the type-specific fields under this expense type first")

        from app.models.expense import Expense

        used_expense = self.db.scalars(
            select(Expense.id).where(Expense.expense_type_id == expense_type_id).limit(1)
        ).first()
        if used_expense:
            raise ValueError("This expense type is already used by expense records")

        self.db.delete(expense_type)
        self.db.commit()

    def list_fields(
        self,
        expense_type_id: str | None = None,
        is_global: bool | None = None,
    ) -> list[ExpenseFieldDefinition]:
        stmt = select(ExpenseFieldDefinition).where(ExpenseFieldDefinition.org_id == self.org_id)
        if is_global is True:
            stmt = stmt.where(ExpenseFieldDefinition.is_global == True)  # noqa: E712
        elif is_global is False:
            stmt = stmt.where(ExpenseFieldDefinition.is_global == False)  # noqa: E712
            if expense_type_id:
                stmt = stmt.where(ExpenseFieldDefinition.expense_type_id == expense_type_id)
        elif expense_type_id:
            stmt = stmt.where(
                (ExpenseFieldDefinition.is_global == True)  # noqa: E712
                | (ExpenseFieldDefinition.expense_type_id == expense_type_id)
            )
        stmt = stmt.order_by(ExpenseFieldDefinition.display_order, ExpenseFieldDefinition.label)
        return list(self.db.scalars(stmt).all())

    def _ensure_unique_field_key(
        self,
        field_key: str,
        is_global: bool,
        expense_type_id: str | None,
        exclude_field_id: str | None = None,
    ) -> None:
        candidates = self.db.scalars(
            select(ExpenseFieldDefinition).where(
                ExpenseFieldDefinition.org_id == self.org_id,
                ExpenseFieldDefinition.field_key == field_key,
            )
        ).all()
        for candidate in candidates:
            if exclude_field_id and candidate.id == exclude_field_id:
                continue
            if is_global:
                raise ValueError("Field key already exists")
            if candidate.is_global or candidate.expense_type_id == expense_type_id:
                raise ValueError("Field key already exists")

    def create_field(self, dto: FieldDefinitionCreate) -> ExpenseFieldDefinition:
        expense_type_id = None
        if dto.is_global:
            expense_type_id = None
        else:
            if not dto.expense_type_id:
                raise ValueError("Expense type not found")
            expense_type = self.get_expense_type(dto.expense_type_id)
            if not expense_type:
                raise ValueError("Expense type not found")
            expense_type_id = expense_type.id

        self._ensure_unique_field_key(dto.field_key, dto.is_global, expense_type_id)

        field = ExpenseFieldDefinition(
            id=str(uuid.uuid4()),
            org_id=self.org_id,
            expense_type_id=expense_type_id,
            is_global=dto.is_global,
            show_in_lists=dto.show_in_lists if dto.is_global else False,
            field_key=dto.field_key,
            label=dto.label,
            field_type=dto.field_type,
            required=dto.required,
            display_order=dto.display_order,
            options=dto.options,
            validation=dto.validation,
        )
        self.db.add(field)
        self.db.commit()
        self.db.refresh(field)
        return field

    def update_field(self, field_id: str, dto: FieldDefinitionUpdate) -> ExpenseFieldDefinition:
        field = self.db.get(ExpenseFieldDefinition, field_id)
        if not field or field.org_id != self.org_id:
            raise ValueError("Field not found")

        updates = dto.model_dump(exclude_unset=True)
        next_is_global = updates.get("is_global", field.is_global)
        next_expense_type_id = None if next_is_global else field.expense_type_id
        self._ensure_unique_field_key(field.field_key, next_is_global, next_expense_type_id, field.id)
        if "is_global" in updates and updates["is_global"] is not None:
            field.is_global = updates.pop("is_global")
            if field.is_global:
                field.expense_type_id = None
            elif not field.expense_type_id:
                raise ValueError("Type-specific fields require an expense type")
        for key, value in updates.items():
            if key == "show_in_lists" and not field.is_global:
                setattr(field, key, False)
                continue
            setattr(field, key, value)
        if not field.is_global:
            field.show_in_lists = False
        self.db.commit()
        self.db.refresh(field)
        return field

    def delete_field(self, field_id: str) -> None:
        field = self.db.get(ExpenseFieldDefinition, field_id)
        if not field or field.org_id != self.org_id:
            raise ValueError("Field not found")
        self.db.delete(field)
        self.db.commit()

    def reorder(
        self,
        ordered_ids: list[str],
        expense_type_id: str | None = None,
        is_global: bool | None = None,
    ) -> None:
        fields = []
        for field_id in ordered_ids:
            field = self.db.get(ExpenseFieldDefinition, field_id)
            if not field or field.org_id != self.org_id:
                continue
            if is_global is True and not field.is_global:
                continue
            if is_global is False:
                if field.is_global:
                    continue
                if expense_type_id and field.expense_type_id != expense_type_id:
                    continue
            fields.append(field)

        for order, field in enumerate(fields):
            field.display_order = order
        self.db.commit()

    def _serialize_field(self, field: ExpenseFieldDefinition) -> dict:
        return {
            "field_key": field.field_key,
            "label": field.label,
            "field_type": field.field_type.value,
            "required": field.required,
            "display_order": field.display_order,
            "options": field.options,
            "validation": field.validation,
            "is_global": field.is_global,
            "show_in_lists": field.show_in_lists,
        }

    def _legacy_list_field(self, field: dict) -> dict:
        show_in_lists = field.get("field_key") in {"amount", "category"}
        return {
            **field,
            "is_global": True,
            "show_in_lists": show_in_lists,
        }

    def _normalize_snapshot(self, snapshot: object) -> dict:
        active_types = self.list_expense_types(active_only=True)
        if isinstance(snapshot, dict) and isinstance(snapshot.get("expense_types"), list):
            normalized = {
                "global_fields": [
                    {
                        **field,
                        "is_global": field.get("is_global", True),
                        "show_in_lists": field.get("show_in_lists", False),
                    }
                    for field in snapshot.get("global_fields", [])
                ],
                "expense_types": [],
            }
            for item in snapshot.get("expense_types", []):
                normalized["expense_types"].append(
                    {
                        "id": item.get("id"),
                        "code": item.get("code"),
                        "name": item.get("name"),
                        "fields": [
                            {
                                **field,
                                "is_global": field.get("is_global", False),
                                "show_in_lists": False,
                            }
                            for field in item.get("fields", [])
                        ],
                    }
                )
            return normalized

        legacy_fields = snapshot if isinstance(snapshot, list) else []
        return {
            "global_fields": [self._legacy_list_field(field) for field in legacy_fields],
            "expense_types": [
                {
                    "id": expense_type.id,
                    "code": expense_type.code,
                    "name": expense_type.name,
                    "fields": [],
                }
                for expense_type in active_types
            ],
        }

    def get_published_schema(self, expense_type_id: str | None = None) -> dict | None:
        stmt = (
            select(FieldSchemaVersion)
            .where(FieldSchemaVersion.org_id == self.org_id)
            .order_by(FieldSchemaVersion.version.desc())
            .limit(1)
        )
        version = self.db.scalars(stmt).first()
        if not version:
            return None

        normalized = self._normalize_snapshot(version.snapshot)
        global_fields = normalized.get("global_fields", [])
        types = normalized.get("expense_types", [])
        selected = next((item for item in types if item.get("id") == expense_type_id), None)
        if expense_type_id is None and not selected and types:
            selected = types[0]

        expense_types = [
            {
                "id": item.get("id"),
                "code": item.get("code"),
                "name": item.get("name"),
            }
            for item in types
            if item.get("id")
        ]
        selected_fields = []
        if selected:
            selected_fields = sorted(
                [*global_fields, *selected.get("fields", [])],
                key=lambda field: (field.get("display_order", 0), field.get("label", "")),
            )
        list_fields = [
            field
            for field in sorted(global_fields, key=lambda item: (item.get("display_order", 0), item.get("label", "")))
            if field.get("show_in_lists")
        ]
        return {
            "version_id": version.id,
            "version": version.version,
            "expense_types": expense_types,
            "selected_expense_type_id": selected.get("id") if selected else None,
            "list_fields": list_fields,
            "fields": selected_fields,
        }

    def publish(self, published_by: str) -> FieldSchemaVersion:
        expense_types = self.list_expense_types(active_only=True)
        last = self.db.scalars(
            select(FieldSchemaVersion)
            .where(FieldSchemaVersion.org_id == self.org_id)
            .order_by(FieldSchemaVersion.version.desc())
            .limit(1)
        ).first()
        next_version = (last.version + 1) if last else 1

        snapshot = {
            "global_fields": [
                self._serialize_field(field)
                for field in self.list_fields(is_global=True)
                if field.enabled
            ],
            "expense_types": [
                {
                    "id": expense_type.id,
                    "code": expense_type.code,
                    "name": expense_type.name,
                    "fields": [
                        self._serialize_field(field)
                        for field in self.list_fields(expense_type.id, is_global=False)
                        if field.enabled
                    ],
                }
                for expense_type in expense_types
            ],
        }
        version = FieldSchemaVersion(
            id=str(uuid.uuid4()),
            org_id=self.org_id,
            version=next_version,
            snapshot=snapshot,
            published_by=published_by,
        )
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version
