import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.db import ensure_schema, ping_db
from src.api.routes_auth import router as auth_router
from src.api.routes_location import router as location_router
from src.api.routes_messaging import router as messaging_router
from src.api.routes_profiles import router as profiles_router
from src.api.routes_rides import router as rides_router

openapi_tags = [
    {"name": "Auth", "description": "Authentication endpoints (register/login)."},
    {"name": "Profiles", "description": "User identity and profile management."},
    {"name": "Location & Nearby", "description": "Location updates and nearby cyclist search."},
    {"name": "Messaging", "description": "Conversation and messaging APIs."},
    {"name": "Rides", "description": "Group ride (event) creation and listing."},
    {"name": "System", "description": "Health and diagnostics."},
]

app = FastAPI(
    title="Bike Connect Backend API",
    description="APIs for cyclist discovery, messaging, and group rides. Designed to match the React frontend API client.",
    version="1.0.0",
    openapi_tags=openapi_tags,
)

cors_origins_raw = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
allow_origins = ["*"] if not cors_origins_raw else [o.strip() for o in cors_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure DB schema exists on startup (simple bootstrap for this project template).
try:
    ensure_schema()
except Exception:
    # If env isn't configured yet (e.g., DATABASE_URL missing), app should still boot for docs/health.
    pass

app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(location_router)
app.include_router(messaging_router)
app.include_router(rides_router)


@app.get(
    "/",
    tags=["System"],
    summary="Health check",
    description="Basic service health check.",
    operation_id="health_check",
)
def health_check():
    """Simple health check endpoint."""
    return {"message": "Healthy"}


@app.get(
    "/health/db",
    tags=["System"],
    summary="Database connectivity check",
    description="Verifies the API can connect to PostgreSQL (SELECT 1).",
    operation_id="health_db",
)
def db_health_check():
    """Check database connectivity."""
    ping_db()
    return {"ok": True}
