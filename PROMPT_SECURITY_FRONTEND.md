# 🛡️ Задание: Комплексное устранение уязвимостей и hardening фронтенда и инфраструктуры UtilityLens (F1–F6, I1–I3)

Привет! Приступаем к реализации критического пакета безопасности и харденинга фронтенда (Streamlit) и инфраструктуры развертывания проекта UtilityLens.

---

### ШАГ 1. Создание рабочей ветки
Создай новую ветку `fix/security-frontend-infra` от актуальной ветки `main` и переключись на нее:
```bash
git checkout -b fix/security-frontend-infra
```

---

### ШАГ 2. F1 — Устранение XSS в карточках (Экранирование динамических данных)

**Цель:** Исключить выполнение внедренного HTML/JS-кода при рендеринге пользовательских и динамических данных.

1. **`web/components/ai_explanation.py`**:
   - Импортируй стандартный модуль `html`.
   - Перед подстановкой в f-строку `card_html` экранируй все динамические переменные:
     ```python
     import html

     safe_summary = html.escape(str(ai_summary))
     ```
   - В блоке построчных пояснений (`item_explanations`) экранируй `name` и `expl` перед выводом:
     ```python
     name = html.escape(str(it.get("display_name", "Услуга")))
     expl = html.escape(str(it.get("plain_explanation", "")))
     st.markdown(f"• **{name}:** {expl}")
     ```

2. **`web/components/anomalies.py`**:
   - Импортируй `html`.
   - Экранируй динамические поля перед генерацией карточки:
     ```python
     safe_title = html.escape(str(a.get("title", "Аномалия")))
     safe_hint = html.escape(str(a.get("hint", "")))
     safe_impact = f"{float(a.get('impact_rub', 0)):,.2f}"
     ```
   - Замени вставку сырых `title` и `hint` в `card_html` на `safe_title` и `safe_hint`.

3. **`web/components/sidebar.py`**:
   - Если в сайдбаре отображаются названия и описания из списка кейсов, экранируй их через `html.escape()`.

**Критерий приемки (F1):**
При передаче в поле `hint` строки `<script>alert(1)</script>` или `<img src=x onerror=alert(1)>` скрипт не исполняется, а отображается в DOM в виде безопасного текста `&lt;script&gt;alert(1)&lt;/script&gt;`.

---

### ШАГ 3. F2 — Передача API-ключа в запросах к бэкенду

**Цель:** Обеспечить поддержку межсервисной аутентификации через API-ключ.

1. **`web/api_client.py`**:
   - В начале модуля добавь чтение API-ключа из переменной окружения:
     ```python
     API_KEY = os.getenv("API_KEY", "").strip()
     ```
   - В класс `ApiClient` добавь атрибут `self.api_key = API_KEY` и вспомогательный метод формирования заголовков:
     ```python
     def _get_headers(self) -> Dict[str, str]:
         headers = {}
         if self.api_key:
             headers["X-API-Key"] = self.api_key
             headers["Authorization"] = f"Bearer {self.api_key}"
         return headers
     ```
   - Передай `headers=self._get_headers()` во ВСЕ исходящие вызовы `httpx`:
     - `httpx.get(f"{self.api_base_url}/api/v1/cases", headers=self._get_headers(), timeout=3.0)`
     - `httpx.post(f"{self.api_base_url}/api/v1/compare", headers=self._get_headers(), ...)`
     - `httpx.stream("POST", f"{self.api_base_url}/api/v1/chat/stream", headers=self._get_headers(), ...)`
     - `httpx.get(f"{self.api_base_url}/health", headers=self._get_headers(), timeout=1.5)`

2. **`web/.env.example`**:
   - Добавь описание переменной `API_KEY`:
     ```env
     # Секретный API-ключ для авторизации в бэкенде (передается в заголовках X-API-Key и Authorization)
     API_KEY=
     ```

**Критерий приемки (F2):**
При задании `API_KEY=secret_token` все запросы к FastAPI уходят с заголовками `X-API-Key: secret_token` и `Authorization: Bearer secret_token`.

---

### ШАГ 4. F3 — Безопасная конфигурация Streamlit для продакшна

**Цель:** Защитить Streamlit от атак межсайтовой подделки запросов (XSRF) и несанкционированного доступа.

1. **Создай файл `web/.streamlit/config.toml`**:
   ```toml
   [server]
   port = 8501
   address = "0.0.0.0"
   headless = true
   enableCORS = false
   enableXsrfProtection = true
   maxUploadSize = 10

   [browser]
   gatherUsageStats = false

   [theme]
   primaryColor = "#7c3aed"
   backgroundColor = "#f8fafc"
   secondaryBackgroundColor = "#ede9fe"
   textColor = "#0f172a"
   ```

