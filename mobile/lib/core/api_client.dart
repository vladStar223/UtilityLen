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

  /// Запуск факторного анализа по кейсу.
  /// Реальные данные берутся только с бэкенда. При ошибке бросаем исключение —
  /// никаких моков в клиенте.
  Future<ComparisonReport> compareBills({String caseId = "case_02_coeff_15"}) async {
    final response = await http
        .post(
          Uri.parse(ApiConfig.compareEndpoint),
          headers: {"Content-Type": "application/json"},
          body: json.encode({"case_id": caseId}),
        )
        .timeout(const Duration(seconds: 15));

    if (response.statusCode == 200) {
      final data = json.decode(utf8.decode(response.bodyBytes));
      final report = ComparisonReport.fromJson(data);
      _lastComparisonId = report.comparisonId;
      return report;
    }

    throw Exception(
      'Сервер вернул ошибку (${response.statusCode}) при сравнении кейса "$caseId"',
    );
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
}
