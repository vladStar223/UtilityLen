import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../bloc/audit/audit_bloc.dart';
import '../bloc/audit/audit_event.dart';
import '../bloc/audit/audit_state.dart';
import '../core/theme.dart';
import '../widgets/anomaly_banner.dart';
import '../widgets/anomaly_bottom_sheet.dart';
import '../widgets/hero_bill_card.dart';
import 'ai_chat_screen.dart';
import 'alerts_screen.dart';
import 'bill_details_screen.dart';
import 'claim_screen.dart';
import 'scanner_screen.dart';

class HomeScreen extends StatelessWidget {
  final VoidCallback onNavigateToReceipts;

  const HomeScreen({super.key, required this.onNavigateToReceipts});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AuditBloc, AuditState>(
      builder: (context, state) {
        final report = state.report;
        final currentAmount = report?.summary.currTotal ?? 6890.50;
        final previousAmount = report?.summary.prevTotal ?? 5420.00;
        final deltaPercent = report?.summary.deltaPct ?? 27.1;
        final deltaAmount = report?.summary.deltaAbs ?? 1470.50;
        final overpayment = report?.anomalies.isNotEmpty == true
            ? report!.anomalies.first.impactRub
            : 0.0;
        final anomalySubtitle = report?.anomalies.isNotEmpty == true
            ? report!.anomalies.first.hint
            : 'Отклонений от нормативов и тарифов не обнаружено.';

        return Scaffold(
          backgroundColor: AppColors.background,
          body: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // App bar header
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Container(
                            width: 32,
                            height: 32,
                            decoration: BoxDecoration(
                              color: AppColors.primary,
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: const Center(
                              child: Icon(
                                Icons.home_work_rounded,
                                color: Colors.white,
                                size: 18,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          const Text(
                            'UtilityLens',
                            style: TextStyle(
                              color: AppColors.textPrimary,
                              fontSize: 18,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ],
                      ),
                      Row(
                        children: [
                          IconButton(
                            icon: const Icon(
                              Icons.camera_alt_rounded,
                              color: AppColors.primary,
                              size: 24,
                            ),
                            tooltip: 'Сфотографировать квитанцию',
                            onPressed: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(builder: (_) => const ScannerScreen()),
                              );
                            },
                          ),
                          Stack(
                            children: [
                              IconButton(
                                icon: const Icon(
                                  Icons.notifications_none_rounded,
                                  color: AppColors.textPrimary,
                                  size: 26,
                                ),
                                onPressed: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(builder: (_) => const AlertsScreen()),
                                  );
                                },
                              ),
                              Positioned(
                                right: 12,
                                top: 12,
                                child: Container(
                                  width: 8,
                                  height: 8,
                                  decoration: const BoxDecoration(
                                    color: AppColors.critical,
                                    shape: BoxShape.circle,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  // Period selector
                  _buildPeriodSelector(context, state.selectedPeriod),
                  const SizedBox(height: 16),

                  // Hero card
                  HeroBillCard(
                    currentAmount: currentAmount,
                    previousAmount: previousAmount,
                    deltaPercent: deltaPercent,
                    deltaAmount: deltaAmount,
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const BillDetailsScreen()),
                      );
                    },
                  ),
                  const SizedBox(height: 16),

                  // Anomaly alert banner or Normal banner
                  if (overpayment > 0) ...[
                    AnomalyBanner(
                      amount: overpayment,
                      title: 'Обнаружена возможная переплата',
                      subtitle: anomalySubtitle,
                      onTap: () => _openAnomalyModal(context, overpayment),
                    ),
                    const SizedBox(height: 18),
                    ElevatedButton.icon(
                      onPressed: () => _openAnomalyModal(context, overpayment),
                      icon: const Icon(Icons.auto_awesome_rounded, size: 20),
                      label: const Text('Разобраться с проблемой'),
                    ),
                  ] else ...[
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.successLight,
                        borderRadius: BorderRadius.circular(18),
                        border: Border.all(color: AppColors.success.withValues(alpha: 0.3)),
                      ),
                      child: const Row(
                        children: [
                          Icon(Icons.check_circle_rounded, color: AppColors.success, size: 24),
                          SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Начисления в норме',
                                  style: TextStyle(
                                    color: AppColors.textPrimary,
                                    fontSize: 14,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                SizedBox(height: 2),
                                Text(
                                  'Тарифы и объёмы соответствуют нормативам',
                                  style: TextStyle(
                                    color: AppColors.textSecondary,
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                  const SizedBox(height: 24),

                  // Recent receipts section
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Последние квитанции',
                        style: TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      TextButton(
                        onPressed: onNavigateToReceipts,
                        child: const Text(
                          'Все →',
                          style: TextStyle(
                            color: AppColors.primary,
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),

                  // Receipt history rows
                  if (state.history.isNotEmpty)
                    ...state.history.take(2).map(
                          (item) => Padding(
                            padding: const EdgeInsets.only(bottom: 8),
                            child: _buildReceiptTile(
                              month: item.period,
                              amount: '${item.totalAmount.toStringAsFixed(2).replaceAll('.', ',')} ₽',
                              onTap: onNavigateToReceipts,
                            ),
                          ),
                        )
                  else
                    _buildReceiptTile(
                      month: 'Октябрь 2026',
                      amount: '5 420,00 ₽',
                      onTap: onNavigateToReceipts,
                    ),
                  const SizedBox(height: 16),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildPeriodSelector(BuildContext context, String currentPeriod) {
    return InkWell(
      onTap: () {
        _showPeriodPicker(context);
      },
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.border),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.calendar_today_rounded,
              color: AppColors.primary,
              size: 16,
            ),
            const SizedBox(width: 8),
            Text(
              currentPeriod,
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 14,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(width: 4),
            const Icon(
              Icons.keyboard_arrow_down_rounded,
              color: AppColors.textSecondary,
              size: 20,
            ),
          ],
        ),
      ),
    );
  }

  void _showPeriodPicker(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.card,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) {
        final periods = ['Ноябрь 2026', 'Октябрь 2026', 'Сентябрь 2026', 'Август 2026'];
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  'Выберите расчётный период',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 12),
                ...periods.map((p) => ListTile(
                      title: Text(p),
                      onTap: () {
                        context.read<AuditBloc>().add(ChangePeriodEvent(p));
                        Navigator.pop(ctx);
                      },
                    )),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildReceiptTile({
    required String month,
    required String amount,
    required VoidCallback onTap,
  }) {
    return Container(
      decoration: FintechDecorations.card(radius: 18),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(18),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            child: Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: AppColors.primaryLight,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Center(
                    child: Icon(
                      Icons.receipt_rounded,
                      color: AppColors.primary,
                      size: 20,
                    ),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Text(
                    month,
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                Text(
                  amount,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(width: 4),
                const Icon(
                  Icons.chevron_right_rounded,
                  color: AppColors.textSecondary,
                  size: 20,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _openAnomalyModal(BuildContext context, double amount) {
    AnomalyBottomSheet.show(
      context,
      amount: amount,
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
  }
}
