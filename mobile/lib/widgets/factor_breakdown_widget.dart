import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../core/models.dart';
import '../core/theme.dart';

/// Full ΔS = ΔT + ΔV + ΔR factor breakdown widget
/// Ported from web/components/anomalies.py factor analysis section
class FactorBreakdownWidget extends StatelessWidget {
  final FactorBreakdown breakdown;

  const FactorBreakdownWidget({super.key, required this.breakdown});

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat('#,##0.00', 'ru_RU');
    final total = breakdown.tariffEffectRub +
        breakdown.volumeEffectRub +
        breakdown.recalculationEffectRub +
        breakdown.newServicesEffectRub;

    return Container(
      decoration: GlassDecoration.dark(radius: 18),
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(7),
                decoration: BoxDecoration(
                  color: AppColors.lavender.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.calculate_outlined, color: AppColors.lavender, size: 18),
              ),
              const SizedBox(width: 10),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Факторный рентген изменения',
                      style: TextStyle(
                        fontSize: 14.5,
                        fontWeight: FontWeight.w700,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    Text(
                      'Детерминированное ядро: ΔS = ΔT + ΔV + ΔR',
                      style: TextStyle(
                        fontSize: 11,
                        color: AppColors.textMuted,
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),

          // ΔT — tariff effect
          _FactorRow(
            symbol: 'ΔT',
            icon: Icons.trending_up_rounded,
            title: 'Рост тарифов (тарифный эффект)',
            amount: breakdown.tariffEffectRub,
            accentColor: AppColors.warningYellow,
            currency: currency,
          ),
          _FactorDivider(),

          // ΔV — volume effect
          _FactorRow(
            symbol: 'ΔV',
            icon: Icons.water_drop_outlined,
            title: 'Изменение объёма потребления',
            amount: breakdown.volumeEffectRub,
            accentColor: AppColors.lavender,
            currency: currency,
          ),
          _FactorDivider(),

          // ΔR — recalculation / penalty
          _FactorRow(
            symbol: 'ΔR',
            icon: Icons.gavel_rounded,
            title: 'Штрафы и перерасчёты УК',
            amount: breakdown.recalculationEffectRub,
            accentColor: AppColors.alertRed,
            currency: currency,
            isHighlight: true,
          ),

          if (breakdown.newServicesEffectRub > 0) ...[
            _FactorDivider(),
            _FactorRow(
              symbol: 'ΔN',
              icon: Icons.add_circle_outline,
              title: 'Новые услуги',
              amount: breakdown.newServicesEffectRub,
              accentColor: const Color(0xFFC084FC),
              currency: currency,
            ),
          ],

          // Total ΔS
          const SizedBox(height: 14),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  AppColors.lavender.withOpacity(0.10),
                  AppColors.violet.withOpacity(0.06),
                ],
              ),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.lavender.withOpacity(0.22)),
            ),
            child: Row(
              children: [
                const Text(
                  'ΔS',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w900,
                    color: AppColors.lavender,
                    letterSpacing: 0.5,
                  ),
                ),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text(
                    'Итого изменение суммы счёта',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: AppColors.textPrimary,
                    ),
                  ),
                ),
                Text(
                  '${total >= 0 ? '+' : ''}${currency.format(total)} ₽',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                    color: total > 0 ? AppColors.alertRed : AppColors.successGreen,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _FactorDivider extends StatelessWidget {
  @override
  Widget build(BuildContext context) =>
      const Divider(color: AppColors.glassBorder, height: 20, thickness: 0.5);
}

class _FactorRow extends StatelessWidget {
  final String symbol;
  final IconData icon;
  final String title;
  final double amount;
  final Color accentColor;
  final NumberFormat currency;
  final bool isHighlight;

  const _FactorRow({
    required this.symbol,
    required this.icon,
    required this.title,
    required this.amount,
    required this.accentColor,
    required this.currency,
    this.isHighlight = false,
  });

  @override
  Widget build(BuildContext context) {
    final isPositive = amount > 0;
    return Row(
      children: [
        // Greek-letter symbol pill
        Container(
          width: 30,
          height: 30,
          decoration: BoxDecoration(
            color: accentColor.withOpacity(0.14),
            borderRadius: BorderRadius.circular(8),
          ),
          alignment: Alignment.center,
          child: Text(
            symbol,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w900,
              color: accentColor,
              letterSpacing: 0.3,
            ),
          ),
        ),
        const SizedBox(width: 10),
        Container(
          padding: const EdgeInsets.all(5),
          decoration: BoxDecoration(
            color: accentColor.withOpacity(0.10),
            borderRadius: BorderRadius.circular(7),
          ),
          child: Icon(icon, color: accentColor, size: 15),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            title,
            style: TextStyle(
              fontSize: 13,
              fontWeight: isHighlight ? FontWeight.w700 : FontWeight.w500,
              color: isHighlight ? AppColors.textPrimary : AppColors.textSecondary,
            ),
          ),
        ),
        Text(
          '${isPositive ? '+' : ''}${currency.format(amount)} ₽',
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w700,
            color: isHighlight
                ? AppColors.alertRed
                : (isPositive ? accentColor : AppColors.successGreen),
          ),
        ),
      ],
    );
  }
}
