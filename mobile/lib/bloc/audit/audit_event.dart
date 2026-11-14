import 'package:equatable/equatable.dart';
import '../../core/models.dart';

abstract class AuditEvent extends Equatable {
  const AuditEvent();

  @override
  List<Object?> get props => [];
}

class LoadAuditDataEvent extends AuditEvent {
  final String caseId;
  const LoadAuditDataEvent({this.caseId = 'case_02_coeff_15'});

  @override
  List<Object?> get props => [caseId];
}

class ChangePeriodEvent extends AuditEvent {
  final String period;
  const ChangePeriodEvent(this.period);

  @override
  List<Object?> get props => [period];
}

class FilterCategoryEvent extends AuditEvent {
  final String category;
  const FilterCategoryEvent(this.category);

  @override
  List<Object?> get props => [category];
}

class CaptureReceiptPhotoEvent extends AuditEvent {
  final String? filePath;
  final String caseId;
  const CaptureReceiptPhotoEvent({this.filePath, this.caseId = 'case_04_vladivostok_coeff3'});

  @override
  List<Object?> get props => [filePath, caseId];
}

class ScanQrEvent extends AuditEvent {
  final String qrPayload;
  const ScanQrEvent(this.qrPayload);

  @override
  List<Object?> get props => [qrPayload];
}

class SetAuditReportEvent extends AuditEvent {
  final ComparisonReport report;
  const SetAuditReportEvent(this.report);

  @override
  List<Object?> get props => [report];
}
