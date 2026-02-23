import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import insert, select

from src.api.db import profiles, session_scope, users
from src.api.schemas import LoginRequest, MeResponse, RegisterRequest, TokenResponse
from src.api.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=MeResponse,
    status_code=201,
    summary="Register a new user",
    description="Creates a new user account and a default profile row.",
    operation_id="auth_register",
)
def register(req: RegisterRequest):
    """Register a user and create a base profile."""
    user_id = str(uuid.uuid4())
    pw_hash = hash_password(req.password)

    with session_scope() as db:
        existing = db.execute(select(users.c.id).where(users.c.email == req.email)).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

        db.execute(
            insert(users).values(
                id=user_id,
                email=req.email,
                password_hash=pw_hash,
                display_name=req.display_name,
            )
        )
        db.execute(
            insert(profiles).values(
                user_id=user_id,
                display_name=req.display_name,
                bio="",
                pace="casual",
                bike_type="road",
                looking_for="friends",
                home_base="",
            )
        )

        return MeResponse(id=user_id, email=req.email, display_name=req.display_name)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Validates credentials and returns an access token for Authorization: Bearer usage.",
    operation_id="auth_login",
)
def login(req: LoginRequest):
    """Login with email/password and return a JWT access token."""
    with session_scope() as db:
        row = db.execute(select(users).where(users.c.email == req.email)).mappings().first()
        if not row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not verify_password(req.password, row["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        token = create_access_token(subject=row["id"])
        return TokenResponse(access_token=token, token_type="bearer")
