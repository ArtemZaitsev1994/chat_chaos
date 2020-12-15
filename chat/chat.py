import os
from uuid import UUID
from typing import List
from html import escape, unescape

from fastapi import (
    Depends, Body,
    WebSocket, APIRouter,
    WebSocketDisconnect,
    Request
)
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from core.utils import get_db
from settings import PHOTO_PATH
from .schemas import ChatRoomRead, MessageCreate, CommonResponse, AccessOpen, ChatRoomList
from .http_requests import get_user_info, get_list_users_info
from .utils import row2dict, ConnectionManager, save_files, check_auth
from .exceptions import UserNewChatLimit, UnsupportedMediaType
from . import services


router = APIRouter()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>LOAD</button>
        </form>

        <form action="" onsubmit="send(event)">
            <button>SEND</button>
        </form>


        <form action="" onsubmit="getPrev(event)">
            <button>Last One</button>
        </form>
        <ul id='messages'>


        <form action="" onsubmit="readMess(event)">
            <button>Read</button>
        </form>


        <form action="" onsubmit="banUser(event)">
            <button>Ban User</button>
        </form>
        

        <form action="" onsubmit="sendFile(event)">
        <input id="files" name="files" type="file" multiple>
        <button>files send FORM ENDPOINT</button>
        </form>

        <script>
            current_page = 1
            page_size = 10
            var message =  {
                'type': 'message',
                'message': '',
                'files': []
            }
            chat_id = '342e1a32-2321-472e-b835-6c7a633b1fa1'
            var ws = new WebSocket("ws://185.10.184.226:8001/ws/%s/%s");
            ws.onopen = function(event) {
                // ws.send(JSON.stringify(data))
                prev_mess =  {
                    'page': current_page,
                    'size': page_size,
                    'type': 'previous'
                }
                 ws.send(JSON.stringify(prev_mess))
            }
            ws.onmessage = function(event) {
                data = JSON.parse(event.data)
                console.log(data)
                data = data.payload
                if (data['type'] == 'message') {
                    mess = data.message
                    var messages = document.getElementById('messages')
                    var message = document.createElement('li')
                    var content = document.createTextNode(`${mess.sender.firstname} ${mess.created_at}: ${mess.text}`)
                    message.appendChild(content)
                    messages.appendChild(message)
                } else if (data['type'] == 'previous') {
                    for (mess of data.messages) {
                        var messages = document.getElementById('messages')
                        var message = document.createElement('li')
                        text = `${mess.sender.firstname} ${mess.created_at}: ${mess.text}`
                        message.textContent = text
                        messages.appendChild(message)
                    } 
                    current_page += 1   
                } else if (data['type'] == 'disconnect') {
                } else if (data['type'] == 'connect') {
                }
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                message =  {
                    'type': 'message',
                    'message': input.value,
                    'files': []
                }

                var files = document.getElementById('files').files
                  for (file of files) {
                    const reader = new FileReader();
                    reader.readAsDataURL(file);
                    reader.fileName = file.name;
                    reader.onload = (event) => {
                      const fileName = event.target.fileName.split('.');
                      const content = event.currentTarget.result;
                      send_data = {
                        'ext': fileName[fileName.length - 1],
                        'file': content
                      }
                      console.log(message)
                      message.files.push(send_data);
                    };
                }
                input.value = ''
                event.preventDefault()
            };
            function send(event) {
                event.preventDefault()
                console.log(message)
                ws.send(JSON.stringify(message))
            };
            function getPrev(event) {
                var input = document.getElementById("messageText")
                prev_mess =  {
                    'page': current_page,
                    'size': page_size,
                    'type': 'previous'
                }
                ws.send(JSON.stringify(prev_mess))
                event.preventDefault()
            };
            function readMess(event) {
                prev_mess =  {
                    'message_id': 2,
                    'type': 'read'
                }
                ws.send(JSON.stringify(prev_mess))
                event.preventDefault()
            };
            function banUser(event) {
                prev_mess =  {
                    'type': 'access_denied'
                }
                ws.send(JSON.stringify(prev_mess))
                event.preventDefault()
            };
            function sendFile(event) {
                event.preventDefault()
              var files = document.getElementById('files').files
              for (file of files) {
                const reader = new FileReader();
                reader.readAsBinaryString(file);
                reader.fileName = file.name;
                reader.onload = (event) => {
                console.log(event)
                  const fileName = event.target.fileName.split('.');
                  const content = event.currentTarget.result;
                  send_data = {
                    'ext': fileName[fileName.length - 1],
                    'file': content
                  }
                  console.log(send_data)
                  ws.send(JSON.stringify(send_data));
                };
              }
            }


        </script>
    </body>
