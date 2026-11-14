import 'package:equatable/equatable.dart';

/// Модели данных для мобильного клиента UtilityLens (Light Fintech & BLoC)

class CaseItem extends Equatable {
  final String caseId;
  final String title;
  final String description;
  final List<String> periods;

  const CaseItem({
    required this.caseId,
    required this.title,
    required this.description,
    required this.periods,
  });

  factory CaseItem.fromJson(Map<String, dynamic> json) {
    return CaseItem(
      caseId: json['case_id'] ?? '',
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      periods: List<String>.from(json['periods'] ?? []),
    );
  }

  @override
  List<Object?> get props => [caseId, title, description, periods];
}

class SummaryReport extends Equatable {
  final String prevPeriod;
  final String currPeriod;
  final double prevTotal;
  final double currTotal;
  final double deltaAbs;
  final double deltaPct;
  final bool qrVerified;
  final String statusLevel; // red, yellow, green

  const SummaryReport({
    required this.prevPeriod,
    required this.currPeriod,
    required this.prevTotal,
    required this.currTotal,
    required this.deltaAbs,
    required this.deltaPct,
    required this.qrVerified,
    required this.statusLevel,
  });

  factory SummaryReport.fromJson(Map<String, dynamic> json) {
    return SummaryReport(
      prevPeriod: json['prev_period'] ?? '',
      currPeriod: json['curr_period'] ?? '',
      prevTotal: (json['prev_total'] as num?)?.toDouble() ?? 0.0,
      currTotal: (json['curr_total'] as num?)?.toDouble() ?? 0.0,
      deltaAbs: (json['delta_abs'] as num?)?.toDouble() ?? 0.0,
      deltaPct: (json['delta_pct'] as num?)?.toDouble() ?? 0.0,
      qrVerified: json['qr_verified'] ?? false,
      statusLevel: json['status_level'] ?? 'green',
    );
  }

  @override
  List<Object?> get props => [
        prevPeriod,
        currPeriod,
        prevTotal,
        currTotal,
        deltaAbs,
        deltaPct,
        qrVerified,
        statusLevel,
      ];
}

class FactorBreakdown extends Equatable {
  final double tariffEffectRub;
  final double volumeEffectRub;
  final double recalculationEffectRub;
  final double newServicesEffectRub;

  const FactorBreakdown({
    required this.tariffEffectRub,
    required this.volumeEffectRub,
    required this.recalculationEffectRub,
    required this.newServicesEffectRub,
  });

  factory FactorBreakdown.fromJson(Map<String, dynamic> json) {
    return FactorBreakdown(
      tariffEffectRub: (json['tariff_effect_rub'] as num?)?.toDouble() ?? 0.0,
      volumeEffectRub: (json['volume_effect_rub'] as num?)?.toDouble() ?? 0.0,
      recalculationEffectRub: (json['recalculation_effect_rub'] as num?)?.toDouble() ?? 0.0,
      newServicesEffectRub: (json['new_services_effect_rub'] as num?)?.toDouble() ?? 0.0,
    );
  }

  @override
  List<Object?> get props => [
        tariffEffectRub,
        volumeEffectRub,
        recalculationEffectRub,
        newServicesEffectRub,
      ];
}

class AnomalyItem extends Equatable {
  final String code;
  final String severity; // red, yellow, info
  final String serviceCategory;
  final String title;
  final double impactRub;
  final String hint;

  const AnomalyItem({
    required this.code,
    required this.severity,
    required this.serviceCategory,
    required this.title,
    required this.impactRub,
    required this.hint,
  });

  factory AnomalyItem.fromJson(Map<String, dynamic> json) {
    return AnomalyItem(
      code: json['code'] ?? '',
      severity: json['severity'] ?? 'yellow',
      serviceCategory: json['service_category'] ?? '',
      title: json['title'] ?? '',
      impactRub: (json['impact_rub'] as num?)?.toDouble() ?? 0.0,
      hint: json['hint'] ?? '',
    );
  }

  @override
  List<Object?> get props => [code, severity, serviceCategory, title, impactRub, hint];
}

class ServiceItem extends Equatable {
  final String category;
  final String displayName;
  final String unit;
  final double prevVolume;
  final double currVolume;
  final double prevTariff;
  final double currTariff;
  final double prevTotal;
  final double currTotal;
  final double deltaAbs;
  final double deltaPct;
  final double tariffDeltaRub;
  final double volumeDeltaRub;
  final double coeffSurchargeRub;
  final String status;
  final String plainExplanation;

  const ServiceItem({
    required this.category,
    required this.displayName,
    required this.unit,
    required this.prevVolume,
    required this.currVolume,
    required this.prevTariff,
    required this.currTariff,
    required this.prevTotal,
    required this.currTotal,
    required this.deltaAbs,
    required this.deltaPct,
    required this.tariffDeltaRub,
    required this.volumeDeltaRub,
    required this.coeffSurchargeRub,
    required this.status,
    required this.plainExplanation,
  });

