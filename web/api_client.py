"""API Client for interacting with the backend service."""
import os
import json
import logging
from typing import Generator, Dict, Any, List
from pathlib import Path

import httpx
import streamlit as st

logger = logging.getLogger("utilitylens.web")

USE_MOCK_API = os.getenv("USE_MOCK_API", "false").lower() in ("true", "1", "yes")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "").strip()

_DEFAULT_AI_SUMMARY = (
    "Детализированный факторный анализ выполнен на бэкенде. "
    "Все составляющие дельты разложены на тарифную и объемную компоненты."
)


class ApiClient:
    def __init__(self):
        self.use_mock = USE_MOCK_API
        self.api_base_url = API_BASE_URL
        self.api_key = API_KEY

    def _get_headers(self) -> Dict[str, str]:
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def get_cases(self) -> List[Dict[str, Any]]:
        if not self.use_mock:
            try:
                response = httpx.get(
                    f"{self.api_base_url}/api/v1/cases",
                    headers=self._get_headers(),
                    timeout=3.0,
                )
                response.raise_for_status()
                cases = response.json().get("cases", [])
                if cases:
                    return [
                        {
                            "case_id": case.get("case_id", ""),
                            "title": case.get("title") or case.get("description", ""),
                            "description": case.get("description", ""),
                        }
                        for case in cases
                        if case.get("case_id")
                    ]
                return []
            except Exception as exc:
                logger.error("Failed to fetch live cases from backend: %s", exc)
                return []
        return self._mock_cases()

    def compare_bills(self, case_id: str = "case_02_coeff_15") -> Dict[str, Any]:
        if self.use_mock:
            if case_id == "case_02_coeff_15":
                contract_path = self._find_contract_file()
                res = None
                if contract_path is not None:
                    try:
                        with open(contract_path, "r", encoding="utf-8") as f:
                            res = json.loads(f.read())
                    except (OSError, json.JSONDecodeError):
                        pass
                if res is None:
                    res = self._coeff_15_mock()
                res["ai_summary"] = (
                    "Внимание: В квитанции за ноябрь 2026 г. обнаружена скрытая переплата. "
                    "Управляющая компания применила штрафной повышающий коэффициент 1.5 к нормативу "
                    "холодного водоснабжения на сумму +245.18 ₽ из-за истекшего срока поверки счетчика. "
                    "В соответствии с п. 59-60 ПП РФ № 354, начисление коэффициента без предварительного "
                    "3-месячного расчета по среднему незаконно. Рекомендуется подать заявление на перерасчет."
                )
                return res
            if case_id == "case_01_heating_spike":
                res = self._heating_spike_mock()
                res["ai_summary"] = (
                    "Анализ начислений: Тариф на отопление остался строго на уровне прошлого месяца (4 000.00 ₽/Гкал). "
                    "Весь прирост счета (+1 700.00 ₽, +32.7%) вызван исключительно ростом объема потребленного тепла "
                    "(с 1.3 до 1.725 Гкал) в связи с сезонным похолоданием в ноябре. "
                    "Перерасчетов, скрытых комиссий и начислений по нормативу не зафиксировано."
                )
                return res
            if case_id == "case_03_tariff_index":
                res = self._tariff_index_mock()
                res["ai_summary"] = (
                    "Анализ начислений: Потребление ресурсов вашей квартирой осталось на прежнем уровне. "
                    "Увеличение итогового платежа на +450.00 ₽ (+9.0%) связано исключительно с плановой "
                    "городской индексацией тарифов на водоснабжение и электроэнергию с 1 июля. "
                    "Все начисления соответствуют утвержденным региональным нормативам."
                )
                return res
            raise ValueError(f"Unknown mock case_id: {case_id}")

        try:
            response = httpx.post(
                f"{self.api_base_url}/api/v1/compare",
                json={"case_id": case_id},
                headers=self._get_headers(),
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            if (
                "ai_summary" not in data
                or not data["ai_summary"]
                or data["ai_summary"] == _DEFAULT_AI_SUMMARY
            ):
                data["ai_summary"] = self._synthesize_ai_summary(data)
            return data
        except httpx.HTTPStatusError as exc:
            logger.error(
                "HTTP error from backend %s: %s",
                exc.response.status_code,
                exc,
                exc_info=True,
            )
            return {
                "error": (
                    f"Ошибка сервера аналитики (код {exc.response.status_code}). "
                    "Попробуйте позже."
                )
            }
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error("Backend connection failed: %s", exc, exc_info=True)
            return {"error": "Сервер аналитики временно недоступен. Проверьте соединение."}
        except Exception as exc:
            logger.error("Unexpected error in compare_bills: %s", exc, exc_info=True)
            return {"error": "Произошла непредвиденная ошибка при анализе квитанции."}

    def chat_stream(self, comparison_id: str, message: str) -> Generator[str, None, None]:
        if self.use_mock:
            text = (
                f"По вашему обращению {comparison_id}: согласно Правилам предоставления "
                "коммунальных услуг (Постановление Правительства РФ № 354), при истечении "
                "межповерочного интервала прибора учета плата первые 3 месяца начисляется "
                "по среднемесячному потреблению (п. 59), а далее — по нормативу с применением "
                "повышающего коэффициента 1.5 (п. 60). Рекомендуется провести поверку счетчика "
                "в кратчайшие сроки и направить акт в управляющую компанию для перерасчета."
            )
            for word in text.split(" "):
                yield word + " "
        else:
            try:
                with httpx.stream(
                    "POST",
                    f"{self.api_base_url}/api/v1/chat/stream",
                    json={"comparison_id": comparison_id, "message": message},
                    headers=self._get_headers(),
                    timeout=10.0,
                ) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line:
                            continue
                        if not line.startswith("data:"):
                            continue
                        raw_payload = line[len("data:"):].strip()
                        if not raw_payload:
                            continue
                        try:
                            payload = json.loads(raw_payload)
                        except json.JSONDecodeError:
                            continue
                        if not isinstance(payload, dict):
                            continue
                        event_type = payload.get("type")
                        if event_type == "token":
                            yield payload.get("content", "")
                        elif event_type == "done":
                            break
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                logger.error("Chat streaming error: %s", exc, exc_info=True)
                yield "⚠️ Не удалось получить ответ от AI-юриста. Пожалуйста, повторите вопрос позже."

    def check_health(self) -> bool:
        try:
            response = httpx.get(
                f"{self.api_base_url}/health",
                headers=self._get_headers(),
                timeout=1.5,
            )
            return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def _mock_cases() -> List[Dict[str, Any]]:
        return [
            {
                "case_id": "case_02_coeff_15",
                "title": "Штрафной коэффициент 1.5 (ХВС)",
                "badge": "red",
                "description": "Просрочка поверки счетчика ХВС",
            },
            {
                "case_id": "case_01_heating_spike",
                "title": "Зимний скачок отопления (Морозы)",
                "badge": "yellow",
                "description": "Рост потребления Гкал без изменения тарифа",
            },
            {
                "case_id": "case_03_tariff_index",
                "title": "Индексация тарифов (+9%)",
                "badge": "yellow",
                "description": "Плановое повышение стоимости при стабильном объеме",
            },
        ]

    @staticmethod
    def _synthesize_ai_summary(data: Dict[str, Any]) -> str:
        summary = data.get("summary", {}) or {}
        anomalies = data.get("anomalies", []) or []
        breakdown = data.get("factor_breakdown", {}) or {}

        parts: List[str] = []

        if anomalies:
            anomaly = anomalies[0]
            title = anomaly.get("title") or "аномалия"
            impact = float(anomaly.get("impact_rub") or 0.0)
            hint = anomaly.get("hint")
            parts.append(f"Главная аномалия: {title}.")
            parts.append(f"Сумма переплаты: {impact:.2f} ₽.")
            if hint:
                if not hint.endswith((".", "!", "?")):
                    hint += "."
                parts.append(f"Рекомендация: {hint}")
        else:
            parts.append("Значимых аномалий не выявлено.")

        tariff_effect = float(breakdown.get("tariff_effect_rub") or 0.0)
        volume_effect = float(breakdown.get("volume_effect_rub") or 0.0)
        if tariff_effect == 0.0 and volume_effect == 0.0:
            parts.append("Изменение суммы не связано с изменением тарифов или объемов.")
        elif abs(tariff_effect) >= abs(volume_effect):
            parts.append(
                f"Доминирующий фактор изменения — тарифный эффект ({tariff_effect:+.2f} ₽)."
            )
        else:
            parts.append(
                f"Доминирующий фактор изменения — объемный эффект ({volume_effect:+.2f} ₽)."
            )

        qr_verified = summary.get("qr_verified")
        if qr_verified is True:
            parts.append("QR-код квитанции успешно верифицирован.")
        elif qr_verified is False:
            parts.append("QR-код квитанции не прошел верификацию.")

        return " ".join(parts)

    @staticmethod
    def _find_contract_file() -> Path | None:
        candidates = [
            Path.cwd() / "contracts" / "compare_response.json",
            Path.cwd().parent / "contracts" / "compare_response.json",
            Path(__file__).resolve().parents[1] / "contracts" / "compare_response.json",
        ]
        for path in candidates:
            if path.exists():
                return path
        return None

    @staticmethod
    def _coeff_15_mock() -> Dict[str, Any]:
        return {
            "comparison_id": "cmp_2026_10_11",
            "summary": {
                "prev_period": "2026-10",
                "curr_period": "2026-11",
                "prev_total": 5420.0,
                "curr_total": 6890.5,
                "delta_abs": 1470.5,
                "delta_pct": 27.13,
                "qr_verified": True,
                "status_level": "red",
            },
            "factor_breakdown": {
                "tariff_effect_rub": 180.0,
                "volume_effect_rub": 940.5,
                "recalculation_effect_rub": 350.0,
                "new_services_effect_rub": 0.0,
            },
            "anomalies": [
                {
                    "code": "APPLYING_COEFF_1_5",
                    "severity": "red",
                    "service_category": "cold_water",
                    "title": "Применен повышающий коэффициент 1.5",
                    "impact_rub": 245.18,
                    "hint": "Истек срок поверки счетчика ХВС или не передавались показания более 3 месяцев.",
                }
            ],
            "items": [
                {
                    "category": "cold_water",
                    "display_name": "Холодное водоснабжение (ХВС)",
                    "unit": "м3",
                    "prev_volume": 6.0,
                    "curr_volume": 8.2,
                    "prev_tariff": 54.0,
                    "curr_tariff": 59.8,
                    "prev_total": 324.0,
                    "curr_total": 735.54,
                    "delta_abs": 411.54,
                    "delta_pct": 127.02,
                    "tariff_delta_rub": 34.8,
                    "volume_delta_rub": 131.56,
                    "coeff_surcharge_rub": 245.18,
                    "status": "red",
                    "plain_explanation": "Расход вырос на 2.2 м³, тариф вырос на 5.80 ₽, плюс начислен штрафной коэффициент 1.5.",
                }
            ],
        }

    @staticmethod
    def _heating_spike_mock() -> Dict[str, Any]:
        return {
            "comparison_id": "cmp_heating_spike",
            "summary": {
                "prev_period": "2026-10",
                "curr_period": "2026-11",
                "prev_total": 5200.0,
                "curr_total": 6900.0,
                "delta_abs": 1700.0,
                "delta_pct": 32.69,
                "qr_verified": True,
                "status_level": "yellow",
            },
            "factor_breakdown": {
                "tariff_effect_rub": 0.0,
                "volume_effect_rub": 1700.0,
                "recalculation_effect_rub": 0.0,
                "new_services_effect_rub": 0.0,
            },
            "anomalies": [
                {
                    "code": "HEAT_SPIKE",
                    "severity": "yellow",
                    "service_category": "heating",
                    "title": "Расход тепла вырос на 38%",
                    "impact_rub": 1700.0,
                    "hint": "Аномальные холода в ноябре",
                }
            ],
            "items": [
                {
                    "category": "heating",
                    "display_name": "Отопление",
                    "unit": "Гкал",
                    "prev_volume": 1.3,
                    "curr_volume": 1.725,
                    "prev_tariff": 4000.0,
                    "curr_tariff": 4000.0,
                    "prev_total": 5200.0,
                    "curr_total": 6900.0,
                    "delta_abs": 1700.0,
                    "delta_pct": 32.69,
                    "tariff_delta_rub": 0.0,
                    "volume_delta_rub": 1700.0,
                    "coeff_surcharge_rub": 0.0,
                    "status": "yellow",
                    "plain_explanation": "Тариф не изменился, увеличение суммы вызвано исключительно объемом потребления.",
                }
            ],
        }

    @staticmethod
    def _tariff_index_mock() -> Dict[str, Any]:
        return {
            "comparison_id": "cmp_tariff_index",
            "summary": {
                "prev_period": "2026-10",
                "curr_period": "2026-11",
                "prev_total": 5000.0,
                "curr_total": 5450.0,
                "delta_abs": 450.0,
                "delta_pct": 9.0,
                "qr_verified": True,
                "status_level": "yellow",
            },
            "factor_breakdown": {
                "tariff_effect_rub": 450.0,
                "volume_effect_rub": 0.0,
                "recalculation_effect_rub": 0.0,
                "new_services_effect_rub": 0.0,
            },
            "anomalies": [],
            "items": [
                {
                    "category": "multiple",
                    "display_name": "Коммунальные услуги (Вода/Свет)",
                    "unit": "разные",
                    "prev_volume": 1.0,
                    "curr_volume": 1.0,
                    "prev_tariff": 5000.0,
                    "curr_tariff": 5450.0,
                    "prev_total": 5000.0,
                    "curr_total": 5450.0,
                    "delta_abs": 450.0,
                    "delta_pct": 9.0,
                    "tariff_delta_rub": 450.0,
                    "volume_delta_rub": 0.0,
                    "coeff_surcharge_rub": 0.0,
                    "status": "yellow",
                    "plain_explanation": "Плановое повышение тарифов на 9% при стабильном объеме потребления.",
                }
            ],
        }


@st.cache_resource
def get_api_client() -> ApiClient:
    """Create (and cache) the API client instance."""
    return ApiClient()
