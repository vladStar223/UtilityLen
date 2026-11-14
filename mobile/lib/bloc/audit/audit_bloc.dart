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
    // Данные истории/трендов/алертов строятся только из реального отчета.
    // Никаких хардкодных моков — пустые списки, если бэкенд ничего не вернул.
    final alerts = <AlertNotificationItem>[];
    for (final anomaly in report.anomalies) {
      final severity = _mapSeverity(anomaly.severity);
      alerts.add(AlertNotificationItem(
        id: 'alert_${anomaly.code}',
        title: anomaly.title.isNotEmpty ? anomaly.title : 'Обнаружена аномалия',
        description: anomaly.hint,
        severity: severity,
        amount: anomaly.impactRub > 0 ? anomaly.impactRub : null,
      ));
    }

    return state.copyWith(
      status: AuditStatus.loaded,
      report: report,
      alerts: alerts,
    );
  }

  String _mapSeverity(String raw) {
    switch (raw) {
      case 'red':
        return 'critical';
      case 'yellow':
        return 'warning';
      case 'info':
        return 'info';
      case 'green':
        return 'success';
      default:
        return raw;
    }
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
