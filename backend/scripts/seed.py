"""Seed or repair dev data for local/Docker demos."""

import sys
import uuid
from pathlib import Path

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.approval import ApprovalSequence, ApprovalStep, ApproverRule
from app.models.config import ExpenseFieldDefinition, FieldSchemaVersion, FieldType
from app.models.organization import Organization
from app.models.permission import Permission, Role, RolePermission, UserRoleAssignment
from app.models.user import User
from app.services.field_schema import FieldSchemaService

ORG_ID = "org-demo"

PERMISSIONS = [
    ("EXPENSE_CREATE", "Create expenses"),
    ("EXPENSE_SUBMIT", "Submit expenses"),
    ("EXPENSE_VIEW_OWN", "View own expenses"),
    ("APPROVAL_ACT", "Approve or reject"),
    ("ARCHIVE_VIEW", "View archives"),
    ("CONFIG_FIELDS", "Configure expense fields"),
    ("CONFIG_USERS", "Configure users and roles"),
    ("CONFIG_APPROVAL", "Configure approval sequences"),
]

ROLES = {
    "EMPLOYEE": ["EXPENSE_CREATE", "EXPENSE_SUBMIT", "EXPENSE_VIEW_OWN"],
    "APPROVER": ["EXPENSE_CREATE", "EXPENSE_SUBMIT", "EXPENSE_VIEW_OWN", "APPROVAL_ACT"],
    "FINANCE": ["APPROVAL_ACT", "ARCHIVE_VIEW"],
    "MANAGER": ["APPROVAL_ACT"],
    "ADMIN": [p[0] for p in PERMISSIONS],
}

DEMO_USERS = {
    "admin@demo.com": {
        "password": "admin123",
        "full_name": "Admin User",
        "roles": ["ADMIN"],
    },
    "employee@demo.com": {
        "password": "employee123",
        "full_name": "Employee User",
        "roles": ["EMPLOYEE"],
        "manager_email": "manager@demo.com",
    },
    "finance@demo.com": {
        "password": "finance123",
        "full_name": "Finance User",
        "roles": ["FINANCE", "APPROVER"],
    },
    "manager@demo.com": {
        "password": "manager123",
        "full_name": "Manager User",
        "roles": ["MANAGER"],
    },
}

DEFAULT_FIELDS = [
    ("amount", "Amount", FieldType.CURRENCY, True, 0, None),
    ("expense_date", "Date", FieldType.DATE, True, 1, None),
    ("category", "Category", FieldType.SELECT, True, 2, {"choices": ["Travel", "Meals", "Office"]}),
    ("description", "Description", FieldType.TEXT, False, 3, None),
]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def get_or_create_permission(db: Session, code: str, description: str) -> Permission:
    permission = db.scalars(select(Permission).where(Permission.code == code)).first()
    if permission:
        permission.description = description
        return permission
    permission = Permission(id=str(uuid.uuid4()), code=code, description=description)
    db.add(permission)
    db.flush()
    return permission


def get_or_create_role(db: Session, code: str) -> Role:
    role = db.scalars(select(Role).where(Role.code == code)).first()
    if role:
        role.name = code.title()
        return role
    role = Role(id=str(uuid.uuid4()), code=code, name=code.title())
    db.add(role)
    db.flush()
    return role


def ensure_role_permission(db: Session, role_id: str, permission_id: str) -> None:
    exists = db.get(RolePermission, {"role_id": role_id, "permission_id": permission_id})
    if not exists:
        db.add(RolePermission(role_id=role_id, permission_id=permission_id))


def ensure_role_assignment(db: Session, user_id: str, role_id: str) -> None:
    exists = db.get(UserRoleAssignment, {"user_id": user_id, "role_id": role_id})
    if not exists:
        db.add(UserRoleAssignment(user_id=user_id, role_id=role_id))


def get_or_create_user(db: Session, email: str, password: str, full_name: str) -> User:
    user = db.scalars(select(User).where(User.email == email)).first()
    if user:
        user.org_id = ORG_ID
        user.full_name = full_name
        user.active = True
        return user
    user = User(
        id=str(uuid.uuid4()),
        org_id=ORG_ID,
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
    )
    db.add(user)
    db.flush()
    return user


def ensure_fields(db: Session) -> None:
    for key, label, field_type, required, order, options in DEFAULT_FIELDS:
        field = db.scalars(
            select(ExpenseFieldDefinition).where(
                ExpenseFieldDefinition.org_id == ORG_ID,
                ExpenseFieldDefinition.field_key == key,
            )
        ).first()
        if not field:
            field = ExpenseFieldDefinition(
                id=str(uuid.uuid4()),
                org_id=ORG_ID,
                field_key=key,
                label=label,
                field_type=field_type,
            )
            db.add(field)
        field.label = label
        field.field_type = field_type
        field.required = required
        field.display_order = order
        field.enabled = True
        field.options = options


def ensure_default_sequence(db: Session) -> None:
    sequence_name = "Finance then Manager"
    sequence = db.scalars(
        select(ApprovalSequence).where(
            ApprovalSequence.org_id == ORG_ID,
            ApprovalSequence.name == sequence_name,
            ApprovalSequence.active == True,  # noqa: E712
        )
    ).first()
    if not sequence:
        sequence = ApprovalSequence(
            id=str(uuid.uuid4()),
            org_id=ORG_ID,
            name=sequence_name,
            active=True,
        )
        db.add(sequence)
        db.flush()

    db.query(ApprovalStep).filter(ApprovalStep.sequence_id == sequence.id).delete()
    for order, role_code in [(1, "FINANCE"), (2, "MANAGER")]:
        db.add(
            ApprovalStep(
                id=str(uuid.uuid4()),
                sequence_id=sequence.id,
                step_order=order,
                approver_rule=ApproverRule.ROLE,
                role_code=role_code,
            )
        )

    for other in db.scalars(
        select(ApprovalSequence).where(
            ApprovalSequence.org_id == ORG_ID,
            ApprovalSequence.active == True,  # noqa: E712
        )
    ):
        other.is_default = other.id == sequence.id


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        organization = db.get(Organization, ORG_ID)
        if not organization:
            db.add(Organization(id=ORG_ID, name="Demo Corp"))
        else:
            organization.name = "Demo Corp"

        perm_map = {code: get_or_create_permission(db, code, desc) for code, desc in PERMISSIONS}
        role_map = {code: get_or_create_role(db, code) for code in ROLES}
        for role_code, permission_codes in ROLES.items():
            for permission_code in permission_codes:
                ensure_role_permission(db, role_map[role_code].id, perm_map[permission_code].id)
        db.flush()

        user_map = {
            email: get_or_create_user(db, email, config["password"], config["full_name"])
            for email, config in DEMO_USERS.items()
        }
        for email, config in DEMO_USERS.items():
            user = user_map[email]
            manager_email = config.get("manager_email")
            user.manager_id = user_map[manager_email].id if manager_email else None
            for role_code in config["roles"]:
                ensure_role_assignment(db, user.id, role_map[role_code].id)

        ensure_fields(db)
        db.flush()

        if not db.scalars(select(FieldSchemaVersion).where(FieldSchemaVersion.org_id == ORG_ID)).first():
            FieldSchemaService(db, ORG_ID).publish(user_map["admin@demo.com"].id)

        ensure_default_sequence(db)
        db.commit()
        print("Seed complete.")
        print("  admin@demo.com / admin123")
        print("  employee@demo.com / employee123")
        print("  finance@demo.com / finance123")
        print("  manager@demo.com / manager123")
        print("  default approval: FINANCE -> MANAGER")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
