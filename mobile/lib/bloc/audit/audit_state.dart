import 'package:equatable/equatable.dart';
import '../../core/models.dart';

enum AuditStatus { initial, loading, loaded, error }

class AuditState extends Equatable {
  final AuditStatus status;
  final ComparisonReport? report;
  final String selectedPeriod;
  final String selectedCategory;
  final List<ReceiptHistoryItem> history;
  final List<MonthlyTrendItem> monthlyTrends;
  final List<AlertNotificationItem> alerts;
  final String? errorMessage;

  const AuditState({
    this.status = AuditStatus.initial,
    this.report,
    this.selectedPeriod = 'Ноябрь 2026',
    this.selectedCategory = 'all',
    this.history = const [],
    this.monthlyTrends = const [],
    this.alerts = const [],
    this.errorMessage,
  });

  AuditState copyWith({
    AuditStatus? status,
    ComparisonReport? report,
    String? selectedPeriod,
    String? selectedCategory,
    List<ReceiptHistoryItem>? history,
    List<MonthlyTrendItem>? monthlyTrends,
    List<AlertNotificationItem>? alerts,
    String? errorMessage,
  }) {
    return AuditState(
      status: status ?? this.status,
      report: report ?? this.report,
      selectedPeriod: selectedPeriod ?? this.selectedPeriod,
      selectedCategory: selectedCategory ?? this.selectedCategory,
      history: history ?? this.history,
      monthlyTrends: monthlyTrends ?? this.monthlyTrends,
      alerts: alerts ?? this.alerts,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }

  @override
  List<Object?> get props => [
        status,
        report,
        selectedPeriod,
        selectedCategory,
        history,
        monthlyTrends,
        alerts,
        errorMessage,
      ];
}
