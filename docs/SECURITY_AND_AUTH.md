# Безопасность и межсервисная аутентификация UtilityLens

Документ описывает меры безопасности фронтенда (Streamlit) и инфраструктуры
развертывания, а также схему межсервисной аутентификации между фронтендом и
бэкендом FastAPI.

## 1. Межсервисная аутентификация (X-API-Key / Bearer)

Фронтенд (`web/api_client.py`) читает общий секрет из переменной окружения
`API_KEY` и добавляет его в каждый исходящий запрос к бэкенду:

```python
API_KEY = os.getenv("API_KEY", "").strip()

def _get_headers(self) -> Dict[str, str]:
    headers = {}
    if self.api_key:
        headers["X-API-Key"] = self.api_key
        headers["Authorization"] = f"Bearer {self.api_key}"
    return headers
```

Итоговые заголовки для всех запросов (`/api/v1/cases`, `/api/v1/compare`,
`/api/v1/chat/stream`, `/health`):

- `X-API-Key: <API_KEY>`
- `Authorization: Bearer <API_KEY>`

Бэкенд (`backend/.env.example`) читает тот же `API_KEY` для проверки входящих
запросов. Если переменная пустая — проверка отключена (режим разработки).
В Docker Compose значение пробрасывается через `${API_KEY:-}`.

## 2. Настройки CORS и XSRF

Streamlit в продакшне отдаётся через единый reverse proxy (Nginx), поэтому
межсайтовый доступ отключён, а защита от подделки запросов включена:

```toml
[server]
enableCORS = false
enableXsrfProtection = true
```

Соответствующие переменные окружения заданы в `web/Dockerfile` и
`web/.env.example`:

- `STREAMLIT_SERVER_ENABLE_CORS=false`
- `STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true`

Телеметрия отключена: `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false`.

## 3. Регламент валидации и сигнатуры файлов

Загрузка квитанций ограничена на клиентской стороне (`web/components/upload_view.py`):

- Максимальный размер файла — 10 МБ (`MAX_FILE_SIZE_BYTES`).
- Проверка Magic Bytes по расширению файла:
  - `.png` — `\x89PNG\r\n\x1a\n`
  - `.jpg`/`.jpeg` — `\xff\xd8\xff`
  - `.pdf` — `%PDF-`
  - `.json` — корректный синтаксис JSON (`json.loads`)
- Допустимые форматы: PNG, JPG, PDF, JSON.

На уровне Nginx действует серверный лимит тела запроса
`client_max_body_size 10M`.

## 4. Конфигурация Nginx и лимиты rate-limit

`deploy/nginx/nginx.conf` реализует единую точку входа:

- Rate-limiting по IP:
  - `/api/` — `10r/s` (burst 20).
  - `/` (фронтенд) — `20r/s` (burst 40).
- `client_max_body_size 10M` — серверный лимит на загрузку.
- Защитные заголовки:
  - `X-Frame-Options: SAMEORIGIN`
  - `X-Content-Type-Options: nosniff`
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`
- SSE-стриминг для чата: `proxy_buffering off`, `proxy_read_timeout 120s`.
- WebSocket-апгрейд для `/_stcore/` (Streamlit).

## 5. Защита от XSS и маскирование ПДн

- Динамические данные экранируются через `html.escape` перед вставкой в HTML
  (`ai_explanation.py`, `anomalies.py`, `sidebar.py`).
- Персональные данные маскируются утилитой `web/utils/masking.py`:
  - `mask_personal_account` — номер лицевого счёта (первые 3 и последние 4 цифры).
  - `mask_address` — номер квартиры в адресе.
  - `mask_fio` — ФИО владельца.
- Сырые исключения бэкенда скрываются от пользователя и пишутся в лог
  (`logging.getLogger("utilitylens.web")`), в интерфейсе отображается
  дружелюбное сообщение с кнопкой повтора.
