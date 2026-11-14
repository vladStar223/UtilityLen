import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/api_client.dart';
import '../../core/models.dart';
import 'audit_event.dart';
import 'audit_state.dart';

class AuditBloc extends Bloc<AuditEvent, AuditState> {
  final ApiClient apiClient;

  AuditBloc({required this.apiClient}) : super(const AuditState()) {
    on<LoadAuditDataEvent>(_onLoadAuditData);
    on<SetAuditReportEvent>(_onSetAuditReport);
    on<ChangePeriodEvent>(_onChangePeriod);
    on<FilterCategoryEvent>(_onFilterCategory);
    on<CaptureReceiptPhotoEvent>(_onCaptureReceiptPhoto);
    on<ScanQrEvent>(_onScanQr);
  }

  void _onSetAuditReport(
    SetAuditReportEvent event,
    Emitter<AuditState> emit,
  ) {
    emit(_buildLoadedState(event.report));
  }

  AuditState _buildLoadedState(ComparisonReport report) {
    final history = [
      if (report.summary.prevTotal > 0)
        ReceiptHistoryItem(
          id: 'rec_prev',
          period: report.summary.prevPeriod.isNotEmpty ? report.summary.prevPeriod : 'Прошлый месяц',
          totalAmount: report.summary.prevTotal,
          providerName: 'Примводоканал · ДЭК',
          hasOverpayment: false,
        ),
      const ReceiptHistoryItem(
        id: 'rec_2026_10',
        period: 'Октябрь 2026',
        totalAmount: 5420.00,
        providerName: 'Примводоканал · ДЭК',
        hasOverpayment: false,
      ),
      const ReceiptHistoryItem(
        id: 'rec_2026_09',
        period: 'Сентябрь 2026',
        totalAmount: 5200.00,
        providerName: 'Примводоканал · ДЭК',
        hasOverpayment: true,
        overpaymentAmount: 686.56,
      ),
      const ReceiptHistoryItem(
        id: 'rec_2026_08',
        period: 'Август 2026',
        totalAmount: 5100.00,
        providerName: 'Примводоканал',
        hasOverpayment: false,
      ),
    ];

    const trends = [
      MonthlyTrendItem(monthLabel: 'Июн', amount: 4200),
      MonthlyTrendItem(monthLabel: 'Июл', amount: 4800),
      MonthlyTrendItem(monthLabel: 'Авг', amount: 5100),
      MonthlyTrendItem(monthLabel: 'Сен', amount: 5200),
      MonthlyTrendItem(monthLabel: 'Окт', amount: 5420),
      MonthlyTrendItem(monthLabel: 'Ноя', amount: 6890.5),
    ];

    final hasAnomalies = report.anomalies.isNotEmpty;
    final topAnomaly = hasAnomalies ? report.anomalies.first : null;
    final overpaymentAmount = topAnomaly?.impactRub ?? 0.0;
    final overpaymentDesc = topAnomaly?.hint ?? 'Все начисления соответствуют нормативам.';
    final overpaymentTitle = topAnomaly?.title ?? 'Отклонений не найдено';

    final alerts = <AlertNotificationItem>[
      if (hasAnomalies)
        AlertNotificationItem(
          id: 'alert_critical_1',
          title: overpaymentTitle,
          description: overpaymentDesc,
          severity: 'critical',
          amount: overpaymentAmount,
        )
      else
        const AlertNotificationItem(
          id: 'alert_norm_ok',
          title: 'Начисления в норме',
          description: 'По всем услугам отклонений от нормативов не найдено',
          severity: 'success',
        ),
      const AlertNotificationItem(
        id: 'alert_meter_warning',
        title: 'Срок поверки счётчика',
        description: 'Поверка истекает через 2 месяца',
        severity: 'warning',
      ),
      const AlertNotificationItem(
        id: 'alert_protection',
        title: 'Ваша защита активна',
        description: 'Мы автоматически проверяем квитанции на соответствие нормативам Владивостока и ПП РФ № 354',
        severity: 'info',
      ),
    ];

    return state.copyWith(
      status: AuditStatus.loaded,
      report: report,
      selectedPeriod: report.summary.currPeriod.isNotEmpty ? report.summary.currPeriod : state.selectedPeriod,
      history: history,
      monthlyTrends: trends,
      alerts: alerts,
    );
  }

  Future<void> _onLoadAuditData(
    LoadAuditDataEvent event,
    Emitter<AuditState> emit,
  ) async {
    emit(state.copyWith(status: AuditStatus.loading));
    try {
      final report = await apiClient.compareBills(caseId: event.caseId);
      emit(_buildLoadedState(report));
    } catch (e) {
      emit(state.copyWith(
        status: AuditStatus.error,
        errorMessage: e.toString(),
      ));
    }
  }

  void _onChangePeriod(
    ChangePeriodEvent event,
    Emitter<AuditState> emit,
  ) {
    emit(state.copyWith(selectedPeriod: event.period));
  }

  void _onFilterCategory(
    FilterCategoryEvent event,
    Emitter<AuditState> emit,
  ) {
    emit(state.copyWith(selectedCategory: event.category));
  }

  Future<void> _onCaptureReceiptPhoto(
    CaptureReceiptPhotoEvent event,
    Emitter<AuditState> emit,
  ) async {
    // При фотосъемке квитанции запускаем факторный аудит
    add(LoadAuditDataEvent(caseId: event.caseId));
  }

  Future<void> _onScanQr(
    ScanQrEvent event,
    Emitter<AuditState> emit,
  ) async {
    // Совместимость: загружаем кейс
    add(const LoadAuditDataEvent(caseId: 'case_04_vladivostok_coeff3'));
  }
}
