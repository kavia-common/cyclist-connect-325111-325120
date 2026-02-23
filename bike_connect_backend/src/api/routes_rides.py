import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert, select

from src.api.db import rides, session_scope
from src.api.deps import get_current_user
from src.api.schemas import RideCreateRequest, RideResponse, RidesResponse

router = APIRouter(prefix="/rides", tags=["Rides"])


@router.get(
    "",
    response_model=RidesResponse,
    summary="List rides",
    description="Returns recent rides (group ride events).",
    operation_id="rides_list",
)
def list_rides(current_user: dict = Depends(get_current_user)):
    """List rides (most recent first)."""
    with session_scope() as db:
        rows = db.execute(select(rides).order_by(rides.c.created_at.desc()).limit(200)).mappings().all()
        return RidesResponse(items=[RideResponse(**dict(r)) for r in rows])


@router.post(
    "",
    response_model=RideResponse,
    summary="Create a ride",
    description="Creates a new group ride event owned by the current user.",
    operation_id="rides_create",
)
def create_ride(req: RideCreateRequest, current_user: dict = Depends(get_current_user)):
    """Create a new ride."""
    ride_id = str(uuid.uuid4())
    with session_scope() as db:
        db.execute(
            insert(rides).values(
                id=ride_id,
                creator_id=current_user["id"],
                title=req.title,
                date=req.date,
                time=req.time,
                pace=req.pace,
                distance_km=req.distance_km,
                start=req.start,
                notes=req.notes,
            )
        )
        row = db.execute(select(rides).where(rides.c.id == ride_id)).mappings().first()
        return RideResponse(**dict(row))


@router.get(
    "/{ride_id}",
    response_model=RideResponse,
    summary="Get a ride",
    description="Get ride details by id.",
    operation_id="rides_get",
)
def get_ride(ride_id: str, current_user: dict = Depends(get_current_user)):
    """Get ride details."""
    with session_scope() as db:
        row = db.execute(select(rides).where(rides.c.id == ride_id)).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Ride not found")
        return RideResponse(**dict(row))
