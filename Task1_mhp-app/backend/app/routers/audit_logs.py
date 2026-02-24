from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import date
from app.models import User, UserRole, AuditLogEntry
from app.auth import get_current_user, require_role
from app.schemas import AuditLogListResponse, AuditLogEntryResponse, AuditLogActorInfo
from app import storage
from app import utils

router = APIRouter()

@router.get("/", response_model=AuditLogListResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    actor_id: Optional[str] = Query(None),
    target_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):

    logs, total = storage.get_audit_logs(
        page=page,
        page_size=page_size,
        actor_id=actor_id,
        target_user_id=target_id,
        action=action,
        entity_type=entity_type,
        start_date=start_date,
        end_date=end_date
    )
    
    # Map raw AuditLogEntry to response schema with enriched actor/target info
    log_responses = []
    for log in logs:
        actor = storage.get_user_by_id(log.actor_id)
        actor_info = AuditLogActorInfo(id=actor.id, name=actor.name, role=actor.role.value) if actor else None
        
        target = storage.get_user_by_id(log.target_user_id) if log.target_user_id else None
        target_info = AuditLogActorInfo(id=target.id, name=target.name, role=target.role.value) if target else None
        
        log_responses.append(AuditLogEntryResponse(
            id=log.id,
            timestamp=log.timestamp,
            actor=actor_info,
            target_user=target_info,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            field_changed=log.field_changed,
            old_value=log.old_value,
            new_value=log.new_value
        ))
        
    return AuditLogListResponse(
        audit_logs=log_responses,
        total=total,
        page=page,
        page_size=page_size
    )
