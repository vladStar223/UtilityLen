# Задание: Интеграция PostgreSQL и Redis в бэкенд UtilityLens

Привет! Приступаем к проектированию и интеграции реляционной базы данных PostgreSQL и кэш-хранилища Redis в бэкенд UtilityLens.

Мы находимся на ветке `feat/backend-core`.

---

### ШАГ 1. Зависимости и конфигурация
1. В `backend/requirements.txt` добавь зависимости:
   - `sqlalchemy>=2.0.0`
   - `psycopg2-binary>=2.9.9` (или `asyncpg>=0.29.0`)
   - `alembic>=1.13.0`
   - `redis>=5.0.0`
2. В конфигурации сервиса (`backend/app/core/config.py` или `database.py`) настрой чтение переменных:
   - `DATABASE_URL`:
     * По умолчанию (для автотестов): `sqlite:///./test.db` (или `:memory:`), чтобы `pytest` работал автономно без внешнего Postgres!
     * Для продакшна / docker-compose: `postgresql://postgres:postgres@db:5432/utilitylens`.
   - `REDIS_URL`:
     * По умолчанию: `redis://localhost:6379/0`.
     * Предусмотри прозрачный fallback: если Redis недоступен (ConnectionError / в юнит-тестах), сервис автоматически переключается на внутреннее хранилище, чтобы тесты не падали без поднятого Redis!

---

### ШАГ 2. Замена оперативной памяти на Redis для отчётов
В `backend/app/agent/tools.py` сейчас отчёты хранятся в словаре Python `_REPORTS: Dict = {}` (в оперативной памяти процесса). 
Нужно вынести кэширование в Redis:
1. Создай модуль кэширования `backend/app/core/cache.py` (или `backend/app/db/redis_client.py`):
   - Функции `set_report(comparison_id, data, ttl=86400)` и `get_report(comparison_id)`.
   - Сериализация отчетов и квитанций в JSON и сохранение в Redis по ключу `comparison:{comparison_id}` с TTL 24 часа.
   - При отсутствии подключения к Redis — корректный fallback (in-memory dict).
2. В `backend/app/agent/tools.py`:
   - Замени прямой доступ к глобальному словарю `_REPORTS` на использование функций модуля кэша (`store_comparison` сохраняет в Redis, `_get_stored_comparison` читает из Redis).

---

### ШАГ 3. Проектирование схемы данных PostgreSQL (`backend/app/db/models.py`)
Спроектируй строгие таблицы SQLAlchemy 2.0:

1. **Таблица `bills` (Квитанции):**
   - `id` (int, pk, autoincrement)
   - `bill_id` (str, unique, index) — например, `bill_2026_10`
   - `period` (str) — расчетный месяц (`2026-10`)
   - `address` (str) — обезличенный адрес
   - `payer` (str) — обезличенный плательщик
   - `total_amount` (numeric(10, 2)) — сумма к оплате
   - `qr_data` (text, nullable) — строка QR по ГОСТ
   - `qr_sum_rub` (numeric(10, 2), nullable)
   - `qr_verified` (bool, default=False)
   - `created_at` (datetime)
   - Связи: `services` (1 к N, cascade), `meters` (1 к N, cascade).

2. **Таблица `bill_services` (Строки начислений услуг):**
   - `id` (int, pk)
   - `bill_id` (str, fk -> `bills.bill_id`, ondelete CASCADE)
   - `service_code` (str) — канонический код (`cold_water`, `heating`, etc.)
   - `raw_name` (str) — наименование из квитанции
   - `unit` (str) — единица измерения (`м3`, `Гкал`)
   - `volume` (numeric(10, 3))
   - `tariff` (numeric(10, 2))
   - `total` (numeric(10, 2))
   - `coefficient` (numeric(5, 2), default=1.0)

3. **Таблица `meter_readings` (Показания счетчиков ИПУ):**
   - `id` (int, pk)
   - `bill_id` (str, fk -> `bills.bill_id`, ondelete CASCADE)
   - `meter_id` (str) — серийный номер прибора
   - `service_code` (str)
   - `prev_reading` (numeric(10, 3))
   - `current_reading` (numeric(10, 3))
   - `verification_due_date` (date, nullable) — срок поверки

