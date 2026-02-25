from fastapi import APIRouter, HTTPException, status, Depends
from app.models import User, UserRole, PolicyConfig
from app.auth import get_current_user, require_role
from app.schemas import PolicyConfigResponse, PolicyConfigUpdate, MessageResponse
from app import storage

router = APIRouter()

@router.get("/", response_model=PolicyConfigResponse)
async def get_policy_config(
    current_user: User = Depends(get_current_user)
):

    return storage.get_policy_config()

@router.put("/", response_model=PolicyConfigResponse)
async def update_policy_config(
    request: PolicyConfigUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):

    config = storage.update_policy_config(
        updated_by=current_user.id,
        cutoff_time=request.cutoff_time,
        forward_planning_days=request.forward_planning_days,
        wfh_monthly_allowance=request.wfh_monthly_allowance
    )
    
    # Audit log entry for policy change
    for field, value in request.model_dump(exclude_unset=True).items():
        storage.create_audit_entry(
            actor_id=current_user.id,
            action="update",
            entity_type="policy",
            entity_id=config.id,
            field_changed=field,
            new_value=str(value)
        )
        
    return config
