import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_config.dart';
import 'models.dart';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;
  ApiClient._internal();

  /// Получение списка эталонных кейсов
  Future<List<CaseItem>> getCases() async {
    try {
      final response = await http
          .get(Uri.parse(ApiConfig.casesEndpoint))
          .timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        final list = data['cases'] as List<dynamic>? ?? [];
        return list.map((e) => CaseItem.fromJson(e)).toList();
      }
    } catch (_) {
      // Fallback на локальный список, если сервер временно недоступен
    }

    return [
      CaseItem(
        caseId: "case_04_vladivostok_coeff3",
        title: "Владивосток: Коэффициент 3.0 (ул. Амурская)",
        description: "Реальная квитанция Приморского водоканала с 3-кратным повышающим штрафом",
        periods: ["2026-08", "2026-09"],
      ),
      CaseItem(
        caseId: "case_02_coeff_15",
        title: "Штрафной коэффициент 1.5 (ХВС)",
        description: "Просрочка поверки счетчика холодной воды",
        periods: ["2026-10", "2026-11"],
      ),
      CaseItem(
        caseId: "case_01_heating_spike",
        title: "Зимний скачок отопления (Морозы)",
        description: "Резкий рост потребления тепла в ноябре",
        periods: ["2026-10", "2026-11"],
      ),
      CaseItem(
        caseId: "case_03_tariff_index",
        title: "Индексация тарифов (+9%)",
        description: "Плановое повышение стоимости ЖКУ с 1 июля",
        periods: ["2026-06", "2026-07"],
      ),
    ];
  }

  /// Запуск факторного анализа по кейсу
  Future<ComparisonReport> compareBills({String caseId = "case_02_coeff_15"}) async {
    // Если выбран реальный кейс с коэффициентом 3.0 с ул. Амурской
    if (caseId == "case_04_vladivostok_coeff3") {
      return _buildVladivostokRealCase();
    }

    try {
      final response = await http
          .post(
            Uri.parse(ApiConfig.compareEndpoint),
            headers: {"Content-Type": "application/json"},
            body: json.encode({"case_id": caseId}),
          )
          .timeout(const Duration(seconds: 8));

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        return ComparisonReport.fromJson(data);
      }
    } catch (_) {
      // Offline fallback
    }

    return _buildMockReport(caseId);
  }

  /// Потоковый диалог с AI-юристом (SSE)
  Stream<String> streamChat(String comparisonId, String message) async* {
    try {
      final request = http.Request("POST", Uri.parse(ApiConfig.chatStreamEndpoint));
      request.headers["Content-Type"] = "application/json";
      request.body = json.encode({
        "comparison_id": comparisonId,
        "message": message,
      });

      final streamedResponse = await request.send().timeout(const Duration(seconds: 10));

      if (streamedResponse.statusCode == 200) {
        await for (final chunk in streamedResponse.stream.transform(utf8.decoder)) {
          for (final line in chunk.split("\n")) {
            if (line.startsWith("data: ")) {
              final payloadStr = line.substring(6).trim();
              if (payloadStr.isNotEmpty) {
                try {
                  final data = json.decode(payloadStr);
                  if (data['type'] == 'token') {
                    yield data['content'] ?? '';
                  }
                } catch (_) {}
              }
            }
          }
        }
        return;
      }
    } catch (_) {
      // Офлайн-ответ AI-юриста
    }

    // Детерминированный юридический ответ при отсутствии связи
    const offlineLawAnswer =
        "По результатам факторного анализа выявлено: начисление произведено с применением "
        "повышающего коэффициента в соответствии с п. 60(1) Постановления Правительства РФ № 354. "
        "Однако применение данного коэффициента незаконно, если управляющая компания не составила "
        "акт о недопуске к прибору учета. Сформирована готовая досудебная претензия с требованием "
        "перерасчета суммы переплаты по ст. 157 ЖК РФ.";

    for (final word in offlineLawAnswer.split(" ")) {
      await Future.delayed(const Duration(milliseconds: 30));
      yield "$word ";
    }
  }

  /// Данные реальной квитанции из Владивостока (ул. Амурская, д. 7) с коэффициентом 3.0
  ComparisonReport _buildVladivostokRealCase() {
    return ComparisonReport(
      comparisonId: "cmp-vladivostok-amurskaya-coeff3",
      summary: SummaryReport(
        prevPeriod: "2026-08",
        currPeriod: "2026-09",
        prevTotal: 750.94,
        currTotal: 1437.50,
        deltaAbs: 686.56,
        deltaPct: 91.43,
        qrVerified: true,
        statusLevel: "red",
      ),
      factorBreakdown: FactorBreakdown(
        tariffEffectRub: 0.0,
        volumeEffectRub: 0.0,
        recalculationEffectRub: 686.56,
        newServicesEffectRub: 0.0,
      ),
      anomalies: [
        AnomalyItem(
          code: "APPLYING_COEFF_3_0",
          severity: "red",
          serviceCategory: "cold_water",
          title: "Применен 3-кратный штрафной коэффициент на ХВС",
          impactRub: 686.56,
          hint: "КГУП «Приморский водоканал» начислил ХВС с коэффициентом 3.0 (1 029.84 ₽ вместо 343.28 ₽). Требуется досудебная претензия по ст. 157 ЖК РФ.",
        ),
      ],
      items: [
        ServiceItem(
          category: "cold_water",
          displayName: "Холодное водоснабжение (ХВС)",
          unit: "м3",
          prevVolume: 7.324,
          currVolume: 7.324,
          prevTariff: 46.87,
          currTariff: 46.87,
          prevTotal: 343.28,
          currTotal: 1029.84,
          deltaAbs: 686.56,
          deltaPct: 200.0,
          tariffDeltaRub: 0.0,
          volumeDeltaRub: 0.0,
          coeffSurchargeRub: 686.56,
          status: "red",
          plainExplanation: "Норматив 7.324 м³ при тарифе 46.87 ₽/м³ умножен на повышающий коэффициент 3.0. Переплата: 686.56 ₽.",
        ),
        ServiceItem(
          category: "drainage",
          displayName: "Водоотведение (ХВС + ГВС)",
          unit: "м3",
          prevVolume: 11.400,
          currVolume: 11.400,
          prevTariff: 35.76,
          currTariff: 35.76,
          prevTotal: 407.66,
          currTotal: 407.66,
          deltaAbs: 0.0,
          deltaPct: 0.0,
          tariffDeltaRub: 0.0,
          volumeDeltaRub: 0.0,
          coeffSurchargeRub: 0.0,
          status: "green",
          plainExplanation: "Объем 11.4 м³ рассчитан строго по нормативу без повышающих коэффициентов.",
        ),
      ],
    );
  }

  ComparisonReport _buildMockReport(String caseId) {
    return ComparisonReport(
      comparisonId: "cmp-mock-coeff15",
      summary: SummaryReport(
        prevPeriod: "2026-10",
        currPeriod: "2026-11",
        prevTotal: 5420.0,
        currTotal: 6890.5,
        deltaAbs: 1470.5,
        deltaPct: 27.13,
        qrVerified: true,
        statusLevel: "red",
      ),
      factorBreakdown: FactorBreakdown(
        tariffEffectRub: 144.8,
        volumeEffectRub: 856.56,
        recalculationEffectRub: 469.14,
        newServicesEffectRub: 0.0,
      ),
      anomalies: [
        AnomalyItem(
          code: "APPLYING_COEFF_1_5",
          severity: "red",
          serviceCategory: "cold_water",
          title: "Применен повышающий коэффициент 1.5",
          impactRub: 245.18,
          hint: "Истек срок поверки счетчика ХВС",
        ),
      ],
      items: [
        ServiceItem(
          category: "cold_water",
          displayName: "Холодное водоснабжение (ХВС)",
          unit: "м3",
          prevVolume: 6.0,
          currVolume: 8.2,
          prevTariff: 54.0,
          currTariff: 59.8,
          prevTotal: 324.0,
          currTotal: 735.54,
          deltaAbs: 411.54,
          deltaPct: 127.02,
          tariffDeltaRub: 34.8,
          volumeDeltaRub: 131.56,
          coeffSurchargeRub: 245.18,
          status: "red",
          plainExplanation: "Начислен коэффициент 1.5 за отсутствие поверки счетчика.",
        ),
      ],
    );
  }
}
