from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert, select, update

from src.api.db import profiles, users
from src.api.deps import get_current_user
from src.api.schemas import MeResponse, ProfileResponse, ProfileUpdateRequest

router = APIRouter(tags=["Profiles"])


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current user",
    description="Returns the authenticated user's basic identity (used by the frontend AuthContext).",
    operation_id="me_get",
)
def me(current_user: dict = Depends(get_current_user)):
    """Return current user identity."""
    return MeResponse(id=current_user["id"], email=current_user["email"], display_name=current_user.get("display_name"))


@router.get(
    "/profiles/{user_id}",
    response_model=ProfileResponse,
    summary="Get a user profile",
    description="Returns profile info for the given user id.",
    operation_id="profiles_get",
)
def get_profile(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get a profile by user id.

    Note: requires auth to keep the app simple; can be relaxed later.
    """
    # current_user is intentionally unused besides auth guard.
    from src.api.db import session_scope  # local import to avoid circulars

    with session_scope() as db:
        row = db.execute(select(profiles).where(profiles.c.user_id == user_id)).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Profile not found")
        return ProfileResponse(**dict(row))


@router.put(
    "/profiles/me",
    response_model=ProfileResponse,
    summary="Update current user's profile",
    description="Updates the authenticated user's profile fields.",
    operation_id="profiles_update_me",
)
def update_me(req: ProfileUpdateRequest, current_user: dict = Depends(get_current_user)):
    """Update the current user's profile."""
    from src.api.db import session_scope  # local import to avoid circulars

    values = {k: v for k, v in req.model_dump().items() if v is not None}

    with session_scope() as db:
        existing = db.execute(select(profiles).where(profiles.c.user_id == current_user["id"])).mappings().first()
        if not existing:
            # create if missing
            db.execute(insert(profiles).values(user_id=current_user["id"], **values))
        else:
            db.execute(update(profiles).where(profiles.c.user_id == current_user["id"]).values(**values))

        # Keep users.display_name in sync when provided
        if "display_name" in values:
            db.execute(update(users).where(users.c.id == current_user["id"]).values(display_name=values["display_name"]))

        row = db.execute(select(profiles).where(profiles.c.user_id == current_user["id"])).mappings().first()
        return ProfileResponse(**dict(row))
