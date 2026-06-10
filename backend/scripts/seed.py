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
from app.models.permission import (
    Permission,
    Role,
    RolePageAccess,
    RolePermission,
    UserRoleAssignment,
)
from app.models.user import User
from app.services.field_schema import FieldSchemaService
from app.services.page_access import PAGE_DEFINITIONS

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
    "DIRECTOR": ["APPROVAL_ACT"],
    "ADMIN": [item[0] for item in PERMISSIONS],
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
        "manager_email": "director@demo.com",
    },
    "finance@demo.com": {
        "password": "finance123",
        "full_name": "Finance User",
        "roles": ["FINANCE", "APPROVER"],
    },
    "director@demo.com": {
        "password": "director123",
        "full_name": "Director User",
        "roles": ["DIRECTOR"],
    },
}

DEFAULT_PAGE_ACCESS = {
    "EMPLOYEE": ["USER_HOME", "USER_MY_EXPENSES", "USER_NEW_EXPENSE", "USER_SETTINGS"],
    "APPROVER": [
        "USER_HOME",
        "USER_MY_EXPENSES",
        "USER_NEW_EXPENSE",
        "USER_APPROVAL_TASKS",
        "USER_ALL_EXPENSES",
        "USER_SETTINGS",
    ],
    "FINANCE": ["USER_HOME", "USER_MY_EXPENSES", "USER_APPROVAL_TASKS", "USER_ALL_EXPENSES", "USER_SETTINGS"],
    "DIRECTOR": ["USER_HOME", "USER_MY_EXPENSES", "USER_APPROVAL_TASKS", "USER_ALL_EXPENSES", "USER_SETTINGS"],
    "ADMIN": [page["key"] for page in PAGE_DEFINITIONS],
}

DEFAULT_FIELDS = [
    ("amount", "Amount", FieldType.CURRENCY, True, 0, None),
    ("expense_date", "Date", FieldType.DATE, True, 1, None),
    ("category", "Category", FieldType.SELECT, True, 2, {"choices": ["Travel", "Meals", "Office"]}),
    ("description", "Description", FieldType.TEXT, False, 3, None),
]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def ensure_assignment(table, key_data: dict, create_data: dict, db: Session) -> None:
    if not db.get(table, key_data):
        db.add(table(**create_data))


def migrate_manager_to_director(db: Session) -> None:
    manager_role = db.scalars(select(Role).where(Role.code == "MANAGER")).first()
    director_role = db.scalars(select(Role).where(Role.code == "DIRECTOR")).first()

    if manager_role and not director_role:
        manager_role.code = "DIRECTOR"
        manager_role.name = "Director"
        director_role = manager_role
    elif manager_role and director_role:
        assignments = db.scalars(select(UserRoleAssignment).where(UserRoleAssignment.role_id == manager_role.id)).all()
        for assignment in assignments:
            ensure_assignment(
                UserRoleAssignment,
                {"user_id": assignment.user_id, "role_id": director_role.id},
                {"user_id": assignment.user_id, "role_id": director_role.id},
                db,
            )
            db.delete(assignment)

        permissions = db.scalars(select(RolePermission).where(RolePermission.role_id == manager_role.id)).all()
        for permission in permissions:
            ensure_assignment(
                RolePermission,
                {"role_id": director_role.id, "permission_id": permission.permission_id},
                {"role_id": director_role.id, "permission_id": permission.permission_id},
                db,
            )
            db.delete(permission)

        page_accesses = db.scalars(select(RolePageAccess).where(RolePageAccess.role_id == manager_role.id)).all()
        for page_access in page_accesses:
            ensure_assignment(
                RolePageAccess,
                {"role_id": director_role.id, "page_key": page_access.page_key},
                {"role_id": director_role.id, "page_key": page_access.page_key},
                db,
            )
            db.delete(page_access)
        db.delete(manager_role)

    db.flush()

    for step in db.scalars(select(ApprovalStep).where(ApprovalStep.role_code == "MANAGER")).all():
        step.role_code = "DIRECTOR"

    manager_user = db.scalars(select(User).where(User.email == "manager@demo.com")).first()
    director_user = db.scalars(select(User).where(User.email == "director@demo.com")).first()
    if manager_user and not director_user:
        manager_user.email = "director@demo.com"
        manager_user.full_name = "Director User"
        manager_user.hashed_password = hash_password("director123")
        director_user = manager_user
    elif manager_user and director_user and manager_user.id != director_user.id:
        for employee in db.scalars(select(User).where(User.manager_id == manager_user.id)).all():
            employee.manager_id = director_user.id
        manager_user.email = f"legacy-manager-{manager_user.id[:6]}@demo.com"
        manager_user.full_name = "Legacy Manager User"
        manager_user.active = False


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
    ensure_assignment(
        RolePermission,
        {"role_id": role_id, "permission_id": permission_id},
        {"role_id": role_id, "permission_id": permission_id},
        db,
    )


def ensure_role_assignment(db: Session, user_id: str, role_id: str) -> None:
    ensure_assignment(
        UserRoleAssignment,
        {"user_id": user_id, "role_id": role_id},
        {"user_id": user_id, "role_id": role_id},
        db,
    )


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
    sequence_name = "Finance then Director"
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
    for order, role_code in [(1, "FINANCE"), (2, "DIRECTOR")]:
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


def ensure_page_access_defaults(db: Session, role_map: dict[str, Role]) -> None:
    for page in PAGE_DEFINITIONS:
        page_key = page["key"]
        if db.scalars(select(RolePageAccess).where(RolePageAccess.page_key == page_key)).first():
            continue
        for role_code, page_keys in DEFAULT_PAGE_ACCESS.items():
            if page_key in page_keys:
                db.add(RolePageAccess(role_id=role_map[role_code].id, page_key=page_key))


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        organization = db.get(Organization, ORG_ID)
        if not organization:
            db.add(Organization(id=ORG_ID, name="Demo Corp"))
        else:
            organization.name = "Demo Corp"

        migrate_manager_to_director(db)

        perm_map = {code: get_or_create_permission(db, code, description) for code, description in PERMISSIONS}
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
        ensure_page_access_defaults(db, role_map)
        db.commit()
        print("Seed complete.")
        print("  admin@demo.com / admin123")
        print("  employee@demo.com / employee123")
        print("  finance@demo.com / finance123")
        print("  director@demo.com / director123")
        print("  default approval: FINANCE -> DIRECTOR")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
