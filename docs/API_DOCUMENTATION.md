# UtilityLens API Documentation

## Запуск сервиса

### Локальный запуск

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Открытие документации

После запуска сервера доступны два интерфейса:

| Интерфейс | URL |
|-----------|-----|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

---

## Обзор API

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/health` | Проверка работоспособности сервиса |
| `GET` | `/api/v1/cases` | Получение списка демо-кейсов Владивостока |
| `POST` | `/api/v1/compare` | Запуск факторного анализа по двум квитанциям |
| `POST` | `/api/v1/chat/stream` | SSE-стриминг диалога с AI-юристом |

---

## Детальный разбор эндпоинтов

### `GET /health`

**Описание:** Проверка работоспособности сервиса. Используется для health-check и мониторинга.

**Параметры:** нет

**Ответ (200):**

```json
{
  "status": "ok"
}
```

**Пример curl:**

```bash
curl -X GET http://localhost:8000/health
```

---

### `GET /api/v1/cases`

**Описание:** Возвращает список доступных демо-кейсов для Владивостока. Каждый кейс содержит пару квитанций (предыдущий и текущий периоды) для демонстрации возможностей факторного анализа.

**Параметры:** нет

**Ответ (200):**

```json
{
  "cases": [
    {
      "case_id": "vladivostok-lenina-10",
      "address": "г. Владивосток, ул. Ленина, д. 10, кв. 25",
      "prev_period": "2024-01",
      "curr_period": "2024-02",
      "description": "Типичная квартира: рост тарифов на отопление и воду"
    }
  ]
}
```

**Пример curl:**

```bash
curl -X GET http://localhost:8000/api/v1/cases
```

---

### `POST /api/v1/compare`

**Описание:** Запускает детерминированный факторный анализ по двум квитанциям. Можно указать либо `case_id` для загрузки готового демо-кейса, либо передать две квитанции (`prev_bill` и `curr_bill`) напрямую.

Результат включает:
- **Сводку** — общее изменение суммы, статус, верификация QR-кода;
- **Факторный разбор** — вклад изменения тарифов, объёмов, перерасчётов и новых услуг;
- **Список аномалий** — обнаруженные отклонения с уровнем серьёзности;
- **Детализацию по услугам** — подробный разбор каждой услуги с объяснениями.

**Тело запроса:**

```json
{
  "case_id": "vladivostok-lenina-10"
}
```

Или с загрузкой квитанций:

```json
{
  "prev_bill": {
    "bill_id": "bill-001",
    "period": "2024-01",
    "address": "г. Владивосток, ул. Ленина, 10",
    "total_amount": 4200.50,
    "services": [
      {
        "service_code": "cold_water",
        "raw_name": "Холодное водоснабжение",
        "unit": "м3",
        "volume": 10.5,
        "tariff": 42.00,
        "total": 441.00
      }
    ]
  },
  "curr_bill": {
    "bill_id": "bill-002",
    "period": "2024-02",
    "address": "г. Владивосток, ул. Ленина, 10",
    "total_amount": 4520.75,
    "services": [
      {
        "service_code": "cold_water",
        "raw_name": "Холодное водоснабжение",
        "unit": "м3",
        "volume": 12.5,
        "tariff": 45.50,
        "total": 568.75
      }
    ]
  }
}
```

**Ответ (200):**

```json
{
  "comparison_id": "cmp-20240215-abc123",
  "summary": {
    "prev_period": "2024-01",
    "curr_period": "2024-02",
    "prev_total": 4200.50,
    "curr_total": 4520.75,
    "delta_abs": 320.25,
    "delta_pct": 7.62,
    "qr_verified": true,
    "status_level": "warning"
  },
  "factor_breakdown": {
    "tariff_effect_rub": 150.50,
    "volume_effect_rub": 200.00,
    "recalculation_effect_rub": -30.25,
    "new_services_effect_rub": 0.0
  },
  "anomalies": [
    {
      "code": "TARIFF_SPIKE",
      "severity": "warning",
      "service_category": "water",
      "title": "Резкий рост тарифа на холодную воду",
      "impact_rub": 43.75,
      "hint": "Проверьте обоснованность повышения тарифа"
    }
  ],
  "items": [
    {
      "category": "water",
      "display_name": "Холодное водоснабжение",
      "unit": "м3",
      "prev_volume": 10.5,
      "curr_volume": 12.5,
      "prev_tariff": 42.00,
      "curr_tariff": 45.50,
      "prev_total": 441.00,
      "curr_total": 568.75,
      "delta_abs": 127.75,
      "delta_pct": 28.97,
      "tariff_delta_rub": 43.75,
      "volume_delta_rub": 84.00,
      "coeff_surcharge_rub": 0.0,
      "status": "warning",
      "plain_explanation": "Тариф вырос на 8.3%, потребление увеличилось на 19%"
    }
  ]
}
```

**Коды ошибок:**

- **400** — не указан `case_id` и не переданы обе квитанции
- **404** — демо-кейс с указанным `case_id` не найден или неполный

**Пример curl:**

```bash
curl -X POST http://localhost:8000/api/v1/compare \
  -H "Content-Type: application/json" \
  -d '{"case_id": "vladivostok-lenina-10"}'
