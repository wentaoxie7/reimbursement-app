import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.approval import ApprovalSequence, ApprovalStep
from app.models.user import User
from app.schemas.admin import ApprovalSequenceCreate, ApprovalSequenceResponse
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/admin", tags=["admin-approval"])


@router.get("/approval-sequences", response_model=list[ApprovalSequenceResponse])
def list_sequences(
    user: User = Depends(require_permission("CONFIG_APPROVAL")),
    db: Session = Depends(get_db),
) -> list[ApprovalSequenceResponse]:
    items = db.scalars(
        select(ApprovalSequence)
        .where(
            ApprovalSequence.org_id == user.org_id,
            ApprovalSequence.active == True,  # noqa: E712
        )
        .order_by(ApprovalSequence.is_default.desc(), ApprovalSequence.name)
    ).all()
    return [ApprovalSequenceResponse.model_validate(s) for s in items]


@router.post("/approval-sequences", response_model=ApprovalSequenceResponse, status_code=status.HTTP_201_CREATED)
def create_sequence(
    body: ApprovalSequenceCreate,
    user: User = Depends(require_permission("CONFIG_APPROVAL")),
    db: Session = Depends(get_db),
) -> ApprovalSequenceResponse:
    seq = ApprovalSequence(
        id=str(uuid.uuid4()),
        org_id=user.org_id,
        name=body.name,
        is_default=False,
    )
    db.add(seq)
    db.flush()
    for step in body.steps:
        db.add(
            ApprovalStep(
                id=str(uuid.uuid4()),
                sequence_id=seq.id,
                step_order=step.step_order,
                approver_rule=step.approver_rule,
                fixed_user_id=step.fixed_user_id,
                role_code=step.role_code,
            )
        )
    db.commit()
    db.refresh(seq)
    return ApprovalSequenceResponse.model_validate(seq)


@router.post("/approval-sequences/{sequence_id}/default", response_model=MessageResponse)
def set_default_sequence(
    sequence_id: str,
    user: User = Depends(require_permission("CONFIG_APPROVAL")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    seq = db.get(ApprovalSequence, sequence_id)
    if not seq or seq.org_id != user.org_id or not seq.active:
        raise HTTPException(status_code=404, detail="Sequence not found")
    for other in db.scalars(
        select(ApprovalSequence).where(
            ApprovalSequence.org_id == user.org_id,
            ApprovalSequence.active == True,  # noqa: E712
        )
    ):
        other.is_default = other.id == sequence_id
    db.commit()
    return MessageResponse(message="Default sequence updated")


@router.delete("/approval-sequences/{sequence_id}", response_model=MessageResponse)
def delete_sequence(
    sequence_id: str,
    user: User = Depends(require_permission("CONFIG_APPROVAL")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    seq = db.get(ApprovalSequence, sequence_id)
    if not seq or seq.org_id != user.org_id or not seq.active:
        raise HTTPException(status_code=404, detail="Sequence not found")

    replacements = list(
        db.scalars(
            select(ApprovalSequence)
            .where(
                ApprovalSequence.org_id == user.org_id,
                ApprovalSequence.active == True,  # noqa: E712
                ApprovalSequence.id != sequence_id,
            )
            .order_by(ApprovalSequence.name)
        ).all()
    )
    if seq.is_default and not replacements:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the only active approval sequence",
        )

    seq.active = False
    seq.is_default = False
    if replacements and not any(item.is_default for item in replacements):
        replacements[0].is_default = True

    db.commit()
    return MessageResponse(message="Approval sequence deleted")
