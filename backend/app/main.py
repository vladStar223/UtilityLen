"""FastAPI entry point for the UtilityLens backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import cases, chat, compare
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="UtilityLens API",
    description="""
## UtilityLens — интеллектуальный анализатор квитанций ЖКХ

Сервис предоставляет возможности для детального анализа и сравнения квитанций за коммунальные услуги:

### Основные возможности
- **Детерминированный факторный анализ** — разложение изменения суммы квитанции на факторы: изменение тарифов, объёмов потребления, перерасчёты и новые услуги.
- **Нормативная база Владивостока и ПП РФ № 354** — проверка тарифов и нормативов в соответствии с местным законодательством и Постановлением Правительства РФ № 354.
- **AI-юрист со стримингом SSE** — интерактивный диалог с AI-помощником, который консультирует по вопросам ЖКХ, помогает разобраться в аномалиях и подготовить обращения.
- **Локальный fallback** — работа без постоянного подключения к внешним AI-сервисам.

### Форматы данных
Все денежные суммы указываются в рублях и округляются до копеек. Объёмы — в единицах измерения услуги (м3, Гкал, кВт·ч). Проценты — в процентных пунктах.
""",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "cases",
            "description": "Демо-кейсы для Владивостока — готовые наборы квитанций для демонстрации возможностей сервиса.",
        },
        {
            "name": "compare",
            "description": "Факторный анализ — сравнение двух квитанций и разложение изменения суммы на факторы.",
        },
        {
            "name": "chat",
            "description": "AI-юрист — стриминговый диалог (SSE) с AI-помощником по контексту проведённого сравнения.",
        },
        {
            "name": "system",
            "description": "Системные эндпоинты для проверки работоспособности сервиса.",
        },
    ],
)

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


@app.get("/health", tags=["system"], summary="Проверка работоспособности", description="Возвращает статус сервиса. Используется для health-check и мониторинга.", responses={200: {"description": "Сервис работает нормально", "content": {"application/json": {"example": {"status": "ok"}}}}})
def health() -> dict:
    return {"status": "ok"}
