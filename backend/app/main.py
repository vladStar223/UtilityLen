"""FastAPI entry point for the UtilityLens backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import auth, bills, cases, chat, compare, user
from app.core.config import settings
from app.core.logging import logger
from app.core.rate_limit import limiter
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
            "name": "auth",
            "description": "Аутентификация пользователей, регистрация и получение профиля.",
        },
        {
            "name": "user",
            "description": "Профиль пользователя и агрегированная статистика аудита квитанций.",
        },
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
            "name": "bills",
            "description": "Загрузка квитанций ЖКХ (PDF, фото, JSON) и история загрузок.",
        },
        {
            "name": "comparisons",
            "description": "История факторных анализов и получение сохранённых отчётов.",
        },
        {
            "name": "system",
            "description": "Системные эндпоинты для проверки работоспособности сервиса.",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "25.vibe.fast.ru",
        "136.234.72.54",
        "testserver",
        "*",
    ],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Log security-relevant HTTP errors (401/403/429/5xx) without any PII."""
    if exc.status_code in (401, 403, 429) or exc.status_code >= 500:
        logger.warning(
            "HTTP %d on %s %s", exc.status_code, request.method, request.url.path
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log unexpected errors and mask them as a generic 500 response."""
    logger.exception(
        "Unhandled error on %s %s: %s",
        request.method,
        request.url.path,
        exc.__class__.__name__,
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX + "/auth", tags=["auth"])
app.include_router(user.router, prefix=API_PREFIX + "/user", tags=["user"])
app.include_router(cases.router, prefix=API_PREFIX, tags=["cases"])
app.include_router(compare.router, prefix=API_PREFIX, tags=["compare"])
app.include_router(chat.router, prefix=API_PREFIX, tags=["chat"])
app.include_router(bills.bills_router, prefix=API_PREFIX + "/bills", tags=["bills"])
app.include_router(bills.comparisons_router, prefix=API_PREFIX + "/comparisons", tags=["comparisons"])



@app.get("/health", tags=["system"], summary="Проверка работоспособности", description="Возвращает статус сервиса. Используется для health-check и мониторинга.", responses={200: {"description": "Сервис работает нормально", "content": {"application/json": {"example": {"status": "ok"}}}}})
def health() -> dict:
    return {"status": "ok"}