2. **Обнови `web/.env.example`**:
   ```env
   # Включение защиты от межсайтовой подделки запросов (XSRF)
   STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
   # Отключение CORS, так как Streamlit отдается через единый reverse proxy
   STREAMLIT_SERVER_ENABLE_CORS=false
   # Запрет сбора телеметрии
   STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
   # Лимит на размер загружаемого файла (в МБ)
   STREAMLIT_SERVER_MAX_UPLOAD_SIZE=10
   ```

3. **Обнови `web/Dockerfile`**:
   Убедись, что переменные окружения прописаны в образе по умолчанию:
   ```dockerfile
   ENV PYTHONUNBUFFERED=1 \
       PYTHONDONTWRITEBYTECODE=1 \
       STREAMLIT_SERVER_PORT=8501 \
       STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
       STREAMLIT_SERVER_HEADLESS=true \
       STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true \
       STREAMLIT_SERVER_ENABLE_CORS=false \
       STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
       STREAMLIT_SERVER_MAX_UPLOAD_SIZE=10
   ```

**Критерий приемки (F3):**
При запуске контейнера защита XSRF активна, телеметрия отключена, максимальный размер загрузки ограничен 10 МБ.

---

### ШАГ 5. F4 — Клиентская валидация и ограничение загрузки файлов

**Цель:** Не допустить загрузки вредоносных бинарных файлов и превышения объема памяти при заливке квитанций.

В файле `web/components/upload_view.py`:
1. Добавь константы и функцию проверки сигнатур файлов (Magic Bytes):
   ```python
   import json

   MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

   def validate_file(uploaded_file) -> tuple[bool, str]:
       """Проверяет реальный размер и сигнатуру файла (Magic Bytes)."""
       if uploaded_file.size > MAX_FILE_SIZE_BYTES:
           return False, f"Размер файла ({uploaded_file.size / (1024*1024):.1f} МБ) превышает лимит 10 МБ."

       # Читаем первые 512 байт для проверки сигнатуры
       header = uploaded_file.read(512)
       uploaded_file.seek(0)  # Сбрасываем указатель назад

       name_lower = uploaded_file.name.lower()

       # Проверка PNG
       if name_lower.endswith(".png"):
           if header.startswith(b"\x89PNG\r\n\x1a\n"):
               return True, "OK"
           return False, "Файл имеет расширение .png, но не является валидным изображением PNG."

       # Проверка JPEG
       if name_lower.endswith((".jpg", ".jpeg")):
           if header.startswith(b"\xff\xd8\xff"):
               return True, "OK"
           return False, "Файл имеет расширение .jpg/.jpeg, но не является валидным изображением JPEG."

       # Проверка PDF
       if name_lower.endswith(".pdf"):
           if header.startswith(b"%PDF-"):
               return True, "OK"
           return False, "Файл имеет расширение .pdf, но поврежден или не является валидным PDF."

       # Проверка JSON
       if name_lower.endswith(".json"):
           try:
               content = uploaded_file.read().decode("utf-8")
               uploaded_file.seek(0)
               json.loads(content)
               return True, "OK"
           except Exception:
               uploaded_file.seek(0)
               return False, "Файл имеет расширение .json, но содержит некорректный синтаксис JSON."

       return False, "Неподдерживаемый формат файла. Допустимы только PNG, JPG, PDF и JSON."
   ```

2. Внутри `render_upload_view()` при наличии `uploaded_file`:
   ```python
   is_valid, error_msg = validate_file(uploaded_file)
   if not is_valid:
       st.error(f"❌ Ошибка валидации файла: {error_msg}")
       return
   ```

**Критерий приемки (F4):**
Файл размером > 10 МБ или файл `.png`, содержащий текстовый скрипт, отклоняется с понятным сообщением об ошибке без падения приложения.

---

### ШАГ 6. F5 — Подавление сырых исключений в интерфейсе и логирование

**Цель:** Скрыть внутренние трейсбеки, пути к файлам и детали ошибок инфраструктуры от конечного пользователя.

