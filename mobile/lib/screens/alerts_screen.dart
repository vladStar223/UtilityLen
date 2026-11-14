import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../bloc/audit/audit_bloc.dart';
import '../bloc/audit/audit_state.dart';
import '../core/theme.dart';
import '../widgets/anomaly_bottom_sheet.dart';
import 'ai_chat_screen.dart';
import 'claim_screen.dart';

class AlertsScreen extends StatelessWidget {
  const AlertsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AuditBloc, AuditState>(
      builder: (context, state) {
        final overpayment = state.report?.anomalies.isNotEmpty == true
            ? state.report!.anomalies.first.impactRub
            : 245.18;

        return Scaffold(
          backgroundColor: AppColors.background,
          appBar: AppBar(
            title: const Text('Предупреждения'),
            leading: IconButton(
              icon: const Icon(Icons.arrow_back_rounded, color: AppColors.textPrimary),
              onPressed: () => Navigator.pop(context),
            ),
          ),
          body: ListView(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            children: [
              // Main Critical Alert Card
              Container(
                decoration: FintechDecorations.alertCard(radius: 20),
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    onTap: () {
                      AnomalyBottomSheet.show(
                        context,
                        amount: overpayment,
                        onCheckLegality: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => const ClaimScreen()),
                          );
                        },
                        onAskAi: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => const AiChatScreen()),
                          );
                        },
                      );
                    },
                    borderRadius: BorderRadius.circular(20),
                    child: Padding(
                      padding: const EdgeInsets.all(18),
                      child: Row(
                        children: [
                          Container(
                            width: 44,
                            height: 44,
                            decoration: BoxDecoration(
                              color: AppColors.critical.withValues(alpha: 0.15),
                              shape: BoxShape.circle,
                            ),
                            child: const Center(
                              child: Icon(
                                Icons.priority_high_rounded,
                                color: AppColors.critical,
                                size: 26,
                              ),
                            ),
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  '1 критическая проблема',
                                  style: TextStyle(
                                    color: AppColors.textPrimary,
                                    fontSize: 16,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                const Text(
                                  'Возможная переплата',
                                  style: TextStyle(
                                    color: AppColors.textSecondary,
                                    fontSize: 12,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  '${overpayment.toStringAsFixed(2).replaceAll('.', ',')} ₽',
                                  style: const TextStyle(
                                    color: AppColors.critical,
                                    fontSize: 18,
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const Icon(
                            Icons.chevron_right_rounded,
                            color: AppColors.critical,
                            size: 26,
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Section: Другие уведомления
              const Text(
                'Другие уведомления',
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 12),

              _buildNotificationItem(
                icon: Icons.warning_amber_rounded,
                iconColor: AppColors.warning,
                bgColor: AppColors.warningLight,
                title: 'Срок поверки счётчика',
                subtitle: 'Поверка истекает через 2 месяца',
                showChevron: true,
              ),
              const SizedBox(height: 12),

              _buildNotificationItem(
                icon: Icons.check_circle_outline_rounded,
                iconColor: AppColors.success,
                bgColor: AppColors.successLight,
                title: 'Начисления в норме',
                subtitle: 'По остальным услугам отклонений не найдено',
                showChevron: true,
              ),
              const SizedBox(height: 12),

              _buildNotificationItem(
                icon: Icons.shield_outlined,
                iconColor: AppColors.primary,
                bgColor: AppColors.primaryLight.withValues(alpha: 0.5),
                title: 'Ваша защита',
                subtitle: 'Мы автоматически проверяем квитанции на соответствие нормативам Владивостока и ПП РФ № 354',
                showChevron: false,
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildNotificationItem({
    required IconData icon,
    required Color iconColor,
    required Color bgColor,
    required String title,
    required String subtitle,
    required bool showChevron,
  }) {
    return Container(
      decoration: FintechDecorations.card(radius: 18),
      padding: const EdgeInsets.all(16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: bgColor,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Center(
              child: Icon(icon, color: iconColor, size: 22),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  subtitle,
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 12,
                    height: 1.3,
                  ),
                ),
              ],
            ),
          ),
          if (showChevron)
            const Icon(
              Icons.chevron_right_rounded,
              color: AppColors.textSecondary,
              size: 20,
            ),
        ],
      ),
    );
  }
}
