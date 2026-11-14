import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/models.dart';
import 'profile_event.dart';
import 'profile_state.dart';

class ProfileBloc extends Bloc<ProfileEvent, ProfileState> {
  ProfileBloc() : super(const ProfileState()) {
    on<LoadProfileEvent>((event, emit) {});
    on<UpdateUserProfileEvent>(_onUpdateProfile);
    on<AddPropertyEvent>(_onAddProperty);
    on<RemovePropertyEvent>(_onRemoveProperty);
    on<ToggleNotificationsEvent>(_onToggleNotifications);
  }

  void _onUpdateProfile(
    UpdateUserProfileEvent event,
    Emitter<ProfileState> emit,
  ) {
    emit(state.copyWith(
      fullName: event.fullName,
      email: event.email,
    ));
  }

  void _onAddProperty(
    AddPropertyEvent event,
    Emitter<ProfileState> emit,
  ) {
    final updatedList = List<PropertyItem>.from(state.properties)..add(event.property);
    emit(state.copyWith(properties: updatedList));
  }

  void _onRemoveProperty(
    RemovePropertyEvent event,
    Emitter<ProfileState> emit,
  ) {
    final updatedList = state.properties.where((p) => p.id != event.propertyId).toList();
    emit(state.copyWith(properties: updatedList));
  }

  void _onToggleNotifications(
    ToggleNotificationsEvent event,
    Emitter<ProfileState> emit,
  ) {
    emit(state.copyWith(notificationsEnabled: event.enabled));
  }
}
