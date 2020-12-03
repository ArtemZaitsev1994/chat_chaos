import os
import json
import uuid
import base64
from typing import List
from datetime import datetime
from collections import defaultdict

import jwt
from fastapi import WebSocket, Request, HTTPException
from starlette import status

from settings import SECRET_KEY, AVAILABLE_IMG_EXTENSTION
from .models import Message
from .exceptions import UnsupportedMediaType
from .schemas import CommonResponse


def row2dict(row: Message) -> dict:
    should_be_string = (datetime, uuid.UUID)
    d = {}
    for column in row.__table__.columns:
        attr = getattr(row, column.name)
        d[column.name] = str(attr) if isinstance(attr, should_be_string) else attr
    return d


class ConnectionManager:
    def __init__(self):
        self.active_connections: defaultdict[List[WebSocket]] = defaultdict(list)

    async def add_connection(self, room_id: str, websocket: WebSocket):
        self.active_connections[room_id].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        self.active_connections[room_id].remove(websocket)

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        await websocket.send_text(json.dumps(CommonResponse(**message).dict()))

    async def broadcast(self, room_id: str, message: dict):
        for connection in self.active_connections[room_id]:
            await self.send_personal_message(connection, message)

    async def check_auth(self, websocket: WebSocket):
        return True

    async def auth_failed_error(self, websocket: WebSocket):
        await websocket.close(code=403)

    async def wrong_users_id_error(self, websocket: WebSocket):
        # response = {
        #     'status': 400,
        #     'payload': None,
        #     'error': {
        #         'code': 'NOT_FOUND',
        #         'message': 'Users are with uuid not found'
        #     }
        # }
        # await self.send_personal_message(websocket, response)
        # self.disconnect(room_id, websocket)
        await websocket.close(code=403)

    async def chat_limit_error(self, websocket: WebSocket):
        # response = {
        #     'status': 403,
        #     'payload': None,
        #     'error': {
        #         'code': 'LIMIT_EXCEEDED',
        #         'message': 'Limit of new chats per day exceeded'
        #     }
        # }
        # await self.send_personal_message(websocket, response)
        # websocket.close(code=403)
        await websocket.close(code=403)

    async def access_denied_error(self, websocket: WebSocket):
        await websocket.close(code=403)

    async def unsupported_media_type_error(self, websocket: WebSocket):
        response = {
            'status': 415,
            'payload': None,
            'error': {
                'code': 'UNSUPPORTED_MEDIA_TYPE',
                'message': 'Now supports only images with .jpg|.jpeg|.png extensions'
            }
        }
        await self.send_personal_message(websocket, response)

    async def too_much_files_error(self, websocket: WebSocket):
        response = {
            'status': 413,
            'payload': None,
            'error': {
                'code': 'REQUEST_ENTITY_TOO_LARGE',
                'message': 'Amount of files should be eq or less than 10'
            }
        }
        await self.send_personal_message(websocket, response)


def save_files(files, path):
    saved_files = []
    for file in files:
        file_info, base64_bytes = file['file'].split(',')
        mime_type, enc = file_info.split(':')[1].split(';')
        mime_type, ext = mime_type.split('/')
        if (
            enc != 'base64'
            or mime_type != 'image'
            or ext not in AVAILABLE_IMG_EXTENSTION
        ):
            raise UnsupportedMediaType()

        filename = f'{uuid.uuid4()}.{ext}'
        os.makedirs(path, exist_ok=True)
        full_path = os.path.join(path, filename)

        with open(full_path, 'wb') as file_to_save:
            decoded_data = base64.decodebytes(base64_bytes.encode('utf-8'))
            file_to_save.write(decoded_data)

        saved_files.append({
            'type': 'image',
            'url': full_path
        })
    return saved_files or None


async def check_auth(request: Request):
    token = request.headers.get('Authorization')
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Authorization header not provided'
        )

    _, token = token.split(' ')
    try:
        payload = jwt.decode(token, 'foo', algorithm=['HS256'])
    except (jwt.DecodeError, jwt.ExpiredSignatureError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Token invalid'
        )
    request.state.user = payload['id']
    return request





# import os

# from fastapi import FastAPI
# import uvicorn
# from fastapi import UploadFile, File
# from PIL import Image

# app = FastAPI()
# static_path = "/data/static/t-blog/"
# static_url = "http://img.tonyiscoding.top"

# def compress_img(file_name, com_level: int):
#     img = Image.open(file_name)
#     w, h = img.size
#     new_img = img.resize((int(w / com_level), int(h / com_level)), Image.ANTIALIAS)
#     new_img.save(file_name)

# @app.post("/upload")
# def upload_file(file: UploadFile = File(...), target: str = None):
#     target_path = static_path + target
#     if not os.path.exists(target_path):
#         os.mkdir(target_path)
#     file_name = target_path + "/" + file.filename
#     image_bytes = file.file.read()
#     image_len = len(image_bytes)
#     with open(file_name, "wb") as f:
#         f.write(image_bytes)
#     if image_len > (400 * 1000):
#         compress_img(file_name, 2)
#     return {"status": "ok"}

# @app.get("/list")
# def get_file_list():
#     file_dict = recursive_files(static_path, "/")
#     return file_dict


# def recursive_files(path: str, abs_path: str) -> dict:
#     file_tree = dict()
#     file_list = os.listdir(path)
#     for file in file_list:
#         next_file = path + "/" + file
#         if os.path.isdir(next_file):  #  if is a directory
#             file_tree[file] = recursive_files(next_file, abs_path + file + "/")
#         else:
#             file_tree[file] = static_url +  abs_path + file
#     return file_tree


# if __name__ == '__main__':
#     uvicorn.run(app=app, port=9001)