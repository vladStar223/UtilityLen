import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../bloc/profile/profile_bloc.dart';
import '../bloc/profile/profile_event.dart';
import '../bloc/profile/profile_state.dart';
import '../core/models.dart';
import '../core/theme.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<ProfileBloc, ProfileState>(
      builder: (context, state) {
        return Scaffold(
          backgroundColor: AppColors.background,
          appBar: AppBar(
            title: const Text('Профиль'),
            actions: [
              IconButton(
                icon: const Icon(Icons.settings_outlined, color: AppColors.textPrimary),
                onPressed: () => _showSettingsModal(context),
              ),
            ],
          ),
          body: ListView(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            children: [
              // User info card
              Container(
                decoration: FintechDecorations.card(radius: 20),
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    onTap: () => _showEditProfileDialog(context, state.fullName, state.email),
                    borderRadius: BorderRadius.circular(20),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        children: [
                          Container(
                            width: 52,
                            height: 52,
                            decoration: BoxDecoration(
                              color: AppColors.primaryLight,
                              shape: BoxShape.circle,
                              border: Border.all(color: AppColors.primary.withValues(alpha: 0.3)),
                            ),
                            child: Center(
                              child: Text(
                                state.fullName.isNotEmpty ? state.fullName[0] : 'А',
                                style: const TextStyle(
                                  color: AppColors.primary,
                                  fontSize: 22,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  state.fullName,
                                  style: const TextStyle(
                                    color: AppColors.textPrimary,
                                    fontSize: 16,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  state.email,
                                  style: const TextStyle(
                                    color: AppColors.textSecondary,
                                    fontSize: 13,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const Icon(
                            Icons.chevron_right_rounded,
                            color: AppColors.textSecondary,
                            size: 24,
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Section: Мои объекты
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Мои объекты',
                    style: TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  Text(
                    '${state.properties.length} шт.',
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // List of properties
              ...state.properties.map((prop) => _buildPropertyCard(context, prop)),

              // Button: Добавить объект
              OutlinedButton.icon(
                onPressed: () => _showAddPropertyDialog(context),
                icon: const Icon(Icons.add_rounded, size: 20),
                label: const Text('Добавить объект'),
              ),
              const SizedBox(height: 28),

              // Settings list
              Container(
                decoration: FintechDecorations.card(radius: 20),
                child: Column(
                  children: [
                    _buildSettingsTile(
                      icon: Icons.notifications_none_rounded,
                      title: 'Уведомления',
                      trailing: Switch(
                        value: state.notificationsEnabled,
                        activeColor: AppColors.primary,
                        onChanged: (val) {
                          context.read<ProfileBloc>().add(ToggleNotificationsEvent(val));
                        },
                      ),
                    ),
                    const Divider(height: 1, indent: 56, endIndent: 16, color: AppColors.border),
                    _buildSettingsTile(
                      icon: Icons.history_rounded,
                      title: 'История действий',
                      onTap: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('История проверок пуста: 1 активный аудит')),
                        );
                      },
                    ),
                    const Divider(height: 1, indent: 56, endIndent: 16, color: AppColors.border),
                    _buildSettingsTile(
                      icon: Icons.info_outline_rounded,
                      title: 'О приложении',
                      onTap: () => _showAboutDialog(context, state.appVersion),
                    ),
                    const Divider(height: 1, indent: 56, endIndent: 16, color: AppColors.border),
                    _buildSettingsTile(
                      icon: Icons.support_agent_rounded,
                      title: 'Поддержка',
                      onTap: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Связь с поддержкой: support@utilitylens.ru')),
                        );
                      },
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        );
      },
    );
  }

  Widget _buildPropertyCard(BuildContext context, PropertyItem prop) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: FintechDecorations.card(radius: 18),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Выбран объект: ${prop.title} (${prop.address})')),
            );
          },
          borderRadius: BorderRadius.circular(18),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: AppColors.primaryLight,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Center(
                    child: Icon(
                      Icons.home_rounded,
                      color: AppColors.primary,
                      size: 22,
                    ),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        prop.title,
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        prop.address,
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
                const Icon(
                  Icons.chevron_right_rounded,
                  color: AppColors.textSecondary,
                  size: 22,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSettingsTile({
    required IconData icon,
    required String title,
    Widget? trailing,
    VoidCallback? onTap,
  }) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            Icon(icon, color: AppColors.primary, size: 22),
            const SizedBox(width: 14),
            Expanded(
              child: Text(
                title,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            trailing ??
                const Icon(
                  Icons.chevron_right_rounded,
                  color: AppColors.textSecondary,
                  size: 20,
                ),
          ],
        ),
      ),
    );
  }

  void _showEditProfileDialog(BuildContext context, String initialName, String initialEmail) {
    final nameCtrl = TextEditingController(text: initialName);
    final emailCtrl = TextEditingController(text: initialEmail);

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.card,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Редактировать профиль'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameCtrl,
              decoration: const InputDecoration(labelText: 'Имя и фамилия'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: emailCtrl,
              decoration: const InputDecoration(labelText: 'Электронная почта'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Отмена'),
          ),
          ElevatedButton(
            onPressed: () {
              context.read<ProfileBloc>().add(
                    UpdateUserProfileEvent(
                      fullName: nameCtrl.text.trim(),
                      email: emailCtrl.text.trim(),
                    ),
                  );
              Navigator.pop(ctx);
            },
            child: const Text('Сохранить'),
          ),
        ],
      ),
    );
  }

  void _showAddPropertyDialog(BuildContext context) {
    final titleCtrl = TextEditingController();
    final addressCtrl = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.card,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Новый объект'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: titleCtrl,
              decoration: const InputDecoration(labelText: 'Название (напр. Квартира №24)'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: addressCtrl,
              decoration: const InputDecoration(labelText: 'Адрес (напр. г. Владивосток...)'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Отмена'),
          ),
          ElevatedButton(
            onPressed: () {
              if (titleCtrl.text.trim().isNotEmpty) {
                context.read<ProfileBloc>().add(
                      AddPropertyEvent(
                        PropertyItem(
                          id: 'prop_${DateTime.now().millisecondsSinceEpoch}',
                          title: titleCtrl.text.trim(),
                          address: addressCtrl.text.trim().isNotEmpty
                              ? addressCtrl.text.trim()
                              : 'г. Владивосток',
                          accountNumber: '30KO-${DateTime.now().millisecond}',
                        ),
                      ),
                    );
              }
              Navigator.pop(ctx);
            },
            child: const Text('Добавить'),
          ),
        ],
      ),
    );
  }

  void _showAboutDialog(BuildContext context, String version) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.card,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('О приложении UtilityLens'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Версия: $version', style: const TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            const Text(
              'UtilityLens — сервис интеллектуального аудита квитанций ЖКХ, выявления необоснованных переплат и защиты прав потребителей по Постановлению Правительства РФ № 354.',
              style: TextStyle(fontSize: 13, height: 1.35),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Закрыть'),
          ),
        ],
      ),
    );
  }

  void _showSettingsModal(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Настройки синхронизации активны')),
    );
  }
}
