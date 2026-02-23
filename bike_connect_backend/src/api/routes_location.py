import math
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import insert, select, update

from src.api.db import locations, profiles, session_scope, users
from src.api.deps import get_current_user
from src.api.schemas import LocationUpdateRequest, NearbyResponse, NearbyUserItem

router = APIRouter(tags=["Location & Nearby"])


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Compute approximate distance between two points on earth (km)."""
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


@router.post(
    "/location",
    summary="Update current user's location",
    description="Stores the authenticated user's latest location for nearby search.",
    operation_id="location_update",
)
def update_location(req: LocationUpdateRequest, current_user: dict = Depends(get_current_user)):
    """Upsert the user's latest lat/lng."""
    now = datetime.now(timezone.utc)
    with session_scope() as db:
        existing = db.execute(select(locations.c.user_id).where(locations.c.user_id == current_user["id"])).first()
        if existing:
            db.execute(
                update(locations)
                .where(locations.c.user_id == current_user["id"])
                .values(lat=req.lat, lng=req.lng, updated_at=now)
            )
        else:
            db.execute(
                insert(locations).values(user_id=current_user["id"], lat=req.lat, lng=req.lng, updated_at=now)
            )
    return {"ok": True}


@router.get(
    "/nearby",
    response_model=NearbyResponse,
    summary="Search nearby cyclists",
    description="Returns cyclists within radius_km of the provided lat/lng. Requires auth.",
    operation_id="nearby_search",
)
def nearby_search(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius_km: float = Query(5.0, gt=0, le=200, description="Search radius in kilometers"),
    current_user: dict = Depends(get_current_user),
):
    """Return nearby users based on last known locations."""
    with session_scope() as db:
        rows = (
            db.execute(
                select(
                    users.c.id.label("user_id"),
                    users.c.email,
                    users.c.display_name,
                    profiles.c.pace,
                    profiles.c.bike_type,
                    locations.c.lat,
                    locations.c.lng,
                )
                .select_from(users)
                .join(locations, locations.c.user_id == users.c.id)
                .join(profiles, profiles.c.user_id == users.c.id, isouter=True)
                .where(users.c.id != current_user["id"])
            )
            .mappings()
            .all()
        )

    items: List[NearbyUserItem] = []
    for r in rows:
        dist = _haversine_km(lat, lng, float(r["lat"]), float(r["lng"]))
        if dist <= radius_km:
            items.append(
                NearbyUserItem(
                    user_id=r["user_id"],
                    email=r["email"],  # In a real app, likely omit this.
                    display_name=r["display_name"],
                    pace=r.get("pace"),
                    bike_type=r.get("bike_type"),
                    distance_km=dist,
                )
            )

    items.sort(key=lambda x: x.distance_km)
    return NearbyResponse(items=items)
