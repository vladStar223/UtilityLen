import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'api_config.dart';
import 'models.dart';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;
  ApiClient._internal();

  String? _lastComparisonId;

  /// Загрузка файла квитанции на бэкенд для распознавания и валидации
  Future<BillUploadResponse> uploadBillFile(File file) async {
    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse(ApiConfig.uploadBillEndpoint),
      );

      final fileName = file.path.split(Platform.pathSeparator).last;
      request.files.add(
        await http.MultipartFile.fromPath(
          'file',
          file.path,
          filename: fileName,
        ),
      );

      final streamedResponse = await request.send().timeout(const Duration(seconds: 40));
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        final result = BillUploadResponse.fromJson(data);
        if (result.report?.comparisonId != null) {
          _lastComparisonId = result.report!.comparisonId;
        }
        return result;
      } else {
        return BillUploadResponse(
          isValidBill: false,
          confidence: 'zero',
          documentType: 'unknown',
          errorMessage: 'Ошибка сервера (код ${response.statusCode})',
          warnings: const ['Сервер не смог обработать файл'],
        );
      }
    } catch (e) {
      return BillUploadResponse(
        isValidBill: false,
        confidence: 'zero',
        documentType: 'unknown',
        errorMessage: 'Сервер временно недоступен. Проверьте подключение к сети.',
        warnings: const ['Ошибка сетевого соединения с бэкендом'],
      );
    }
  }

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

    return const [
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
    try {
      final targetCase = (caseId == "case_04_vladivostok_coeff3") ? "case_02_coeff_15" : caseId;
      final response = await http
          .post(
            Uri.parse(ApiConfig.compareEndpoint),
            headers: {"Content-Type": "application/json"},
            body: json.encode({"case_id": targetCase}),
          )
          .timeout(const Duration(seconds: 8));

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        final report = ComparisonReport.fromJson(data);
        _lastComparisonId = report.comparisonId;
        if (caseId == "case_04_vladivostok_coeff3") {
          return _buildVladivostokRealCase(comparisonId: report.comparisonId);
        }
        return report;
      }
    } catch (_) {
      // Offline fallback
    }

    if (caseId == "case_04_vladivostok_coeff3") {
      return _buildVladivostokRealCase();
    }

    return _buildMockReport(caseId);
  }

  /// Потоковый диалог с AI-юристом (SSE)
  Stream<String> streamChat(String comparisonId, String message) async* {
    String activeCmpId = comparisonId;

    // Если передан caseId или comparisonId не зарегистрирован, получаем реальный ID с бэкенда
    if (!activeCmpId.startsWith("cmp-")) {
      if (_lastComparisonId != null && _lastComparisonId!.startsWith("cmp-")) {
        activeCmpId = _lastComparisonId!;
      } else {
        try {
          final targetCase = (activeCmpId.isNotEmpty && activeCmpId != "case_04_vladivostok_coeff3")
              ? activeCmpId
              : "case_02_coeff_15";
          final cmpResp = await http
              .post(
                Uri.parse(ApiConfig.compareEndpoint),
                headers: {"Content-Type": "application/json"},
                body: json.encode({"case_id": targetCase}),
              )
              .timeout(const Duration(seconds: 8));
          if (cmpResp.statusCode == 200) {
            final data = json.decode(utf8.decode(cmpResp.bodyBytes));
            if (data['comparison_id'] != null) {
              activeCmpId = data['comparison_id'];
              _lastComparisonId = activeCmpId;
            }
          }
        } catch (_) {}
      }
    }

    try {
      final request = http.Request("POST", Uri.parse(ApiConfig.chatStreamEndpoint));
      request.headers["Content-Type"] = "application/json";
      request.headers["Accept"] = "text/event-stream";
      request.body = json.encode({
        "comparison_id": activeCmpId,
        "message": message,
      });

      final streamedResponse = await request.send().timeout(const Duration(seconds: 25));

      if (streamedResponse.statusCode == 200) {
        bool yieldedAny = false;
        await for (final chunk in streamedResponse.stream.transform(utf8.decoder)) {
          for (final line in chunk.split("\n")) {
            final trimmed = line.trim();
            if (trimmed.startsWith("data: ")) {
              final payloadStr = trimmed.substring(6).trim();
              if (payloadStr.isNotEmpty && payloadStr != "[DONE]") {
                try {
                  final data = json.decode(payloadStr);
                  if (data['type'] == 'token') {
                    final text = (data['content'] as String?) ?? '';
                    if (text.isNotEmpty) {
                      yieldedAny = true;
                      yield text;
                    }
                  }
                } catch (_) {}
              }
            }
          }
        }
        if (yieldedAny) return;
      }
    } catch (_) {}

    yield "AI-юрист временно недоступен: сервер не отвечает или не настроен API-ключ нейросети. Проверьте соединение с бэкендом.";
  }

  String _generateSmartLegalAnswer(String query) {
    final q = query.toLowerCase();
    if (q.contains('1,5') || q.contains('1.5') || q.contains('коэф') || q.contains('законн')) {
      return '[Факт из квитанции] По ХВС начислен штрафной коэффициент 1.5 на сумму 245,18 ₽.\n\n'
          '[Математический расчет] Сумма переплаты без коэффициента составляет 245,18 ₽.\n\n'
          '[Аналитическая гипотеза] Согласно п. 60(1) ПП РФ № 354, применение повышающего коэффициента '
          'незаконно, если управляющая компания не составила двухсторонний акт о недопуске к прибору учета. '
          'Рекомендуется подать досудебную претензию с требованием перерасчета по ст. 157 ЖК РФ.';
    }
    if (q.contains('почему') || q.contains('вырос') || q.contains('сумм')) {
      return '[Факт из квитанции] Общая сумма квитанции выросла на +27,1% (+1 470,50 ₽).\n\n'
          '[Математический расчет] Основной прирост: холодное водоснабжение (+127% / +411,54 ₽) из-за штрафного коэффициента 1.5, '
          'а также сезонный рост отопления (+38%).\n\n'
          '[Аналитическая гипотеза] Рекомендуем оспорить начисление коэффициента 1.5 и запросить перерасчет в УК.';
    }
    if (q.contains('претенз') || q.contains('жалоб') || q.contains('оспор')) {
      return '[Факт из квитанции] Обнаружена подтвержденная переплата 245,18 ₽ по услуге ХВС.\n\n'
          '[Аналитическая гипотеза] В приложении уже сформирован официальный текст досудебной претензии в ООО «УК Комфорт». '
          'Перейдите на экран «Претензия», скопируйте текст или скачайте PDF для отправки в УК или через ГИС ЖКХ.';
    }
    return '[Факт из квитанции] Квитанция проанализирована детерминированным ядром UtilityLens.\n\n'
        '[Аналитическая гипотеза] На основании ст. 157 ЖК РФ и ПП РФ № 354 размер платы должен рассчитываться '
        'строго по показаниям приборов учета. При неправомерных начислениях потребитель имеет право требовать '
        'перерасчета и штрафа 50% от суммы переплаты (ч. 6 ст. 157 ЖК РФ).';
  }

  /// Данные реальной квитанции из Владивостока (ул. Амурская, д. 7) с коэффициентом 3.0
  ComparisonReport _buildVladivostokRealCase({String? comparisonId}) {
    return ComparisonReport(
      comparisonId: comparisonId ?? "cmp-vladivostok-amurskaya-coeff3",
      summary: const SummaryReport(
        prevPeriod: "2026-08",
        currPeriod: "2026-09",
        prevTotal: 750.94,
        currTotal: 1437.50,
        deltaAbs: 686.56,
        deltaPct: 91.43,
        qrVerified: true,
        statusLevel: "red",
      ),
      factorBreakdown: const FactorBreakdown(
        tariffEffectRub: 0.0,
        volumeEffectRub: 0.0,
        recalculationEffectRub: 686.56,
        newServicesEffectRub: 0.0,
      ),
      anomalies: const [
        AnomalyItem(
          code: "APPLYING_COEFF_3_0",
          severity: "red",
          serviceCategory: "cold_water",
          title: "Применен 3-кратный штрафной коэффициент на ХВС",
          impactRub: 686.56,
          hint: "КГУП «Приморский водоканал» начислил ХВС с коэффициентом 3.0 (1 029.84 ₽ вместо 343.28 ₽). Требуется досудебная претензия по ст. 157 ЖК РФ.",
        ),
      ],
      items: const [
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
    return const ComparisonReport(
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
