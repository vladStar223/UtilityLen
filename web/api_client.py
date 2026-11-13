"""API Client for interacting with the backend service."""
import os
import json
from typing import Generator, Dict, Any, List
from pathlib import Path

import httpx
import streamlit as st

USE_MOCK_API = os.getenv("USE_MOCK_API", "true").lower() in ("true", "1", "yes")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class ApiClient:
    def __init__(self):
        self.use_mock = USE_MOCK_API
        self.api_base_url = API_BASE_URL

    def get_cases(self) -> List[Dict[str, Any]]:
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

    def compare_bills(self, case_id: str = "case_02_coeff_15") -> Dict[str, Any]:
        if self.use_mock:
            if case_id == "case_02_coeff_15":
                contract_path = self._find_contract_file()
                if contract_path is not None:
                    try:
                        with open(contract_path, "r", encoding="utf-8") as f:
                            return json.loads(f.read())
                    except (OSError, json.JSONDecodeError):
                        pass
                return self._heating_spike_mock()
            if case_id == "case_01_heating_spike":
                return self._heating_spike_mock()
            if case_id == "case_03_tariff_index":
                return self._tariff_index_mock()
            raise ValueError(f"Unknown mock case_id: {case_id}")

        response = httpx.post(
            f"{self.api_base_url}/api/v1/compare",
            json={"case_id": case_id},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

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
            with httpx.stream(
                "POST",
                f"{self.api_base_url}/api/v1/chat/stream",
                json={"comparison_id": comparison_id, "message": message},
                timeout=10.0,
            ) as response:
                response.raise_for_status()
                for chunk in response.iter_bytes():
                    if chunk:
                        yield chunk.decode("utf-8", errors="replace")

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
