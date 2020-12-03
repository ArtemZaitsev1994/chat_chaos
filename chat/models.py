import uuid
import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, desc
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSON


from core.db import Base


class ChatRoom(Base):
    __tablename__ = 'chat_room'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    users = relationship('ChatUsers', back_populates='chat_room')
    messages = relationship('Message', back_populates='chat_room', order_by=desc('created_at'))


class ChatUsers(Base):
    __tablename__ = 'chat_users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user = Column(UUID(as_uuid=True))
    chat_room_id = Column(UUID(as_uuid=True), ForeignKey('chat_room.id'), nullable=True)
    chat_room = relationship(ChatRoom, back_populates='users')
    access = Column(Boolean, default=True)


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    chat_room = relationship(ChatRoom, back_populates='messages')
    chat_room_id = Column(UUID(as_uuid=True), ForeignKey('chat_room.id'))
    sender = Column(UUID(as_uuid=True))
    received = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    files = Column(JSON, default=None)


class NewChatCount(Base):
    __tablename__ = 'new_chat_count'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user = Column(UUID, unique=True)
    count = Column(Integer, default=0)
