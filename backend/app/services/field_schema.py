import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.config import ExpenseFieldDefinition, FieldSchemaVersion
from app.schemas.admin import FieldDefinitionCreate, FieldDefinitionUpdate


class FieldSchemaService:
    def __init__(self, db: Session, org_id: str):
        self.db = db
        self.org_id = org_id

    def list_fields(self) -> list[ExpenseFieldDefinition]:
        stmt = (
            select(ExpenseFieldDefinition)
            .where(ExpenseFieldDefinition.org_id == self.org_id)
            .order_by(ExpenseFieldDefinition.display_order)
        )
        return list(self.db.scalars(stmt).all())

    def create_field(self, dto: FieldDefinitionCreate) -> ExpenseFieldDefinition:
        field = ExpenseFieldDefinition(
            id=str(uuid.uuid4()),
            org_id=self.org_id,
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
        for key, value in dto.model_dump(exclude_unset=True).items():
            setattr(field, key, value)
        self.db.commit()
        self.db.refresh(field)
        return field

    def delete_field(self, field_id: str) -> None:
        field = self.db.get(ExpenseFieldDefinition, field_id)
        if not field or field.org_id != self.org_id:
            raise ValueError("Field not found")
        self.db.delete(field)
        self.db.commit()

    def reorder(self, ordered_ids: list[str]) -> None:
        for order, field_id in enumerate(ordered_ids):
            field = self.db.get(ExpenseFieldDefinition, field_id)
            if field and field.org_id == self.org_id:
                field.display_order = order
        self.db.commit()

    def get_published_schema(self) -> dict | None:
        stmt = (
            select(FieldSchemaVersion)
            .where(FieldSchemaVersion.org_id == self.org_id)
            .order_by(FieldSchemaVersion.version.desc())
            .limit(1)
        )
        version = self.db.scalars(stmt).first()
        if not version:
            return None
        return {
            "version_id": version.id,
            "version": version.version,
            "fields": version.snapshot,
        }

    def publish(self, published_by: str) -> FieldSchemaVersion:
        fields = self.list_fields()
        enabled = [f for f in fields if f.enabled]
        last = self.db.scalars(
            select(FieldSchemaVersion)
            .where(FieldSchemaVersion.org_id == self.org_id)
            .order_by(FieldSchemaVersion.version.desc())
            .limit(1)
        ).first()
        next_version = (last.version + 1) if last else 1
        snapshot = [
            {
                "field_key": f.field_key,
                "label": f.label,
                "field_type": f.field_type.value,
                "required": f.required,
                "display_order": f.display_order,
                "options": f.options,
                "validation": f.validation,
            }
            for f in enabled
        ]
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
