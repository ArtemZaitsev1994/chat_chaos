from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from routes import routes

app = FastAPI()
app.include_router(routes)

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
