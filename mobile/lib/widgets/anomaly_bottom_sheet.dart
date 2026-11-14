import 'package:flutter/material.dart';
import '../core/theme.dart';

class AnomalyBottomSheet extends StatelessWidget {
  final double amount;
  final VoidCallback onCheckLegality;
  final VoidCallback onAskAi;

  const AnomalyBottomSheet({
    super.key,
    required this.amount,
    required this.onCheckLegality,
    required this.onAskAi,
  });

  static Future<void> show(
    BuildContext context, {
    required double amount,
    required VoidCallback onCheckLegality,
    required VoidCallback onAskAi,
  }) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => AnomalyBottomSheet(
        amount: amount,
        onCheckLegality: onCheckLegality,
        onAskAi: onAskAi,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Drag handle
            Center(
              child: Container(
                width: 44,
                height: 4,
                decoration: BoxDecoration(
                  color: AppColors.border,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Header + Close button
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Подробности начисления',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close_rounded, color: AppColors.textSecondary),
                  onPressed: () => Navigator.pop(context),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Card with overpayment
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: AppColors.criticalLight,
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: AppColors.critical.withValues(alpha: 0.2)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          const Icon(
                            Icons.warning_amber_rounded,
                            color: AppColors.critical,
                            size: 26,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            '${amount.toStringAsFixed(2).replaceAll('.', ',')} ₽',
                            style: const TextStyle(
                              color: AppColors.critical,
                              fontSize: 24,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ],
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppColors.critical.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Text(
                          'Требует проверки',
                          style: TextStyle(
                            color: AppColors.critical,
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Возможная переплата',
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 18),

            // Section 1: Почему возникла проблема?
            const Text(
              'Почему возникла проблема?',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 15,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 6),
            const Text(
              'Применён повышающий коэффициент 1,5. Необходимо проверить срок поверки прибора и наличие переданных показаний.',
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 13,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 20),

            // Section 2: Что можно сделать?
            const Text(
              'Что можно сделать?',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 15,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 12),

            ElevatedButton(
              onPressed: () {
                Navigator.pop(context);
                onCheckLegality();
              },
              child: const Text('Проверить законность начисления'),
            ),
            const SizedBox(height: 10),

            OutlinedButton(
              onPressed: () {
                Navigator.pop(context);
                onAskAi();
              },
              style: OutlinedButton.styleFrom(
                backgroundColor: AppColors.primaryLight.withValues(alpha: 0.5),
                side: BorderSide.none,
              ),
              child: const Text('Объяснить через AI-юриста'),
            ),
            const SizedBox(height: 14),

            // Footer disclaimer
            Row(
              children: [
                Icon(
                  Icons.info_outline_rounded,
                  color: AppColors.textSecondary.withValues(alpha: 0.8),
                  size: 16,
                ),
                const SizedBox(width: 6),
                const Expanded(
                  child: Text(
                    'Данные основаны на информации из вашей квитанции.',
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 11,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
          ],
        ),
      ),
    );
  }
}