1. **`web/api_client.py`**:
   - Настрой логгер модуля:
     ```python
     import logging
     logger = logging.getLogger("utilitylens.web")
     ```
   - Оберни метод `compare_bills` в безопасную обработку исключений:
     ```python
     def compare_bills(self, case_id: str = "case_02_coeff_15") -> Dict[str, Any]:
         if self.use_mock:
             # Существующая логика моков...
             ...
         try:
             response = httpx.post(
                 f"{self.api_base_url}/api/v1/compare",
                 json={"case_id": case_id},
                 headers=self._get_headers(),
                 timeout=10.0,
             )
             response.raise_for_status()
             data = response.json()
             if not data.get("ai_summary"):
                 data["ai_summary"] = self._synthesize_ai_summary(data)
             return data
         except httpx.HTTPStatusError as exc:
             logger.error("HTTP error from backend %s: %s", exc.response.status_code, exc, exc_info=True)
             return {"error": f"Ошибка сервера аналитики (код {exc.response.status_code}). Попробуйте позже."}
         except (httpx.ConnectError, httpx.TimeoutException) as exc:
             logger.error("Backend connection failed: %s", exc, exc_info=True)
             return {"error": "Сервер аналитики временно недоступен. Проверьте соединение."}
         except Exception as exc:
             logger.error("Unexpected error in compare_bills: %s", exc, exc_info=True)
             return {"error": "Произошла непредвиденная ошибка при анализе квитанции."}
     ```
   - В методе `chat_stream` логируй исключения в лог и отдавай чистое сообщение:
     ```python
     except Exception as exc:
         logger.error("Chat streaming error: %s", exc, exc_info=True)
         yield "⚠️ Не удалось получить ответ от AI-юриста. Пожалуйста, повторите вопрос позже."
     ```

2. **`web/app.py`**:
   - При отображении экрана `analysis` проверяй наличие ключа `error`:
     ```python
     result = st.session_state["analysis_result"]
     if result.get("error"):
         st.error(f"⚠️ {result['error']}")
         if st.button("🔄 Повторить попытку"):
             st.session_state["analysis_result"] = None
             st.rerun()
         st.stop()
     ```

**Критерий приемки (F5):**
При остановленном бэкенде в интерфейсе появляется аккуратная плашка с кнопкой повтора вместо красного Python-стектрейса `httpx.ConnectError`.

---

### ШАГ 7. F6 — Маскирование персональных данных (ПДн) в интерфейсе

**Цель:** Защитить персональные данные плательщиков при демонстрации экрана или шеринге скриншотов.

1. **Создай утилиту `web/utils/masking.py`**:
   ```python
   import re

   def mask_personal_account(account: str) -> str:
       """Маскирует номер лицевого счета: оставляет первые 3 и последние 4 цифры."""
       if not account:
           return ""
       digits = re.sub(r"\D", "", str(account))
       if len(digits) <= 7:
           return "***"
       return f"{digits[:3]}***{digits[-4:]}"

   def mask_address(address: str) -> str:
       """Обезличивает точный номер квартиры в адресе."""
       if not address:
           return ""
       # Заменяет 'кв. 25' / 'кв. 102' на 'кв. **'
       return re.sub(r"(кв\.?\s*)\d+", r"\1**", str(address), flags=re.IGNORECASE)

   def mask_fio(fio: str) -> str:
       """Заменяет полное ФИО на обезличенного собственника."""
       if not fio:
           return "Собственник помещения"
       return "Собственник помещения"
   ```

2. **Примени маскирование в компонентах**:
   - В `web/components/sidebar.py`: при выводе адресов и счетов кейсов пропускай их через `mask_address` и `mask_personal_account`.
   - В `web/components/table_view.py`: если в таблице начислений присутствуют реквизиты плательщика или счет, маскируй их.

**Критерий приемки (F6):**
В интерфейсе UtilityLens отсутствуют полные номера лицевых счетов и точные номера квартир.

---

### ШАГ 8. I1 — Reverse-proxy c TLS и заголовками безопасности (Nginx)

**Цель:** Создать единую защищенную точку входа с rate-limiting, SSL/TLS терминацией и security-заголовками.

1. **Создай директорию `deploy/nginx/` и файл `deploy/nginx/nginx.conf`**:
   ```nginx
   events {
       worker_connections 1024;
   }

   http {
       include       /etc/nginx/mime.types;
       default_type  application/octet-stream;

       # Rate limiting: 10 запросов в секунду с одного IP
       limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
       limit_req_zone $binary_remote_addr zone=web_limit:10m rate=20r/s;

       # Лимит размера тела запроса (10 МБ для квитанций)
       client_max_body_size 10M;

       # Защитные HTTP-заголовки
       add_header X-Frame-Options "SAMEORIGIN" always;
       add_header X-Content-Type-Options "nosniff" always;
       add_header X-XSS-Protection "1; mode=block" always;
       add_header Referrer-Policy "strict-origin-when-cross-origin" always;

       upstream backend_upstream {
           server backend:8000;
       }

       upstream web_upstream {
           server web:8501;
       }

       server {
           listen 80;
           server_name localhost;

           # Проксирование API запросов
           location /api/ {
               limit_req zone=api_limit burst=20 nodelay;
               proxy_pass http://backend_upstream;
               proxy_set_header Host $host;
               proxy_set_header X-Real-IP $remote_addr;
               proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
               proxy_set_header X-Forwarded-Proto $scheme;
               
               # Поддержка SSE-стриминга (отключение буферизации для чата)
               proxy_buffering off;
               proxy_cache off;
               proxy_read_timeout 120s;
           }

           # Проксирование WebSockets и статики Streamlit
           location /_stcore/ {
               proxy_pass http://web_upstream;
               proxy_http_version 1.1;
               proxy_set_header Upgrade $http_upgrade;
               proxy_set_header Connection "upgrade";
               proxy_set_header Host $host;
               proxy_read_timeout 86400s;
           }

           # Фронтенд Streamlit
           location / {
               limit_req zone=web_limit burst=40 nodelay;
               proxy_pass http://web_upstream;
               proxy_http_version 1.1;
               proxy_set_header Upgrade $http_upgrade;
               proxy_set_header Connection "upgrade";
               proxy_set_header Host $host;
               proxy_set_header X-Real-IP $remote_addr;
               proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           }
       }
   }
   ```

