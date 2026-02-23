from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token to be used as 'Authorization: Bearer <token>'.")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer').")


class RegisterRequest(BaseModel):
    email: str = Field(..., description="User email (unique).")
    password: str = Field(..., min_length=6, description="User password (min 6 chars).")
    display_name: Optional[str] = Field(default=None, description="Optional display name shown in the UI.")


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email.")
    password: str = Field(..., description="User password.")


class MeResponse(BaseModel):
    id: str = Field(..., description="User ID.")
    email: str = Field(..., description="Email.")
    display_name: Optional[str] = Field(default=None, description="Display name.")


class ProfileResponse(BaseModel):
    user_id: str = Field(..., description="User ID.")
    display_name: Optional[str] = Field(default=None, description="Display name.")
    bio: Optional[str] = Field(default=None, description="Bio.")
    pace: Optional[str] = Field(default=None, description="Pace preference.")
    bike_type: Optional[str] = Field(default=None, description="Bike type.")
    looking_for: Optional[str] = Field(default=None, description="What the user is looking for.")
    home_base: Optional[str] = Field(default=None, description="Approximate home base.")
    updated_at: Optional[datetime] = Field(default=None, description="Last update time (UTC).")


class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(default=None, description="Display name.")
    bio: Optional[str] = Field(default=None, description="Bio.")
    pace: Optional[str] = Field(default=None, description="Pace preference.")
    bike_type: Optional[str] = Field(default=None, description="Bike type.")
    looking_for: Optional[str] = Field(default=None, description="What the user is looking for.")
    home_base: Optional[str] = Field(default=None, description="Approximate home base.")


class LocationUpdateRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude.")
    lng: float = Field(..., ge=-180, le=180, description="Longitude.")


class NearbyUserItem(BaseModel):
    user_id: str = Field(..., description="Nearby user id.")
    display_name: Optional[str] = Field(default=None, description="Display name.")
    email: Optional[str] = Field(default=None, description="Email (may be omitted in production).")
    pace: Optional[str] = Field(default=None, description="Pace preference.")
    bike_type: Optional[str] = Field(default=None, description="Bike type.")
    distance_km: float = Field(..., description="Approximate distance in kilometers.")


class NearbyResponse(BaseModel):
    items: List[NearbyUserItem] = Field(default_factory=list, description="Nearby users.")


class ConversationItem(BaseModel):
    id: str = Field(..., description="Conversation id.")
    title: str = Field(..., description="Conversation title shown by frontend (usually other user's display name).")
    last_message: str = Field(default="", description="Last message preview.")


class ConversationsResponse(BaseModel):
    items: List[ConversationItem] = Field(default_factory=list, description="List of conversations.")


class MessageItem(BaseModel):
    id: str = Field(..., description="Message id.")
    text: str = Field(..., description="Message body.")
    created_at: datetime = Field(..., description="Timestamp (UTC).")
    is_mine: bool = Field(..., description="True if the message was sent by the current user.")


class MessagesResponse(BaseModel):
    items: List[MessageItem] = Field(default_factory=list, description="Messages.")


class SendMessageRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Message text.")


class RideCreateRequest(BaseModel):
    title: str = Field(..., description="Ride title.")
    date: Optional[str] = Field(default=None, description="Ride date 'YYYY-MM-DD'.")
    time: Optional[str] = Field(default=None, description="Ride time 'HH:MM'.")
    pace: Optional[str] = Field(default=None, description="Pace.")
    distance_km: Optional[float] = Field(default=None, description="Distance in km.")
    start: Optional[str] = Field(default=None, description="Start location.")
    notes: Optional[str] = Field(default=None, description="Extra notes.")


class RideResponse(BaseModel):
    id: str = Field(..., description="Ride id.")
    title: str = Field(..., description="Ride title.")
    date: Optional[str] = Field(default=None, description="Ride date.")
    time: Optional[str] = Field(default=None, description="Ride time.")
    pace: Optional[str] = Field(default=None, description="Pace.")
    distance_km: Optional[float] = Field(default=None, description="Distance in km.")
    start: Optional[str] = Field(default=None, description="Start location.")
    notes: Optional[str] = Field(default=None, description="Notes.")
    creator_id: Optional[str] = Field(default=None, description="Creator user id.")


class RidesResponse(BaseModel):
    items: List[RideResponse] = Field(default_factory=list, description="Ride list.")
