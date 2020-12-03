from typing import List
from uuid import UUID

from sqlalchemy.orm import Session, aliased, defaultload
from sqlalchemy import and_, desc

from settings import NEW_CHATS_PER_DAY_LIMIT
from .models import ChatRoom, ChatUsers, Message, NewChatCount
from .exceptions import UserNewChatLimit
from .schemas import MessageCreate


def get_messages(
    db: Session,
    chat_room: ChatRoom,
    limit: int = 10,
    offset: int = 0
) -> List[Message]:
    result = db.query(
        Message
    ).filter(
        Message.chat_room == chat_room
    ).order_by(
        desc(Message.created_at)
    ).offset(offset).limit(limit).all()
    return result


def get_chat_list(
    db: Session,
    user: str,
    limit: int = 10,
    offset: int = 0
) -> List[ChatRoom]:
    result = db.query(
        ChatRoom
    ).filter(
        ChatRoom.users.any(user=user)
    ).options(
        defaultload('users')
    ).offset(offset).limit(limit).all()
    return result


def read_messages(
    db: Session,
    chat_room: ChatRoom
):
    result = db.query(Message).filter(
        and_(
            Message.chat_room == chat_room,
            Message.received == False
        )
    ).update({Message.received: True})
    db.commit()
    return result


def check_user_new_chat_limit(
    db: Session,
    user: str
):
    query = db.query(NewChatCount).filter(NewChatCount.user == user).first()
    if query is None:
        count = NewChatCount(user=user)
        db.add(count)
        db.commit()
    return query or count


def get_or_create_chat_room(db: Session, users: str) -> ChatRoom:
    alias1 = aliased(ChatUsers)
    alias2 = aliased(ChatUsers)
    query = db.query(alias1)
    query = query.filter(
        and_(
            alias1.user.in_(users.values()),
            alias2.user.in_(users.values())
        )
    )
    query = query.join(
        alias2,
        and_(
            alias1.chat_room_id == alias2.chat_room_id,
            alias1.user != alias2.user
        )
    )
    query = query.first()
    if query is None:
        new_chats_count = check_user_new_chat_limit(db, users['self_id'])
        if new_chats_count.count > NEW_CHATS_PER_DAY_LIMIT:
            raise UserNewChatLimit()

        chat_users = []
        for user in users.values():
            chat_user = ChatUsers(user=user)
            db.add(chat_user)
            chat_users.append(chat_user)

        chat_room = ChatRoom()
        chat_room.users.extend(chat_users)
        db.add(chat_room)
        new_chats_count.count += 1
        db.add(new_chats_count)
        db.commit()
        db.refresh(chat_room)
    else:
        chat_room = query.chat_room

    return chat_room


def save_message(
    db: Session,
    message: MessageCreate,
    chat_room: ChatRoom
) -> Message:
    msg = message.dict()
    message = Message(**msg)
    chat_room.messages.append(message)
    db.add(message)
    db.add(chat_room)
    db.commit()
    db.refresh(message)
    return message


def set_access_denied(
    db: Session,
    user: ChatUsers
):  
    user.access = False
    db.add(user)
    return db.commit()


def set_access_open(
    db: Session,
    user_id: UUID,
    chat_room_id: UUID
):  
    result = db.query(
        ChatUsers
    ).filter(
        and_(
            ChatUsers.user == user_id,
            ChatUsers.chat_room_id == chat_room_id
        )
    ).update({ChatUsers.access: True})
    db.commit()
    return result
