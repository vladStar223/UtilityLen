import 'package:equatable/equatable.dart';
import '../../core/models.dart';

class ProfileState extends Equatable {
  final String fullName;
  final String email;
  final List<PropertyItem> properties;
  final bool notificationsEnabled;
  final String appVersion;

  const ProfileState({
    this.fullName = 'Алексей Петров',
    this.email = 'alexey@example.ru',
    this.properties = const [
      PropertyItem(
        id: 'prop_vlad_24',
        title: 'Квартира №24',
        address: 'г. Владивосток, ул. Амурская, д. 7',
        accountNumber: '30KO233810-14',
        isDefault: true,
      ),
    ],
    this.notificationsEnabled = true,
    this.appVersion = '1.0.0 (Build 42)',
  });

  ProfileState copyWith({
    String? fullName,
    String? email,
    List<PropertyItem>? properties,
    bool? notificationsEnabled,
    String? appVersion,
  }) {
    return ProfileState(
      fullName: fullName ?? this.fullName,
      email: email ?? this.email,
      properties: properties ?? this.properties,
      notificationsEnabled: notificationsEnabled ?? this.notificationsEnabled,
      appVersion: appVersion ?? this.appVersion,
    );
  }

  @override
  List<Object?> get props => [
        fullName,
        email,
        properties,
        notificationsEnabled,
        appVersion,
      ];
}
