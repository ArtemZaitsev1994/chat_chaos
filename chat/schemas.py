from typing import List, Optional, Union, Dict
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class MessageCreate(BaseModel):
    text: str
    sender: UUID
    received: bool
    files: Optional[List]


class MessageRead(MessageCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class ChatRoomRead(BaseModel):
    id: UUID
    interlocutor: dict
    last_mess: Optional[MessageRead]

    class Config:
        orm_mode = True


class Error(BaseModel):
    code: str
    message: str


class CommonResponse(BaseModel):
    status: int
    payload: Union[dict, list, None]
    error: Optional[Error]


class AccessOpen(BaseModel):
    room_id: str


class ChatRoomList(CommonResponse):
    class Payload(BaseModel):
        self_info: dict
        rooms: List[ChatRoomRead]

    payload: Payload












