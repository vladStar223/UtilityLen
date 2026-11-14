# 🤖 UtilityLens Mobile — AGENTS.md

Инструкция для автономных AI-агентов (Antigravity, Codex, Cursor, Claude Code) по разработке, архитектуре и поддержке мобильного приложения **UtilityLens Mobile**.

---

## 📌 Назначение приложения
**UtilityLens Mobile** — нативное мобильное приложение на Flutter для жителей Владивостока и Приморского края, предназначенное для автоматического аудита начислений за ЖКУ, выявления скрытых переплат и неправомерных штрафных коэффициентов (1.5 и 3.0), проверки ГОСТ QR-кодов и консультаций с AI-юристом по ЖКХ.

---

## 🏗️ Структура проекта `mobile/`

```
mobile/
├── android/                   # Нативные настройки Android (permissions, gradle, theme)
├── assets/
│   └── receipts/              # Встроенные эталонные квитанции Владивостока (ул. Амурская)
├── lib/
│   ├── agent/                 # Клиентский AI-агент и координатор сценариев
│   │   └── utility_lens_agent.dart
│   ├── bloc/                  # Бизнес-логика (BLoC Pattern)
│   │   ├── audit/             # AuditBloc, AuditEvent, AuditState (расчеты, периоды, кейсы)
│   │   ├── chat/              # ChatBloc, ChatEvent, ChatState (SSE стриминг диалога)
│   │   └── profile/           # ProfileBloc, ProfileEvent, ProfileState (объекты, настройки)
│   ├── core/                  # Ядро приложения
│   │   ├── api_client.dart    # Сетевой клиент к FastAPI бэкенду (compare, chat SSE, fallback)
│   │   ├── api_config.dart    # Конфигурация базовых URL и эндпоинтов
│   │   ├── models.dart        # Equatable модели данных (ComparisonReport, ServiceItem и др.)
│   │   └── theme.dart         # Цветовая палитра Light Glassmorphism + Modern Fintech
│   ├── screens/               # 10 ключевых экранов интерфейса
│   │   ├── onboarding_screen.dart     # Экран 1: Онбординг
│   │   ├── scanner_screen.dart        # Экран 2: Интерактивный сканер с лазерным лучом
│   │   ├── home_screen.dart           # Экран 3: Главный дашборд аудита (Hero Card, Аномалии)
│   │   ├── bill_details_screen.dart   # Экран 4: Детализация услуг «Было/Стало»
│   │   ├── alerts_screen.dart         # Экран 6: Центр предупреждений
│   │   ├── analytics_screen.dart      # Экран 7: Интерактивный график динамики начислений
│   │   ├── ai_chat_screen.dart        # Экран 8: Чат с AI-юристом со стримингом SSE
│   │   ├── claim_screen.dart          # Экран 9: Готовая досудебная претензия (ст. 157 ЖК РФ)
│   │   ├── profile_screen.dart        # Экран 10: Профиль и управление объектами недвижимости
│   │   ├── receipts_screen.dart       # История квитанций
│   │   ├── receipt_viewer_screen.dart # Просмотр квитанций из галереи с зумом и детекцией
│   │   └── main_scaffold.dart         # Нижняя 4-вкладочная навигация (Проверка, Квитанции, Аналитика, Профиль)
│   ├── widgets/               # Переиспользуемые виджеты
│   │   ├── anomaly_banner.dart        # Розовый баннер критической аномалии
│   │   ├── anomaly_bottom_sheet.dart  # Экран 5: Шторка подробностей начисления
│   │   ├── bottom_nav_bar.dart        # Нативная нижняя панель навигации
│   │   ├── hero_bill_card.dart        # Фиолетовая Hero-карта с суммой и спарклайном
│   │   ├── receipt_upload_bottom_sheet.dart # Выбор: Галерея / Камера / Образцы Приморья
│   │   └── service_item_row.dart      # Раскрывающаяся строка услуги с факторным анализом
│   └── main.dart              # Точка входа, MultiBlocProvider, темы
├── test/
│   └── widget_test.dart       # Смоук-тесты виджетов
└── pubspec.yaml               # Зависимости проекта
```

---

## ⚙️ Принципы работы с Бэкендом

### 1. Адресация API (`lib/core/api_config.dart`)
* **Боевой сервер:** `http://136.234.72.54:8000`
* **Эмулятор Android:** `http://10.0.2.2:8000`
* **Префикс роутов:** `/api/v1`

### 2. Протокол взаимодействия
1. **Запуск факторного анализа:**
   * Метод: `POST /api/v1/compare`
   * Тело: `{"case_id": "case_02_coeff_15"}` (или `case_04_vladivostok_coeff3`).
   * Ответ: `ComparisonReport`. Содержит уникальный `comparison_id` вида `cmp-...`.
2. **Диалог с AI-юристом (SSE):**
   * Метод: `POST /api/v1/chat/stream`
   * Тело: `{"comparison_id": "cmp-...", "message": "..."}`
   * Ответ: `text/event-stream`. Чанки:
     * `data: {"type": "token", "content": "..."}`
     * `data: {"type": "tool_call", "name": "..."}`
     * `data: {"type": "done"}`
3. **Отказоустойчивость (Offline Fallback):**
   Если бэкенд временно недоступен или отсутствует сеть, `ApiClient` и `AuditBloc` автоматически задействуют детерминированные офлайн-модели (с реальными суммами из квитанций Владивостока).

---

## 🎨 Дизайн-токены (Light Glassmorphism + Modern Fintech)

* **Фон:** `Color(0xFFF7F7FF)`
* **Карточки:** `Color(0xFFFFFFFF)` со скруглением `18.0 - 22.0`
* **Основной акцент:** `Color(0xFF6046E8)`
* **Светлый акцент:** `Color(0xFFEAE6FF)`
* **Критический статус:** `Color(0xFFEF476F)`
* **Предупреждение:** `Color(0xFFFFB938)`
* **Успех:** `Color(0xFF24B47E)`
* **Границы:** `Color(0xFFE7E6F2)`
* **Текст:** `Color(0xFF171735)` (основной), `Color(0xFF777895)` (вторичный).

---

## 🧪 Команды проверки перед коммитом
```bash
# Проверка статического анализа кода
flutter analyze

# Запуск юнит-тестов
flutter test

# Сборка релизного APK
flutter build apk --release

# Установка на подключенное Android устройство
adb push build/app/outputs/flutter-apk/app-release.apk /data/local/tmp/app.apk
adb shell pm install -r -d /data/local/tmp/app.apk
adb shell am start -n com.utilitylens.utilitylens_mobile/.MainActivity
```
