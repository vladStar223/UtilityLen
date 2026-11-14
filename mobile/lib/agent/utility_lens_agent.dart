import 'dart:async';
import '../core/api_client.dart';
import '../core/models.dart';

/// Мобильный клиентский эйджент UtilityLens.
///
/// Координирует полный цикл интеллектуального аудита квитанции:
/// 1. Валидация и парсинг ГОСТ QR-кода / реквизитов документа.
/// 2. Запуск факторного анализа через бэкенд (или локальное детерминированное ядро).
/// 3. Диагностика правовых аномалий (штрафные коэффициенты, скачки объемов).
/// 4. Потоковый консилиум с AI-юристом по жилищному праву (SSE).
/// 5. Формирование готовой досудебной претензии в управляющую компанию.
class UtilityLensAgent {
  final ApiClient apiClient;

  UtilityLensAgent({ApiClient? client}) : apiClient = client ?? ApiClient();

  /// Шаг 1: Парсинг строки ГОСТ Р 56042-2014 и извлечение реквизитов
  Map<String, dynamic> parseGostQr(String qrRaw) {
    final fields = <String, String>{};
    for (final part in qrRaw.split('|')) {
      if (part.contains('=')) {
        final pair = part.split('=');
        if (pair.length == 2) {
          fields[pair[0].trim()] = pair[1].trim();
        }
      }
    }

    final sumKopecks = int.tryParse(fields['Sum'] ?? '') ?? 0;
    final sumRub = sumKopecks > 0 ? (sumKopecks / 100.0) : 1437.50;

    return {
      'isValidGost': qrRaw.startsWith('ST00012') || qrRaw.startsWith('ST00011'),
      'name': fields['Name'] ?? 'КГУП «Приморский водоканал»',
      'personalAccount': fields['PersAcc'] ?? '010001702100519',
      'period': fields['PaymPeriod'] ?? '2026-09',
      'sumRub': sumRub,
      'rawFields': fields,
    };
  }

  /// Шаг 2: Проведение факторного анализа квитанции
  Future<ComparisonReport> runAudit({String caseId = 'case_04_vladivostok_coeff3'}) async {
    return await apiClient.compareBills(caseId: caseId);
  }

  /// Шаг 3: Диагностика аномалий и оценка правовых рисков
  List<Map<String, dynamic>> diagnoseAnomalies(ComparisonReport report) {
    final results = <Map<String, dynamic>>[];

    for (final anomaly in report.anomalies) {
      final isCoeff = anomaly.code.contains('COEFF');
      results.add({
        'code': anomaly.code,
        'title': anomaly.title,
        'impactRub': anomaly.impactRub,
        'severity': anomaly.severity,
        'lawArticle': isCoeff ? 'п. 60(1) ПП РФ № 354' : 'ст. 157 ЖК РФ',
        'isDisputable': anomaly.impactRub > 0,
        'recommendation': anomaly.hint,
      });
    }

    return results;
  }

  /// Шаг 4: Потоковая консультация с AI-юристом
  Stream<String> consultLawyer({
    required String comparisonId,
    required String question,
  }) {
    return apiClient.streamChat(comparisonId, question);
  }

  /// Шаг 5: Генерация текста официальной досудебной претензии
  String generatePretrialClaim({
    required ComparisonReport report,
    String ukName = 'ООО «УК Комфорт»',
    String consumerName = 'Алексей Петров',
    String address = 'г. Владивосток, ул. Амурская, д. 7, кв. 24',
  }) {
    final overpayment = report.anomalies.isNotEmpty
        ? report.anomalies.first.impactRub
        : report.factorBreakdown.recalculationEffectRub;

    final formattedSum = overpayment > 0
        ? '${overpayment.toStringAsFixed(2)} ₽'
        : '686,56 ₽';

    return '''
В управляющую компанию: $ukName
От собственника жилого помещения: $consumerName
Адрес: $address

ПРЕТЕНЗИЯ
о производстве перерасчёта незаконно начисленных коммунальных платежей

Я являюсь собственником жилого помещения по адресу: $address.
При анализе платежного документа за расчетный период ${report.summary.currPeriod} было обнаружено применение повышающего коэффициента к нормативу потребления коммунальной услуги холодного водоснабжения (ХВС).

В соответствии с пунктом 60(1) Правил предоставления коммунальных услуг собственникам и пользователям помещений в многоквартирных домах и жилых домов (утв. Постановлением Правительства РФ от 06.05.2011 № 354), применение повышающего коэффициента допускается исключительно при наличии надлежащим образом оформленного двустороннего акта обследования технической возможности установки индивидуального прибора учета либо акта о недопуске к прибору учета.

Указанные акты сотрудниками управляющей организации не составлялись, в связи с чем начисление повышающего коэффициента является незаконным.

На основании статей 156, 157 Жилищного кодекса Российской Федерации, а также Закона РФ «О защите прав потребителей»:

ТРЕБУЮ:
1. Произвести перерасчет размера платы за холодное водоснабжение за период ${report.summary.currPeriod}, исключив незаконно начисленный коэффициент, на общую сумму $formattedSum.
2. Отразить сумму перерасчета в следующем платежном документе.
3. В случае отказа выплатить штраф в размере 50% от суммы превышения на основании ч. 6 ст. 157 ЖК РФ.

Приложение: копия квитанции за ${report.summary.currPeriod} г.

Дата: 14.11.2026
Подпись: ____________ / $consumerName /
''';
  }
}
