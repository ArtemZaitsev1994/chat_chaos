from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from routes import routes

app = FastAPI()
app.include_router(routes)

origins = [
    "http://localhost:3001",
    "https://localhost:3001",
    "http://192.168.101.75:3001",
    "http://134.122.73.229:3050"
]

headers = [
    'Access-Control-Allow-Headers',
    'Access-Control-Allow-Credentials',
    'Access-Control-Allow-Origin',
    'Access-Control-Allow-Methods',
    'set-cookie'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["DELETE", "GET", "POST", "PUT"],
    allow_headers=headers,
)
