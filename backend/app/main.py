"""FastAPI entry point for the UtilityLens backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import cases, chat, compare

app = FastAPI(title="UtilityLens Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://localhost:3000",
        "http://127.0.0.1:8501",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(cases.router, prefix=API_PREFIX, tags=["cases"])
app.include_router(compare.router, prefix=API_PREFIX, tags=["compare"])
app.include_router(chat.router, prefix=API_PREFIX, tags=["chat"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