  factory ServiceItem.fromJson(Map<String, dynamic> json) {
    return ServiceItem(
      category: json['category'] ?? '',
      displayName: json['display_name'] ?? '',
      unit: json['unit'] ?? '',
      prevVolume: (json['prev_volume'] as num?)?.toDouble() ?? 0.0,
      currVolume: (json['curr_volume'] as num?)?.toDouble() ?? 0.0,
      prevTariff: (json['prev_tariff'] as num?)?.toDouble() ?? 0.0,
      currTariff: (json['curr_tariff'] as num?)?.toDouble() ?? 0.0,
      prevTotal: (json['prev_total'] as num?)?.toDouble() ?? 0.0,
      currTotal: (json['curr_total'] as num?)?.toDouble() ?? 0.0,
      deltaAbs: (json['delta_abs'] as num?)?.toDouble() ?? 0.0,
      deltaPct: (json['delta_pct'] as num?)?.toDouble() ?? 0.0,
      tariffDeltaRub: (json['tariff_delta_rub'] as num?)?.toDouble() ?? 0.0,
      volumeDeltaRub: (json['volume_delta_rub'] as num?)?.toDouble() ?? 0.0,
      coeffSurchargeRub: (json['coeff_surcharge_rub'] as num?)?.toDouble() ?? 0.0,
      status: json['status'] ?? 'green',
      plainExplanation: json['plain_explanation'] ?? '',
    );
  }

  @override
  List<Object?> get props => [
        category,
        displayName,
        unit,
        prevVolume,
        currVolume,
        prevTariff,
        currTariff,
        prevTotal,
        currTotal,
        deltaAbs,
        deltaPct,
        tariffDeltaRub,
        volumeDeltaRub,
        coeffSurchargeRub,
        status,
        plainExplanation,
      ];
}

class ComparisonReport extends Equatable {
  final String comparisonId;
  final SummaryReport summary;
  final FactorBreakdown factorBreakdown;
  final List<AnomalyItem> anomalies;
  final List<ServiceItem> items;

  const ComparisonReport({
    required this.comparisonId,
    required this.summary,
    required this.factorBreakdown,
    required this.anomalies,
    required this.items,
  });

  factory ComparisonReport.fromJson(Map<String, dynamic> json) {
    return ComparisonReport(
      comparisonId: json['comparison_id'] ?? '',
      summary: SummaryReport.fromJson(json['summary'] ?? {}),
      factorBreakdown: FactorBreakdown.fromJson(json['factor_breakdown'] ?? {}),
      anomalies: (json['anomalies'] as List<dynamic>?)
              ?.map((e) => AnomalyItem.fromJson(e))
              .toList() ??
          [],
      items: (json['items'] as List<dynamic>?)
              ?.map((e) => ServiceItem.fromJson(e))
              .toList() ??
          [],
    );
  }

  @override
  List<Object?> get props => [comparisonId, summary, factorBreakdown, anomalies, items];
}

class ChatMessage extends Equatable {
  final String text;
  final bool isUser;
  final DateTime timestamp;

  ChatMessage({
    required this.text,
    required this.isUser,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  @override
  List<Object?> get props => [text, isUser, timestamp];
}

/// Модель объекта недвижимости (Раздел «Мои объекты» в профиле)
class PropertyItem extends Equatable {
  final String id;
  final String title; // "Квартира №24"
  final String address; // "г. Владивосток, ул. Амурская, д. 7"
  final String accountNumber; // Лицевой счет
  final bool isDefault;

  const PropertyItem({
    required this.id,
    required this.title,
    required this.address,
    required this.accountNumber,
    this.isDefault = false,
  });

  @override
  List<Object?> get props => [id, title, address, accountNumber, isDefault];
}

/// Модель квитанции в истории
class ReceiptHistoryItem extends Equatable {
  final String id;
  final String period; // "Октябрь 2026"
  final double totalAmount; // 5420.00
  final String providerName; // "Примводоканал + ДЭК"
  final bool hasOverpayment;
  final double overpaymentAmount;

  const ReceiptHistoryItem({
    required this.id,
    required this.period,
    required this.totalAmount,
    required this.providerName,
    this.hasOverpayment = false,
    this.overpaymentAmount = 0.0,
  });

  @override
  List<Object?> get props => [id, period, totalAmount, providerName, hasOverpayment, overpaymentAmount];
}

/// Модель уведомления / алертов
class AlertNotificationItem extends Equatable {
  final String id;
  final String title;
  final String description;
  final String severity; // critical, warning, success, info
  final double? amount;

  const AlertNotificationItem({
    required this.id,
    required this.title,
    required this.description,
    required this.severity,
    this.amount,
  });

  @override
  List<Object?> get props => [id, title, description, severity, amount];
}

/// Модель графика динамики в аналитике
class MonthlyTrendItem extends Equatable {
  final String monthLabel; // "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя"
  final double amount; // 4200, 4800, 5100, 5200, 5420, 6890.5

  const MonthlyTrendItem({
    required this.monthLabel,
    required this.amount,
  });

  @override
  List<Object?> get props => [monthLabel, amount];
}
