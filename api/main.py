"""FastAPI-приложение для Mini App: uvicorn api.main:app."""

from fastapi import FastAPI

from core.config import get_settings
from core.logging import setup_logging

setup_logging(get_settings().log_level)

app = FastAPI(title="Agro Monitor API")


@app.get("/health")
async def health() -> dict[str, str]:
    """Проверка, что API запущено."""
    return {"status": "ok"}
