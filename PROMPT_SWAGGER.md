# Задание: Документация бэкенда и обогащение Swagger (OpenAPI)

Привет! Нам нужно оформить качественную документацию по бэкенду и обогатить Swagger UI (OpenAPI).

Мы находимся на ветке `feat/backend-core`.

Выполни следующие задачи шаг за шагом:

### 1. Обогащение Swagger / OpenAPI в FastAPI коде:
- В `backend/app/main.py`:
  - Добавь в `FastAPI(...)`:
    * `title="UtilityLens API"`;
    * Подробный `description` с описанием возможностей сервиса (детерминированный факторный анализ квитанций ЖКХ, нормативная база Владивостока и ПП РФ № 354, AI-юрист со стримингом SSE, локальный fallback);
    * `version="0.1.0"`;
    * `openapi_tags` (метаданные с описанием групп эндпоинтов: `cases`, `compare`, `chat`, `system`).
- В роутерах (`backend/app/api/cases.py`, `compare.py`, `chat.py`):
  - Добавь к каждому эндпоинту:
    * Понятные русскоязычные `summary` и `description`;
    * Описания кодов ответов (200, 400, 404);
    * Примеры тел запросов и ответов (`openapi_examples`).
- В моделях `backend/app/core/models.py`:
  - Добавь к ключевым полям `Field(description="...", examples=[...])`, чтобы в схемах Swagger UI было понятно назначение каждого поля и единицы измерения (рубли, проценты, м3, Гкал).

---

### 2. Создание файла `docs/API_DOCUMENTATION.md`:
Создай подробный документ со спецификацией API:
- Как запустить сервис и открыть Swagger UI (`http://localhost:8000/docs`) и ReDoc (`http://localhost:8000/redoc`).
- Таблица всех доступных методов API.
- Детальный разбор каждого эндпоинта:
  * `GET /health` — проверка работоспособности;
  * `GET /api/v1/cases` — получение списка демо-кейсов Владивостока;
  * `POST /api/v1/compare` — запуск факторного анализа по `case_id` или двум загруженным квитанциям;
  * `POST /api/v1/chat/stream` — SSE-стриминг диалога с AI-юристом по контексту сравнения.
- Спецификация формата Server-Sent Events (SSE) для фронтенда (события `token`, `tool_call`, `done`).
- Примеры вызовов через `curl` с реальными примерами входных JSON и ответов.

---

### 3. Проверка тестов:
Запусти автотесты и убедись, что добавление метаданных не сломало логику:
- Все тесты `backend/tests/` должны проходить успешно (13 passed).

---

### 4. Фиксация изменений в Git:
Добавь файлы и сделай коммит:
```bash
git add backend/ docs/API_DOCUMENTATION.md
git commit -m "docs(api): enrich Swagger OpenAPI schemas and add API_DOCUMENTATION.md"
```