2. **Добавь сервис `nginx` в `deploy/docker-compose.yml`**:
   ```yaml
     nginx:
       image: nginx:1.25-alpine
       ports:
         - "80:80"
       volumes:
         - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
       depends_on:
         - backend
         - web
   ```

---

### ШАГ 9. I2 — Обновление .env.example и docker-compose.yml

1. **`backend/.env.example`**:
   Добавь в конец:
   ```env
   # Секретный API-ключ для проверки входящих запросов от фронтенда (если пустой — проверка отключена)
   API_KEY=

   # Пароль базы данных PostgreSQL для продакшна (в Docker)
   POSTGRES_PASSWORD=postgres

   # Таймаут вызова внешнего LLM-провайдера (секунды)
   LLM_TIMEOUT_S=5.0
   ```

2. **`web/.env.example`**:
   Убедись, что добавлены `API_KEY` и безопасные флаги Streamlit.

3. **`deploy/docker-compose.yml`**:
   - В сервисе `db` используй `${POSTGRES_PASSWORD:-postgres}`.
   - В сервисах `backend` и `web` передай переменную `API_KEY`:
     ```yaml
     environment:
       - API_KEY=${API_KEY:-}
     ```

---

### ШАГ 10. I3 — Документация по безопасности (SECURITY.md и архитектура)

1. **Создай файл `SECURITY.md` в корне репозитория**:
   ```markdown
   # Политика безопасности UtilityLens

   ## Поддерживаемые версии
   Обновления безопасности выпускаются для актуальной версии ветки `main`.

   ## Сообщение об уязвимости
   Если вы обнаружили уязвимость безопасности в UtilityLens, пожалуйста, не открывайте публичный issue.
   Направьте сообщение команде безопасности на email: `security@utilitylens.local` или в личные сообщения мейнтейнеров.

   ## Принятые меры безопасности
   - Защита от XSS через принудительное экранирование динамического HTML (`html.escape`).
   - Изоляция API через проверку заголовков `X-API-Key` и `Authorization`.
   - Защита от переполнения памяти: клиентский и серверный лимит 10 МБ на загрузку квитанций.
   - Проверка сигнатур файлов (Magic Bytes) против атак загрузки вредоносных файлов.
   - Маскирование персональных данных (ПДн) плательщиков и номеров лицевых счетов.
   - Rate-limiting и фильтрация заголовков на уровне Nginx reverse proxy.
   ```

2. **Создай документ `docs/SECURITY_AND_AUTH.md`**:
   Опиши детально:
   - Схему межсервисной аутентификации (`X-API-Key` / `Bearer`).
   - Настройки CORS и XSRF.
   - Регламент валидации и сигнатуры файлов.
   - Конфигурацию Nginx и лимиты rate-limit.

---

### ШАГ 11. Проверка и верификация решения

Выполни контрольные проверки:
1. Запусти валидацию XSS:
   - Передай в `hint` аномалии текст `<script>alert(1)</script>`. Убедись, что в инспекторе браузера он отображается как `&lt;script&gt;` и не исполняется.
2. Проверь отправку заголовков API-ключа:
   - Запусти тест с `API_KEY=test_key` и убедись, что `_get_headers()` возвращает `X-API-Key` и `Authorization`.
3. Проверь валидацию загрузки файлов:
   - Попробуй загрузить файл > 10 МБ или текстовый файл с расширением `.png`. Должна появиться русскоязычная ошибка валидации.
4. Убедись в отсутствии необработанных исключений:
   - Запусти UI при выключенном бэкенде — приложение не должно падать в красный трейсбек.

---

### ШАГ 12. Фиксация изменений в Git
Добавь все измененные и новые файлы и создай коммит:
```bash
git add web/ deploy/ docs/ SECURITY.md backend/.env.example
git commit -m "fix(security): resolve F1-F6 and I1-I3 security vulnerabilities and hardening"
```
