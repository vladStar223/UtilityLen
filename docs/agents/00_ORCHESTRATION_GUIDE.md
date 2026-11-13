# 🎯 Регламент мультиагентной разработки: Contract-First + Directory Isolation

Чтобы независимые AI-агенты разрабатывали фронтенд, бэкенд и логику агента параллельно без конфликтов слияния и рассинхрона по полям, работа строится по паттерну **Contract-First + Directory Isolation**.

До запуска агентов жестко фиксируется единый JSON-контракт и стабы ответов (`contracts/` и `data/cases/`), а каждому агенту выдается изолированная директория с запретом на редактирование чужих папок.

---

## 1. Матрица владения папками (Directory Lock)

Главное правило оркестрации: **один файл — один владелец**.

```text
utility-lens/
├── contracts/                   # [FROZEN / Архитектор] Схемы API и JSON-контракты (агентам менять запрещено)
│   ├── bill_schema.json         # Каноническая схема одной квитанции
│   └── compare_response.json    # Эталонный ответ /api/v1/compare (мок для фронта)
├── data/                        # [FROZEN / Архитектор] Обезличенные демо-кейсы и база знаний
│   ├── cases/                   # Пары квитанций: case_02_coeff_15/ (prev_bill, curr_bill)
│   └── knowledge_base/          # Словарь ЖКХ (glossary.json) и нормативы ПП РФ №354
├── backend/                     # [AGENT 1: Backend + Math] Полный доступ только внутри backend/
│   ├── app/
│   │   ├── api/                 # Роуты FastAPI
│   │   ├── core/                # Pydantic-модели, нормализатор услуг, факторный анализ
│   │   ├── ingestion/           # QR-валидатор (ГОСТ), парсер таблиц
│   │   └── agent/               # [AGENT 2: AI-Lawyer] Промпты, Tools, SSE-стриминг
│   └── tests/                   # Автотесты математики и API
├── web/                         # [AGENT 3: Frontend] Полный доступ только внутри web/
│   ├── app.py                   # Точка входа (Streamlit)
│   ├── api_client.py            # Адаптер: переключатель Mock JSON ↔ реальный HTTP API
│   └── components/              # Карточки светофора, графики дельт, виджет чата
└── deploy/                      # [Архитектор] docker-compose.yml
```

---

## 2. Единый API-контракт

| Метод и путь | Назначение | Входные данные | Выходные данные |
|---|---|---|---|
| `GET /api/v1/cases` | Список предзагруженных демо-кейсов | — | Массив `{case_id, title, description, periods}` |
| `POST /api/v1/bills/parse` | Загрузка своей квитанции и валидация по QR | `multipart/form-data` (`file`) | `BillDocument` (`qr_match: bool`) |
| `POST /api/v1/compare` | Детерминированное сравнение двух месяцев и поиск аномалий | `{prev_bill_id, curr_bill_id}` или `{case_id}` | `ComparisonReport` (факторный разбор, аномалии) |
| `POST /api/v1/chat/stream` | Потоковый ответ AI-юриста по контексту сравнения | `{comparison_id, message, history}` | `text/event-stream` (SSE) |

Эталонный JSON ответа: `contracts/compare_response.json`.

---

## 3. Запуск параллельной работы через `git worktree`

```bash
# 1. В основной ветке фиксируем контракты и данные
git checkout main

# 2. Создаем изолированные рабочие директории под каждого агента
git worktree add ../ul-backend -b feat/backend-core
git worktree add ../ul-frontend -b feat/web-ui

# 3. Запускаем Агента 1 в папке ../ul-backend
# 4. Запускаем Агента 3 в папке ../ul-frontend

# 5. Когда оба закончили — сливаем ветки в main без конфликтов:
git checkout main
git merge feat/backend-core
git merge feat/web-ui

# 6. Запуск через docker-compose
docker compose -f deploy/docker-compose.yml up --build
```