```

---

### `POST /api/v1/chat/stream`

**Описание:** Запускает стриминговый диалог с AI-юристом по контексту ранее выполненного сравнения. Ответ передаётся в формате Server-Sent Events (SSE).

**Тело запроса:**

```json
{
  "comparison_id": "cmp-20240215-abc123",
  "message": "Почему выросла сумма за отопление?"
}
```

С историей диалога:

```json
{
  "comparison_id": "cmp-20240215-abc123",
  "message": "А можно оспорить?",
  "history": [
    {"role": "user", "content": "Почему выросла сумма за отопление?"},
    {"role": "assistant", "content": "Тариф вырос на 8.3%..."}
  ]
}
```

**Формат Server-Sent Events (SSE):**

Стрим возвращает события в формате SSE. Каждое событие состоит из двух строк: `event:` и `data:`.

#### Типы событий

**`token`** — фрагмент текста ответа:

```
event: token
data: {"text": "Сумма"}

event: token
data: {"text": " выросла"}

event: token
data: {"text": " на 7.6%"}
```

**`tool_call`** — уведомление о вызове инструмента (например, поиск по нормативам):

```
event: tool_call
data: {"tool": "search_regulations", "args": {"query": "тариф отопление Владивосток 2024"}}
```

**`done`** — завершение стрима:

```
event: done
data: {}
```

#### Обработка на фронтенде

```javascript
const eventSource = new EventSource('http://localhost:8000/api/v1/chat/stream');

eventSource.addEventListener('token', (event) => {
  const data = JSON.parse(event.data);
  console.log('Token:', data.text);
});

eventSource.addEventListener('tool_call', (event) => {
  const data = JSON.parse(event.data);
  console.log('Tool call:', data.tool, data.args);
});

eventSource.addEventListener('done', () => {
  console.log('Stream completed');
  eventSource.close();
});
```

**Коды ошибок:**

- **400** — некорректный запрос (например, пустое сообщение)
- **404** — `comparison_id` не найден в хранилище

**Пример curl:**

```bash
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "comparison_id": "cmp-20240215-abc123",
    "message": "Почему выросла сумма за отопление?"
  }'
```

---

## Модели данных

Полные схемы всех моделей (BillDocument, ComparisonReport и др.) доступны в Swagger UI по адресу http://localhost:8000/docs.

### Единицы измерения

- **Денежные суммы** — рубли, округление до копеек (2 знака после запятой)
- **Объёмы** — единицы измерения услуги (м3, Гкал, кВт·ч)
- **Проценты** — процентные пункты
- **Коэффициенты** — безразмерные величины

---

## Дополнительные ресурсы

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json