4. **Таблица `comparisons` (Отчеты факторного анализа):**
   - `id` (int, pk)
   - `comparison_id` (str, unique, index) — `cmp_2026_10_11`
   - `prev_bill_id` (str, nullable)
   - `curr_bill_id` (str, nullable)
   - `delta_abs` (numeric(10, 2))
   - `delta_pct` (numeric(6, 2))
   - `status_level` (str) — `green`, `yellow`, `red`
   - `factor_breakdown` (JSON/JSONB) — дельты тарифа, объема, перерасчетов
   - `summary_data` (JSON/JSONB)
   - `created_at` (datetime)
   - Связи: `anomalies` (1 к N, cascade), `messages` (1 к N, cascade).

5. **Таблица `comparison_anomalies` (Обнаруженные аномалии):**
   - `id` (int, pk)
   - `comparison_id` (str, fk -> `comparisons.comparison_id`, ondelete CASCADE)
   - `code` (str) — `APPLYING_COEFF_1_5`, `SOI_SPIKE`
   - `severity` (str) — `red`, `yellow`
   - `service_category` (str)
   - `title` (str)
   - `impact_rub` (numeric(10, 2))
   - `hint` (text)

6. **Таблица `chat_messages` (История сообщений AI-юриста):**
   - `id` (int, pk)
   - `comparison_id` (str, fk -> `comparisons.comparison_id`, ondelete CASCADE)
   - `role` (str) — `user`, `assistant`, `system`
   - `content` (text)
   - `tool_calls` (JSON/JSONB, nullable)
   - `created_at` (datetime)

---

### ШАГ 4. CRUD операции и интеграция с FastAPI
В `backend/app/db/crud.py`:
- `save_bill(db, bill_doc)`: сохранение квитанции, ее услуг и показаний счетчиков.
- `get_bill(db, bill_id)`: получение квитанции по ID.
- `save_comparison(db, report, prev_bill, curr_bill)`: сохранение отчета факторного анализа и аномалий в Postgres.
- `get_comparison(db, comparison_id)`: получение отчета из БД (или fallback).
- `save_chat_message(db, comparison_id, role, content, tool_calls)`: сохранение сообщений чата в БД.
- `get_chat_history(db, comparison_id)`: получение истории сообщений.

В роутерах (`compare.py`, `chat.py`):
- Интегрируй сохранение в БД через dependency `db: Session = Depends(get_db)`. При этом сохрани возможность работы с памятью/демо-кейсами как fallback.

---

### ШАГ 5. Добавление PostgreSQL и Redis в Docker Compose
В `deploy/docker-compose.yml`:
1. Добавь сервис `db`:
   * образ `postgres:16-alpine`;
   * переменные: `POSTGRES_DB=utilitylens`, `POSTGRES_USER=postgres`, `POSTGRES_PASSWORD=postgres`;
   * volume: `postgres_data:/var/lib/postgresql/data`;
2. Добавь сервис `redis`:
   * образ `redis:7-alpine`;
   * volume: `redis_data:/data`;
3. Сервису `backend` добавь:
   * `DATABASE_URL=postgresql://postgres:postgres@db:5432/utilitylens`;
   * `REDIS_URL=redis://redis:6379/0`;
   * `depends_on`: `[db, redis]`.
4. В секцию `volumes` добавь `postgres_data:` и `redis_data:`.

---

### ШАГ 6. Автотесты и коммит
1. Напиши тесты для кэша и БД в `backend/tests/test_db.py` и `backend/tests/test_cache.py`.
2. Запусти `pytest backend/tests/` и убедись, что ВСЕ автотесты (включая старые 13 тестов API) успешно проходят (зеленые).
3. Закоммить изменения:
   ```bash
   git add backend/ deploy/docker-compose.yml
   git commit -m "feat(db): integrate PostgreSQL, Redis caching for reports, SQLAlchemy models and compose services"
   ```
