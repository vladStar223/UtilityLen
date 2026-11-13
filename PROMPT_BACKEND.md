# Задание на разработку Backend Core для UtilityLens

Привет! Приступаем к разработке бэкенд-части проекта UtilityLens («Объясни мою квитанцию»).

### ШАГ 1. Создание рабочей ветки
Создай новую ветку `feat/backend-core` от текущего состояния и переключись на нее:
```bash
git checkout -b feat/backend-core
```

---

### ШАГ 2. Изучение документации и контрактов
Перед написанием кода внимательно прочитай и используй как спецификацию следующие файлы:
1. `contracts/bill_schema.json` — каноническая схема квитанции `BillDocument`.
2. `contracts/compare_response.json` — эталонный выходной JSON отчета `ComparisonReport` (эндпоинт /api/v1/compare).
3. `docs/agents/01_BACKEND_CORE_AGENT.md` — детальное задание на модели, нормализатор, математику факторного анализа и QR-парсер.
4. `docs/agents/02_AI_LAWYER_AGENT.md` — задание на AI-юриста (tools, системный промпт, SSE-стриминг, генерацию претензий).
5. `docs/BRANCH_WORKFLOW_AND_STRUCTURE.md` — целевая файловая структура каталога `backend/`.
6. `docs/vladivostok_kb_design/knowledge_base/` — база знаний (`glossary.json`, `rules_and_faq.json`, `claim_templates.json`).
7. `data/cases/case_02_coeff_15/` — эталонные данные для тестирования (`prev_bill.json`, `curr_bill.json`).

ВАЖНОЕ ПРАВИЛО (Directory Lock): Тебе разрешено создавать и изменять файлы ТОЛЬКО внутри каталога `backend/`. Файлы в `contracts/` и `web/` изменять СТРОГО ЗАПРЕЩЕНО.

---

### ШАГ 3. Реализация бэкенда (`backend/`)
Создай структуру директорий и реализуй файлы:

1. `backend/requirements.txt`:
   Зависимости: `fastapi>=0.110.0`, `uvicorn[standard]>=0.28.0`, `pydantic>=2.6.0`, `httpx>=0.27.0`, `pytest>=8.0.0`, `pytest-asyncio>=0.23.0`.

2. `backend/app/core/models.py`:
   - Pydantic v2 модели: `BillDocument`, `ServiceLine`, `MeterReading`, `ComparisonReport`, `SummaryReport`, `FactorBreakdown`, `AnomalyItem`, `ServiceItem`.
   - Поля должны ТОЧНО соответствовать `contracts/bill_schema.json` и `contracts/compare_response.json`.
   - Денежные поля защити валидатором округления до 2 знаков после запятой (`round(v, 2)`).

3. `backend/app/core/normalizer.py`:
   - Сопоставление сырых наименований услуг из квитанций в канонические коды:
     * ХВС, Холодная вода -> `cold_water`
     * ГВС, Горячая вода -> `hot_water`
     * Отопление, Тепловая энергия -> `heating`
     * Электроэнергия, Свет -> `electricity`
     * КР на СОИ ХВС, ОДН ХВС -> `cold_water_soi`
     * Содержание жилья, Текущий ремонт -> `maintenance`
     * Обращение с ТКО, Вывоз мусора -> `waste`

4. `backend/app/core/analyzer.py`:
   - Детерминированный факторный анализ:
     * Эффект тарифа: dS_tariff = (T2 - T1) * V1
     * Эффект объема: dS_volume = T2 * (V2 - V1)
     * Прочие эффекты / перерасчеты: dS_recalc = S2 - (T2 * V2)
     * Сходимость баланса: сумма дельт по всем строкам должна сходиться с итоговой дельтой квитанции до копейки.
   - Детекторы аномалий:
     * `APPLYING_COEFF_1_5` и `APPLYING_COEFF_3_0` (штрафной коэффициент);
     * `METER_VERIFICATION_DUE` (истек срок поверки);
     * `SOI_SPIKE` (рост расходов на СОИ/ОДН > 30%);
     * `OPTIONAL_SERVICE_DETECTED` (навязанные услуги: страхование, антенна).

5. `backend/app/ingestion/qr_parser.py`:
   - Декодер строки ГОСТ Р 56042-2014 (`ST00012|...`):
     * Извлечение `Sum` (деление на 100 для перевода копеек в рубли).
     * Извлечение `PaymPeriod`.
     * Сверка суммы квитанции с суммой QR: если расхождение > 1.00 ₽, выставлять `qr_verified = False`.

6. `backend/app/agent/tools.py`:
   - `lookup_glossary(term: str)`: поиск определений и статей ПП РФ № 354 в `knowledge_base/glossary.json`.
   - `get_anomaly_action_plan(anomaly_code: str)`: поиск плана действий в `knowledge_base/rules_and_faq.json`.
   - `draft_uk_claim(comparison_id: str, anomaly_code: str)`: подстановка данных из `ComparisonReport` в шаблон из `knowledge_base/claim_templates.json`.

7. `backend/app/agent/runner.py`:
   - Системный промпт AI-юриста (роль эксперта по ЖКХ, нулевые галлюцинации в цифрах, обязательная маркировка утверждений: `[Факт из квитанции]`, `[Математический расчет]`, `[Аналитическая гипотеза]`).
   - Функция маскирования ПДн (ФИО -> «Собственник помещения», адрес -> «г. Владивосток, МКД», номер л/с -> «40702***1234»).
   - SSE-генератор потоковых ответов (`text/event-stream`) с типами событий `token`, `tool_call`, `done`.
   - Автономный fallback: если LLM API не отвечает или вернул ошибку, возвращать готовый текст из `rules_and_faq.json`.

8. `backend/app/api/`:
   - `cases.py`: `GET /api/v1/cases` — отдает список кейсов из папки `data/cases/`.
   - `compare.py`: `POST /api/v1/compare` — принимает две квитанции (или `case_id`), запускает факторный анализ и отдает `ComparisonReport`.
   - `chat.py`: `POST /api/v1/chat/stream` — принимает `{comparison_id, message, history}` и отдает SSE-стриминг ответа юриста.

9. `backend/app/main.py`:
   - Точка входа FastAPI, CORS middleware для фронтенда (порты 8501, 3000), регистрация роутеров с префиксом `/api/v1`.

10. `backend/Dockerfile`:
    - Базовый образ `python:3.11-slim`, установка зависимостей из `requirements.txt`, запуск через uvicorn на порту 8000.

11. `backend/tests/`:
    - `test_analyzer.py`: юнит-тесты на факторный анализ с использованием данных `data/cases/case_02_coeff_15/`. Проверка того, что результат точно совпадает со структурой `contracts/compare_response.json`.
    - `test_agent.py`: тесты вызова инструментов `lookup_glossary` и целостности сумм в претензиях.

---

### ШАГ 4. Фиксация результата
После реализации всех файлов проверь статус через `git status` и создай коммит:
```bash
git add backend/
git commit -m "feat(backend): implement FastAPI core, math analyzer, QR parser, AI-lawyer agent and tests"
```
