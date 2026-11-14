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

  static String _periodToHuman(String period) {
    if (period.contains('11')) return 'Ноябрь 2026';
    if (period.contains('10')) return 'Октябрь 2026';
    if (period.contains('09')) return 'Сентябрь 2026';
    if (period.contains('08')) return 'Август 2026';
    return period.isNotEmpty ? period : 'Ноябрь 2026';
  }

  static String _periodToMonthLabel(String period) {
    if (period.contains('11')) return 'Ноя';
    if (period.contains('10')) return 'Окт';
    if (period.contains('09')) return 'Сен';
    if (period.contains('08')) return 'Авг';
    if (period.contains('07')) return 'Июл';
    if (period.contains('06')) return 'Июн';
    return period;
  }

  AuditState _buildLoadedState(ComparisonReport report) {
    const history = [
      ReceiptHistoryItem(
        id: 'rec_2026_11',
        period: 'Ноябрь 2026',
        totalAmount: 6890.50,
        providerName: 'ДЭК «Дальэнергосбыт» / ХВС',
        hasOverpayment: true,
        overpaymentAmount: 245.18,
      ),
      ReceiptHistoryItem(
        id: 'rec_2026_10',
        period: 'Октябрь 2026',
        totalAmount: 5420.00,
        providerName: 'АО «Дальневосточная РКЦ»',
        hasOverpayment: false,
      ),
      ReceiptHistoryItem(
        id: 'rec_2026_09',
        period: 'Сентябрь 2026',
        totalAmount: 1437.50,
        providerName: 'КГУП «Примводоканал»',
        hasOverpayment: true,
        overpaymentAmount: 686.56,
      ),
      ReceiptHistoryItem(
        id: 'rec_2026_08',
        period: 'Август 2026',
        totalAmount: 5100.00,
        providerName: 'КГУП «Приморский водоканал»',
        hasOverpayment: false,
      ),
    ];

    final currAmount = report.summary.currTotal;
    final prevAmount = report.summary.prevTotal;
    final currPeriod = report.summary.currPeriod;
    final prevPeriod = report.summary.prevPeriod;

    final currLabel = _periodToMonthLabel(currPeriod);
    final prevLabel = _periodToMonthLabel(prevPeriod);

    final trends = [
      const MonthlyTrendItem(monthLabel: 'Июн', amount: 4200),
      const MonthlyTrendItem(monthLabel: 'Июл', amount: 4800),
      const MonthlyTrendItem(monthLabel: 'Авг', amount: 5100),
      MonthlyTrendItem(monthLabel: prevLabel, amount: prevAmount),
      MonthlyTrendItem(monthLabel: currLabel, amount: currAmount),
    ];

    final overpaymentAmount = report.anomalies.isNotEmpty
        ? report.anomalies.first.impactRub
        : 0.0;
    final overpaymentDesc = report.anomalies.isNotEmpty
        ? report.anomalies.first.hint
        : 'Начисления в норме, переплат не обнаружено';

    final alerts = [
      if (overpaymentAmount > 0)
        AlertNotificationItem(
          id: 'alert_critical_1',
          title: '1 критическая проблема',
          description: overpaymentDesc,
          severity: 'critical',
          amount: overpaymentAmount,
        ),
      const AlertNotificationItem(
        id: 'alert_meter_warning',
        title: 'Срок поверки счётчика',
        description: 'Поверка истекает через 2 месяца',
        severity: 'warning',
      ),
      const AlertNotificationItem(
        id: 'alert_norm_ok',
        title: 'Начисления в норме',
        description: 'По остальным услугам отклонений не найдено',
        severity: 'success',
      ),
      const AlertNotificationItem(
        id: 'alert_protection',
        title: 'Ваша защита активна',
        description: 'Мы автоматически проверяем квитанции на соответствие нормативам Владивостока и ПП РФ № 354',
        severity: 'info',
      ),
    ];

    final humanPeriod = _periodToHuman(report.summary.currPeriod);

    return state.copyWith(
      status: AuditStatus.loaded,
      report: report,
      history: history,
      monthlyTrends: trends,
      alerts: alerts,
      selectedPeriod: humanPeriod,
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

  Future<void> _onChangePeriod(
    ChangePeriodEvent event,
    Emitter<AuditState> emit,
  ) async {
    final String targetCase;
    if (event.period.contains('Окт')) {
      targetCase = 'case_01_heating_spike';
    } else if (event.period.contains('Сен')) {
      targetCase = 'case_04_vladivostok_coeff3';
    } else if (event.period.contains('Авг')) {
      targetCase = 'case_03_tariff_index';
    } else {
      targetCase = 'case_02_coeff_15';
    }

    emit(state.copyWith(status: AuditStatus.loading, selectedPeriod: event.period));
    try {
      final report = await apiClient.compareBills(caseId: targetCase);
      emit(_buildLoadedState(report).copyWith(selectedPeriod: event.period));
    } catch (e) {
      emit(state.copyWith(
        status: AuditStatus.error,
        errorMessage: e.toString(),
      ));
    }
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
    add(LoadAuditDataEvent(caseId: event.caseId));
  }

  Future<void> _onScanQr(
    ScanQrEvent event,
    Emitter<AuditState> emit,
  ) async {
    add(const LoadAuditDataEvent(caseId: 'case_04_vladivostok_coeff3'));
  }
}
