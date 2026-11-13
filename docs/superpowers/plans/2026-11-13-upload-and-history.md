# План реализации: Загрузка документов, мультимодальный анализ и история пользователей

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Реализовать полный цикл загрузки документов (JSON, PDF, фото квитанций), их интеллектуальное распознавание через Pydantic/Vision конвейер, сохранение под профилем пользователя и автоматический факторный анализ с отображением истории в Streamlit.

**Architecture:** Модульный конвейер на FastAPI: `auth` (JWT + User модели в SQLAlchemy) -> `parser` (JSON / pypdf / Vision LLM) -> `comparison_service` (авто-поиск истории, факторный анализ дельты или аудит норм Владивостока) -> `api` (`/bills/upload`, `/bills/history`, `/comparisons/history`) -> UI в Streamlit (`sidebar`, `upload_view`).

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy 2.0, SQLite / PostgreSQL, pypdf, httpx, Streamlit.

**Spec:** [docs/superpowers/specs/2026-11-13-upload-and-history-design.md](file:///d:/hakaton/docs/superpowers/specs/2026-11-13-upload-and-history-design.md)

## Global Constraints
- Python 3.10+
- Совместимость с Pydantic v2 и схемами `contracts/bill_schema.json`
- Детерминированный fallback при отсутствии API-ключа Vision
- Демо-пользователь по умолчанию: `demo@utilitylens.ru` (пароль `demo123`, `user_id="user_demo_01"`)
- Чистая архитектура без ломающих изменений существующих эндпоинтов `/api/v1/cases` и `/api/v1/compare`

---

### Task 1: [Auth & DB Models] Пользователи, аутентификация и связь с квитанциями

**Files:**
- Create: `backend/app/core/auth.py`
- Create: `backend/app/api/auth.py`
- Modify: `backend/app/db/models.py`
- Modify: `backend/app/db/crud.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_auth.py`

**Interfaces:**
- Produces:
  - `User` модель: `user_id: str`, `username: str`, `email: str`, `hashed_password: str`
  - `get_current_user(token: str = Depends(oauth2_scheme)) -> User`
  - `create_access_token(data: dict) -> str`
  - `POST /api/v1/auth/login` -> `{"access_token": "...", "token_type": "bearer", "user": {...}}`
  - `POST /api/v1/auth/register` -> `{"access_token": "...", "token_type": "bearer", "user": {...}}`
  - `GET /api/v1/auth/me` -> `UserResponse`
  - Внешний ключ `user_id` в таблицах `bills` и `comparisons`

- [ ] **Step 1: Написать падающий тест для аутентификации и моделей**
- [ ] **Step 2: Запустить тест, убедиться в падении**
- [ ] **Step 3: Реализовать `User` в `models.py`, `auth.py`, функции в `crud.py`, роуты `api/auth.py` и seed демо-пользователя в `init_db()`**
- [ ] **Step 4: Запустить тест, убедиться в прохождении**
- [ ] **Step 5: Закоммитить изменения (`feat(auth): add user model, jwt authentication and auth routes`)**

---

### Task 2: [Multimodal Parser Pipeline] Мультимодальный агент распознавания (JSON, PDF, Vision)

**Files:**
- Create: `backend/app/agent/parser.py`
- Modify: `backend/app/agent/__init__.py`
- Test: `backend/tests/test_parser.py`

**Interfaces:**
- Consumes: `BillDocument` из `app.core.models`, `settings` из `app.core.config`
- Produces:
  - `DocumentParser.parse_file(content: bytes, filename: str, mime_type: str) -> BillDocument`
  - `JsonBillParser`: прямой разбор JSON в `BillDocument`
  - `PdfBillParser`: парсинг текстового слоя через `pypdf`, извлечение метаданных и строк услуг
  - `VisionBillParser`: кодирование в Base64, запрос к Vision LLM API (с детерминированным fallback)

- [ ] **Step 1: Написать тесты для парсинга JSON, PDF и Vision fallback**
- [ ] **Step 2: Запустить тест, убедиться в падении**
- [ ] **Step 3: Реализовать `backend/app/agent/parser.py` с тремя парсерами и роутером форматов**
- [ ] **Step 4: Запустить тест, убедиться в прохождении**
- [ ] **Step 5: Закоммитить изменения (`feat(parser): implement multimodal parser for JSON, PDF and Vision`)**

---

### Task 3: [Auto-Comparison Service] Логика авто-поиска истории и факторного анализа

**Files:**
- Create: `backend/app/services/comparison_service.py`
- Modify: `backend/app/db/crud.py`
- Test: `backend/tests/test_comparison_service.py`

**Interfaces:**
- Consumes: `BillDocument` из `app.core.models`, `analyze` из `app.core.analyzer`, `crud` из `app.db`
- Produces:
  - `process_uploaded_bill(db: Session, bill: BillDocument, user_id: str) -> ComparisonReport`:
    1. Сохраняет `curr_bill` в таблицу `bills` с `user_id`.
    2. Вызывает `find_previous_bill(db, user_id, address, period)`.
    3. Если найдена `prev_bill`: запускает полный `analyze(prev_bill, curr_bill)`.
    4. Если первой квитанция: проводит нормативный аудит тарифов Владивостока и аномалий коэффициента 1.5.
    5. Сохраняет `Comparison` в БД с `user_id` и регистрирует в `tools.store_comparison`.
    6. Возвращает готовый `ComparisonReport`.

- [ ] **Step 1: Написать тесты на сценарий с найденной предыдущей квитанцией и сценарий первой квитанции**
- [ ] **Step 2: Запустить тест, убедиться в падении**
- [ ] **Step 3: Реализовать `comparison_service.py` и методы сохранения/поиска в `crud.py`**
- [ ] **Step 4: Запустить тест, убедиться в прохождении**
- [ ] **Step 5: Закоммитить изменения (`feat(analysis): implement auto-comparison service with user history lookup`)**

---

### Task 4: [API Routes & Streamlit UI] Эндпоинты загрузки, история и интерфейс в Streamlit

**Files:**
- Create: `backend/app/api/bills.py`
- Modify: `backend/app/main.py`
- Modify: `web/api_client.py`
- Modify: `web/components/sidebar.py`
- Modify: `web/components/upload_view.py`
- Modify: `web/app.py`
- Test: `backend/tests/test_bills_api.py`

**Interfaces:**
- Consumes: `auth`, `parser`, `comparison_service`
- Produces:
  - `POST /api/v1/bills/upload` (принимает файл, возвращает `ComparisonReport`)
  - `GET /api/v1/bills/history` (список квитанций пользователя)
  - `GET /api/v1/comparisons/history` (список отчетов пользователя)
  - `GET /api/v1/comparisons/{comparison_id}` (детальный отчет)
  - В `web/api_client.py`: методы `upload_bill()`, `get_bill_history()`, `get_comparison_history()`, `login()`
  - В `web/components/sidebar.py`: профиль пользователя и кликабельная история прошлых анализов
  - В `web/components/upload_view.py`: реальная отправка файла на бэк, индикатор прогресса и переход к отчету

- [ ] **Step 1: Написать тесты для эндпоинтов загрузки и истории в FastAPI**
- [ ] **Step 2: Запустить тест, убедиться в падении**
- [ ] **Step 3: Реализовать `backend/app/api/bills.py`, подключить в `main.py`, обновить фронтенд Streamlit**
- [ ] **Step 4: Запустить тест, убедиться в прохождении**
- [ ] **Step 5: Закоммитить изменения (`feat(ui): connect bill upload, user history and profile to Streamlit UI`)**
