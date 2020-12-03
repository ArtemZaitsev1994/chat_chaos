from fastapi import APIRouter
from chat import chat


routes = APIRouter()

routes.include_router(chat.router)
