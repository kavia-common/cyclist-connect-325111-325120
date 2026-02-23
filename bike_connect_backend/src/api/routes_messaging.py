import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, insert, select

from src.api.db import (
    conversation_participants,
    conversations,
    messages,
    session_scope,
    users,
)
from src.api.deps import get_current_user
from src.api.schemas import (
    ConversationItem,
    ConversationsResponse,
    MessageItem,
    MessagesResponse,
    SendMessageRequest,
)

router = APIRouter(tags=["Messaging"])


def _ensure_participant(db, conversation_id: str, user_id: str) -> None:
    exists = (
        db.execute(
            select(conversation_participants.c.user_id).where(
                and_(
                    conversation_participants.c.conversation_id == conversation_id,
                    conversation_participants.c.user_id == user_id,
                )
            )
        ).first()
        is not None
    )
    if not exists:
        raise HTTPException(status_code=403, detail="Not a participant in this conversation")


@router.get(
    "/conversations",
    response_model=ConversationsResponse,
    summary="List conversations",
    description="Returns conversations for the current user with a title and last message preview.",
    operation_id="conversations_list",
)
def list_conversations(current_user: dict = Depends(get_current_user)):
    """List conversations for the current user."""
    with session_scope() as db:
        conv_ids = (
            db.execute(
                select(conversation_participants.c.conversation_id).where(
                    conversation_participants.c.user_id == current_user["id"]
                )
            )
            .scalars()
            .all()
        )

        items: List[ConversationItem] = []
        for cid in conv_ids:
            # Determine the "other user" (1:1 conversations assumed for now)
            other = (
                db.execute(
                    select(users.c.display_name, users.c.email)
                    .select_from(conversation_participants)
                    .join(users, users.c.id == conversation_participants.c.user_id)
                    .where(
                        and_(
                            conversation_participants.c.conversation_id == cid,
                            conversation_participants.c.user_id != current_user["id"],
                        )
                    )
                )
                .mappings()
                .first()
            )

            last_msg = (
                db.execute(
                    select(messages.c.text)
                    .where(messages.c.conversation_id == cid)
                    .order_by(messages.c.created_at.desc())
                    .limit(1)
                )
                .scalars()
                .first()
            )

            title = (other or {}).get("display_name") or (other or {}).get("email") or "Conversation"
            items.append(ConversationItem(id=str(cid), title=title, last_message=last_msg or ""))

        return ConversationsResponse(items=items)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=MessagesResponse,
    summary="Get messages",
    description="Returns messages for a conversation, with is_mine flags used by the frontend UI.",
    operation_id="conversations_messages_list",
)
def get_messages(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """List messages in a conversation."""
    with session_scope() as db:
        _ensure_participant(db, conversation_id, current_user["id"])
        rows = (
            db.execute(
                select(messages)
                .where(messages.c.conversation_id == conversation_id)
                .order_by(messages.c.created_at.asc())
            )
            .mappings()
            .all()
        )

    items = [
        MessageItem(
            id=r["id"],
            text=r["text"],
            created_at=r["created_at"],
            is_mine=r["sender_id"] == current_user["id"],
        )
        for r in rows
    ]
    return MessagesResponse(items=items)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageItem,
    summary="Send a message",
    description="Adds a message to the conversation. Requires participant membership.",
    operation_id="conversations_messages_send",
)
def send_message(conversation_id: str, req: SendMessageRequest, current_user: dict = Depends(get_current_user)):
    """Send a message to a conversation."""
    msg_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    with session_scope() as db:
        # Auto-create conversation if it doesn't exist and conversation_id looks like a placeholder
        conv = db.execute(select(conversations.c.id).where(conversations.c.id == conversation_id)).first()
        if not conv:
            # Create empty conversation; caller still must be participant, so add them.
            db.execute(insert(conversations).values(id=conversation_id, created_at=now))
            db.execute(
                insert(conversation_participants).values(conversation_id=conversation_id, user_id=current_user["id"])
            )

        _ensure_participant(db, conversation_id, current_user["id"])

        db.execute(
            insert(messages).values(
                id=msg_id,
                conversation_id=conversation_id,
                sender_id=current_user["id"],
                text=req.text,
                created_at=now,
            )
        )

    return MessageItem(id=msg_id, text=req.text, created_at=now, is_mine=True)