</html>
"""

success_response = {
    'status': 200,
    'error': None
}
error_response = {
    'status': 500,
    'payload': None
}

@router.get("/chat/{self_id}/{another}")
async def get(self_id, another):
    return HTMLResponse(html % (self_id, another))


@router.get("/user_2")
async def get():
    return HTMLResponse(html % ('6ec37deb-d87d-4c42-a0cd-3a29ac1cbb2d', '64e42832-d857-4e38-b1ad-c785157c3c12'))


websocket_manager = ConnectionManager()

@router.websocket("/ws/{current_user}/{recipient}")
async def websocket_endpoint(
    current_user: str,
    recipient: str,
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    # Проверяем токен пришедший от соединения
    if not await websocket_manager.check_auth(websocket):
        return await websocket_manager.auth_failed_error(websocket)

    # TODO
    # init_data = await websocket.receive_json()
    init_data = {'self_id': current_user, 'recipient': recipient}
    if (values := list(init_data.values()))[0] == values[1]:
        return await websocket_manager.wrong_users_id_error(websocket)

    # пытаемся получить комнату чата, бросаем исключение,
    # если чат новый и превышен лимит новых чатов для пользователя
    try:
        chat_room = services.get_or_create_chat_room(db, init_data)
    except UserNewChatLimit:
        return await websocket_manager.chat_limit_error(websocket)

    # Если кто-то из пользователей ограничил доступ
    for _user in chat_room.users:
        if not _user.access:
            return await websocket_manager.access_denied_error(websocket)

    # Запрашиваем данные о пользователях с сервера аутентификации
    users = await get_list_users_info({'users_uuid': [str(x.user) for x  in chat_room.users]})
    if len(users) != 2:
        return await websocket_manager.wrong_users_id_error(websocket)

    await websocket.accept()
    current_user = init_data['self_id']
    await websocket_manager.add_connection(chat_room.id, websocket)

    # Отправляем сообщение в чат, что пользователь подключился
    response = {
        'payload': {
            'type': 'connect',
            'message': f'User connected {users[current_user]["firstname"]}'
        }
    }
    response.update(success_response)
    await websocket_manager.broadcast(chat_room.id, response)

    # Messages processing
    try:
        while True:
            data = await websocket.receive_json()
            if data['type'] == 'message':
                files = data.get('files') or None
                if files:
                    if len(files) > 10:
                        await websocket_manager.too_much_files_error(websocket)
                        continue

                    path = os.path.join(PHOTO_PATH, str(chat_room.id))
                    try:
                        files = save_files(data['files'], path)
                    except UnsupportedMediaType:
                        await websocket_manager.unsupported_media_type_error(websocket)
                        continue

                message = MessageCreate(
                    text=escape(data['message']),
                    sender=current_user,
                    received=False,
                    files=files
                )
                msg = services.save_message(db, message, chat_room)
                msg = row2dict(msg)
                msg['sender'] = {
                    'id': users[msg['sender']]['id'],
                    'firstname': users[msg['sender']]['firstname'],
                    'lastname': users[msg['sender']]['lastname'],
                }
                response = {
                    'payload': {
                        'type': data['type'],
                        'message': unescape(msg)
                    }
                }
                response.update(success_response)
                await websocket_manager.broadcast(chat_room.id, response)

            elif data['type'] == 'previous':
                # Recieve previous messages from chat
                limit = data['size']
                offset = limit * (data['page'] - 1)
                prev_messages = services.get_messages(db, chat_room, limit=limit, offset=offset)
                messages = []
                for msg in prev_messages:
                    dict_msg = row2dict(msg)
                    dict_msg['sender'] = {
                        'id': users[dict_msg['sender']]['id'],
                        'firstname': users[dict_msg['sender']]['firstname'],
                        'lastname': users[dict_msg['sender']]['lastname'],
                    }
                    dict_msg['text'] = unescape(dict_msg['text'])
                    messages.append(dict_msg)

                response = {
                    'payload': {
                        'type': data['type'],
                        'messages': messages
                    }
                }
                response.update(success_response)
                await websocket_manager.send_personal_message(websocket, response)

            elif data['type'] == 'read':
                result = services.read_messages(db, chat_room)

                response = {
                    'payload': {
                        'type': data['type'],
                        'read': bool(result)
                    }
                }
                response.update(success_response)
                await websocket_manager.broadcast(chat_room.id, response)

            elif data['type'] == 'access_denied':
                _current_user = next(
                    (_user for _user in chat_room.users if str(_user.user) == current_user),
                    None
                )
                services.set_access_denied(db, _current_user)

                response = {
                    'payload': {
                        'type': data['type'],
                        'success': not _current_user.access,
                        'user_closed_access': current_user
                    }
                }
                response.update(success_response)
                await websocket_manager.broadcast(chat_room.id, response)
                return websocket_manager.disconnect(chat_room.id, websocket)

    except WebSocketDisconnect:
        websocket_manager.disconnect(chat_room.id, websocket)
        response = {
            'payload': {
                'type': 'disconnect',
                'message': f'User left {users[current_user]["firstname"]}'
            }
        }
        response.update(success_response)
        await websocket_manager.broadcast(chat_room.id, response)


@router.post('/list_chat/', response_model=ChatRoomList)
async def get_list_chat(
    request: Request = Depends(check_auth),
    db: Session = Depends(get_db),
    limit: int = Body(...),
    offset: int = Body(...)
):
    """Get chat room list for user"""
    limit = min(limit, 100)
    self_user_id = request.state.user
    chat_rooms = services.get_chat_list(
        db,
        request.state.user,
        limit=limit,
        offset=offset
    )
    users = {str(_user.user) for room in chat_rooms for _user in room.users}
    if not users:
        users = {self_user_id}
    users = await get_list_users_info({'users_uuid': users})

    rooms = []
    for _chat in chat_rooms:
        last_mess = None
        if _chat.messages:
            last_mess = _chat.messages[0]
        chat = row2dict(_chat)
        chat['interlocutor'] = next(
            (
                users[_id]
                for _user
                in _chat.users
                if (_id := str(_user.user)) != self_user_id
            ),
            None
        )
        chat['last_mess'] = last_mess
        rooms.append(chat)

    response = {
        'payload': {
            'self_info': users[self_user_id],
            'rooms': rooms
        }
    }
    response.update(success_response)
    return response


@router.post('/set_access_open/', response_model=CommonResponse)
async def set_access_open(
    room_id: AccessOpen,
    request: Request = Depends(check_auth),
    db: Session = Depends(get_db),
):
    """Return access to chat for the interlocutor""" 
    room_id = room_id.dict()['room_id']
    result = services.set_access_open(db, request.state.user, room_id)
    response = {
        'payload': {
            'success': bool(result)
        }
    }
    response.update(success_response)
    return response


# @router.post("/uploadfiles/")
# async def create_upload_files(
#     request: Request,
#     files: List[UploadFile] = File(...),
#     chat_id: str = Body(...)    
# ):
#     try:
#         content_length = request.headers['content-length']
#     except KeyError:
#         return Response(status_code=status.HTTP_411_LENGTH_REQUIRED)
#     else:
#         if int(content_length) > 50 * 1024 * 1024:
#             return Response(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

#     for file in files:
#         # image_bytes = file.file.read()
#         # image_len = len(image_bytes)

#         mime_type, ext = file.content_type.split('/')
#         filename = f'{uuid.uuid4()}.{ext}'

#         if mime_type.lower() == 'image':
#             path = os.path.join(PHOTO_PATH, chat_id)
#             os.makedirs(path, exist_ok=True)

#             with open(os.path.join(path, filename), "wb") as buf:
#                 shutil.copyfileobj(file.file, buf)

#         elif mime_type.lower() == 'application':
#             path = os.path.join(FILES_PATH, chat_id)
#             os.makedirs(path, exist_ok=True)

#             with open(os.path.join(path, filename), "wb") as buf:
#                 shutil.copyfileobj(file.file, buf)

#     return {"filenames": [file.filename for file in files]}


# @router.get("/files")
# async def main():
#     content = """
# <body>
# <form action="/files/" enctype="multipart/form-data" method="post">
# <input name="files" type="file" multiple>
# <input type="submit">
# </form>
# <form action="/uploadfiles/" enctype="multipart/form-data" method="post">
# <input name="files" type="file" multiple>
# <input name="chat_id" value="342e1a32-2321-472e-b835-6c7a633b1fa1">
# <input type="submit">
# </form>
# </body>
#     """
#     return HTMLResponse(content=content)
