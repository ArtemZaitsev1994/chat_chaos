from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from routes import routes

app = FastAPI()
app.include_router(routes)

origins = [
    "http://localhost",
    "http://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
