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
    'access-control-allow-credentials',
    'access-control-allow-headers,'
    'accept',
    'ccept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'Access-Control-Allow-Headers',
    'Access-Control-Allow-Credentials',
    'set-cookie',
    'access-control-allow-methods',
    'access-control-allow-origin',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["OPTIONS", "DELETE", "GET", "POST", "PUT"],
    allow_headers=headers,
)
