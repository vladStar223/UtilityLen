import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../core/models.dart';
import '../core/theme.dart';

class FactorBreakdownWidget extends StatelessWidget {
  final FactorBreakdown breakdown;

  const FactorBreakdownWidget({super.key, required this.breakdown});

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat("#,##0.00", "ru_RU");

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.calculate_outlined, color: AppTheme.accentCyan, size: 20),
                const SizedBox(width: 8),
                const Text(
                  "Факторный рентген изменения (ΔS)",
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              "Математическое разложение детерминированного ядра:",
              style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.5)),
            ),
            const SizedBox(height: 16),
            _buildFactorRow(
              icon: Icons.trending_up,
              title: "Рост тарифов края (ΔT)",
              amount: breakdown.tariffEffectRub,
              color: AppTheme.warningYellow,
              currency: currency,
            ),
            const Divider(color: Colors.white10, height: 16),
            _buildFactorRow(
              icon: Icons.water_drop_outlined,
              title: "Изменение объема (ΔV)",
              amount: breakdown.volumeEffectRub,
              color: AppTheme.primaryBlue,
              currency: currency,
            ),
            const Divider(color: Colors.white10, height: 16),
            _buildFactorRow(
              icon: Icons.gavel_outlined,
              title: "Штрафы и перерасчеты УК (ΔR)",
              amount: breakdown.recalculationEffectRub,
              color: AppTheme.alertRed,
              currency: currency,
              isHighlight: true,
            ),
            if (breakdown.newServicesEffectRub > 0) ...[
              const Divider(color: Colors.white10, height: 16),
              _buildFactorRow(
                icon: Icons.add_circle_outline,
                title: "Новые услуги (ΔN)",
                amount: breakdown.newServicesEffectRub,
                color: Colors.purpleAccent,
                currency: currency,
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildFactorRow({
    required IconData icon,
    required String title,
    required double amount,
    required Color color,
    required NumberFormat currency,
    bool isHighlight = false,
  }) {
    final isPositive = amount > 0;
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(6),
          decoration: BoxDecoration(
            color: color.withOpacity(0.15),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, color: color, size: 16),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            title,
            style: TextStyle(
              fontSize: 13,
              fontWeight: isHighlight ? FontWeight.bold : FontWeight.w500,
              color: isHighlight ? Colors.white : Colors.white.withOpacity(0.8),
            ),
          ),
        ),
        Text(
          "${isPositive ? '+' : ''}${currency.format(amount)} ₽",
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
            color: isHighlight ? AppTheme.alertRed : (isPositive ? color : AppTheme.successGreen),
          ),
        ),
      ],
    );
  }
}
