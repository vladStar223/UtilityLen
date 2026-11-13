# 📋 Задание для Агента 1: Backend Core («Бухгалтер»)

## 🎯 Роль и зона ответственности
- **Роль:** Backend Core Engineer («Бухгалтер»).
- **Зона полного доступа:** `backend/app/core/`, `backend/app/ingestion/`, `backend/app/api/`, `backend/tests/`.
- **СТРОГО ЗАПРЕЩЕНО:**
  - Менять файлы в `web/**` и `contracts/**`.
  - Изменять структуры полей в контрактах без согласования с архитектором.

---

## 📝 Список задач (Backlog)

1. **Слой моделей (`backend/app/core/models.py`):**
   - Строгие Pydantic v2 модели: `BillDocument`, `ServiceLine`, `MeterReading`, `ComparisonReport`, `FactorBreakdown`, `AnomalyItem`, `ServiceItem`.
   - Полное совпадение по полям со спецификацией `contracts/compare_response.json` и `contracts/bill_schema.json`.
   - Денежные поля защищены валидатором округления до 2 знаков после запятой (защита от погрешностей float).

2. **Нормализатор услуг (`backend/app/core/normalizer.py`):**
   - Маппинг сырых названий из квитанций в канонические коды:
     - `ХВС`, `Холодная вода`, `Холодное в/с` $\rightarrow$ `cold_water`
     - `КР на СОИ ХВС`, `ХВС ОДН`, `ХВС СОИ` $\rightarrow$ `cold_water_soi`
     - `Отопление`, `Тепловая энергия` $\rightarrow$ `heating`
     - `ГВС`, `Горячая вода` $\rightarrow$ `hot_water`
     - `Содержание жилья`, `Текущий ремонт` $\rightarrow$ `maintenance`

3. **Математическое ядро факторного анализа (`backend/app/core/analyzer.py`):**
   - Построчный расчет:
     - **Эффект тарифа:** $\Delta S_{\text{тариф}} = (T_2 - T_1) \cdot V_1$
     - **Эффект объема:** $\Delta S_{\text{объем}} = T_2 \cdot (V_2 - V_1)$
     - **Эффект коэффициента и перерасчета:** $\Delta S_{\text{прочее}} = S_2 - (T_2 \cdot V_2)$
   - Детекторы аномалий:
     - `APPLYING_COEFF_1_5`: если `coefficient > 1.0` или фактический итог больше базового произведения без перерасчетов.
     - `METER_VERIFICATION_DUE`: срок поверки счетчика истек или истекает менее чем через 60 дней.
     - `SOI_SPIKE`: рост расходов на общедомовые нужды (СОИ / ОДН) более чем на 30%.
     - `OPTIONAL_SERVICE_DETECTED`: обнаружены необязательные строки (антенна, страхование).

4. **Модуль QR-парсинга (`backend/app/ingestion/qr_parser.py`):**
   - Декодер строки ГОСТ Р 56042-2014 (`ST00012|...`):
     - Извлечение поля `Sum` (деление на 100 для перевода копеек в рубли).
     - Извлечение `PaymPeriod`.
     - Сверка суммы квитанции с суммой QR: если расхождение $> 1.00$ ₽, выставляется `qr_verified = False`.

5. **API Роуты (`backend/app/api/`):**
   - `GET /api/v1/cases`: возвращает список кейсов из `data/cases/`.
   - `POST /api/v1/compare`: рассчитывает отчет `ComparisonReport` по двум квитанциям.

6. **Автотесты (`backend/tests/test_analyzer.py`):**
   - Тесты факторного анализа на данных `data/cases/case_02_coeff_15/`.
   - Проверка баланса: сумма всех дельт строк должна сойтись с итоговой дельтой квитанции до копейки.

---

## ✅ Критерий приемки (Definition of Done)
1. Команда `pytest backend/tests/` завершается с кодом 0 (100% тестов зеленые).
2. Выходной JSON метода `POST /api/v1/compare` на эталонном кейсе `case_02_coeff_15` по полям и значениям точно сходится с `contracts/compare_response.json`.
