import 'package:equatable/equatable.dart';

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

class ScanQrEvent extends AuditEvent {
  final String qrPayload;
  const ScanQrEvent(this.qrPayload);

  @override
  List<Object?> get props => [qrPayload];
}
