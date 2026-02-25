"""
Announcement endpoints.

POST /api/announcements/draft          — create a new draft              (TL / Admin)
GET  /api/announcements/drafts         — list own announcements           (TL / Admin)
POST /api/announcements/{id}/publish   — publish or schedule a draft     (TL / Admin)
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends, status

from app.models import User, UserRole, Announcement, AnnouncementStatus
from app.auth import require_role
from app import auth as auth_service
from app import storage
from app.event_bus import notify_announcement
from app.schemas import (
    AnnouncementCreate,
    AnnouncementPublishRequest,
    AnnouncementResponse,
    AnnouncementListResponse,
)

router = APIRouter(prefix="/api/announcements", tags=["Announcements"])


# ── helpers ────────────────────────────────────────────────────────────────

def _to_response(ann: Announcement) -> AnnouncementResponse:
    return AnnouncementResponse(
        id=ann.id,
        title=ann.title,
        body=ann.body,
        audience=ann.audience,
        status=ann.status.value if hasattr(ann.status, "value") else str(ann.status),
        scheduled_at=ann.scheduled_at,
        published_at=ann.published_at,
        created_by=ann.created_by,
        created_at=ann.created_at,
        updated_at=ann.updated_at,
    )


# ── Create draft ────────────────────────────────────────────────────

@router.post("/draft", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_draft(
    body: AnnouncementCreate,
    current_user: User = Depends(require_role([UserRole.TEAM_LEAD, UserRole.ADMIN])),
):

    ann = Announcement(
        title=body.title,
        body=body.body,
        audience=body.audience,
        status=AnnouncementStatus.DRAFT,
        scheduled_at=body.scheduled_at,
        created_by=current_user.id,
    )
    saved = storage.create_announcement(ann)
    return _to_response(saved)


# ── List drafts / announcements ────────────────────────────────────

@router.get("/drafts", response_model=AnnouncementListResponse)
async def list_announcements(
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status: draft | scheduled | sent",
    ),
    current_user: User = Depends(require_role([UserRole.TEAM_LEAD, UserRole.ADMIN])),
):
 
    announcements = storage.get_announcements(
        created_by=current_user.id,
        status_filter=status_filter,
    )
    return AnnouncementListResponse(
        announcements=[_to_response(a) for a in announcements],
        total=len(announcements),
    )


# ── Publish / schedule ─────────────────────────────────────────────

@router.post("/{announcement_id}/publish", response_model=AnnouncementResponse)
async def publish_announcement(
    announcement_id: str,
    body: AnnouncementPublishRequest = AnnouncementPublishRequest(),
    current_user: User = Depends(require_role([UserRole.TEAM_LEAD, UserRole.ADMIN])),
):

    # Load & ownership check
    ann = storage.get_announcement_by_id(announcement_id)
    if not ann:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found",
        )
    if current_user.role != UserRole.ADMIN and ann.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only publish your own announcements",
        )
    if ann.status == AnnouncementStatus.SENT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Announcement has already been sent",
        )

    updated = storage.publish_announcement(
        announcement_id=announcement_id,
        scheduled_at=body.scheduled_at,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish announcement",
        )

    result = _to_response(updated)

    # Broadcast via SSE only when sending immediately
    if updated.status == AnnouncementStatus.SENT:
        notify_announcement({
            "id": updated.id,
            "title": updated.title,
            "body": updated.body,
            "audience": updated.audience,
            "published_at": updated.published_at.isoformat() if updated.published_at else None,
            "created_by": updated.created_by,
        })

    return result
