from typing import Dict, Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.db import session_scope, users
from src.api.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def _get_db() -> Session:
    """FastAPI dependency to yield a DB session."""
    with session_scope() as db:
        yield db


# PUBLIC_INTERFACE
def get_db() -> Session:
    """FastAPI dependency that provides a SQLAlchemy Session."""
    return Depends(_get_db)


# PUBLIC_INTERFACE
def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """FastAPI dependency that returns the current authenticated user row.

    Raises 401 if the bearer token is missing/invalid.
    """
    if not creds or not creds.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = creds.credentials
    try:
        payload: Dict = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    with session_scope() as db:
        row = db.execute(select(users).where(users.c.id == user_id)).mappings().first()
        if not row:
            raise HTTPException(status_code=401, detail="User not found")
        return dict(row)
