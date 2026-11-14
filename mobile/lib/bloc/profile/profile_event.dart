import 'package:equatable/equatable.dart';
import '../../core/models.dart';

abstract class ProfileEvent extends Equatable {
  const ProfileEvent();

  @override
  List<Object?> get props => [];
}

class LoadProfileEvent extends ProfileEvent {}

class UpdateUserProfileEvent extends ProfileEvent {
  final String fullName;
  final String email;

  const UpdateUserProfileEvent({required this.fullName, required this.email});

  @override
  List<Object?> get props => [fullName, email];
}

class AddPropertyEvent extends ProfileEvent {
  final PropertyItem property;
  const AddPropertyEvent(this.property);

  @override
  List<Object?> get props => [property];
}

class RemovePropertyEvent extends ProfileEvent {
  final String propertyId;
  const RemovePropertyEvent(this.propertyId);

  @override
  List<Object?> get props => [propertyId];
}

class ToggleNotificationsEvent extends ProfileEvent {
  final bool enabled;
  const ToggleNotificationsEvent(this.enabled);

  @override
  List<Object?> get props => [enabled];
}
