import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../core/models.dart';
import '../core/theme.dart';

class KpiCard extends StatelessWidget {
  final String title;
  final double amount;
  final double? deltaAmount;
  final double? deltaPct;
  final String? subtitle;
  final bool isAlert;

  const KpiCard({
    super.key,
    required this.title,
    required this.amount,
    this.deltaAmount,
    this.deltaPct,
    this.subtitle,
    this.isAlert = false,
  });

  @override
  Widget build(BuildContext context) {
    final currencyFormat = NumberFormat('#,##0.00', 'ru_RU');
    final isPositiveDelta = (deltaAmount ?? 0) > 0;

    return Container(
      decoration: GlassDecoration.dark(radius: 16),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: TextStyle(
              fontSize: 12,
              color: AppColors.textMuted,
              fontWeight: FontWeight.w500,
              letterSpacing: 0.2,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            '${currencyFormat.format(amount)} ₽',
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.bold,
              color: AppColors.textPrimary,
            ),
          ),
          if (deltaAmount != null) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: isAlert
                    ? AppColors.alertRedBg
                    : (isPositiveDelta
                        ? AppColors.warningYellowBg
                        : AppColors.successGreenBg),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: (isAlert
                          ? AppColors.alertRed
                          : (isPositiveDelta ? AppColors.warningYellow : AppColors.successGreen))
                      .withOpacity(0.3),
                  width: 1,
                ),
              ),
              child: Text(
                '${isPositiveDelta ? '+' : ''}${currencyFormat.format(deltaAmount)} ₽ '
                '(${isPositiveDelta ? '+' : ''}${deltaPct?.toStringAsFixed(1)}%)',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  color: isAlert
                      ? AppColors.alertRed
                      : (isPositiveDelta ? AppColors.warningYellow : AppColors.successGreen),
                ),
              ),
            ),
          ],
          if (subtitle != null) ...[
            const SizedBox(height: 6),
            Text(
              subtitle!,
              style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
            ),
          ],
        ],
      ),
    );
  }
}

/// Compact KPI summary strip (3 tiles in a row) ported from web kpi_cards.py
class KpiSummaryStrip extends StatelessWidget {
  final ComparisonReport report;

  const KpiSummaryStrip({super.key, required this.report});

  @override
  Widget build(BuildContext context) {
    final fmt = NumberFormat('#,##0.00', 'ru_RU');
    final totalAnomaly = report.anomalies.fold<double>(0, (s, a) => s + a.impactRub);

    return Row(
      children: [
        _MiniKpi(label: 'Было', value: '${fmt.format(report.summary.prevTotal)} ₽'),
        const SizedBox(width: 8),
        _MiniKpi(
          label: 'Стало',
          value: '${fmt.format(report.summary.currTotal)} ₽',
          accent: report.summary.deltaAbs > 0 ? AppColors.alertRed : AppColors.successGreen,
        ),
        const SizedBox(width: 8),
        _MiniKpi(
          label: 'Переплата',
          value: '+${fmt.format(totalAnomaly)} ₽',
          accent: AppColors.alertRed,
          highlight: true,
        ),
      ],
    );
  }
}

class _MiniKpi extends StatelessWidget {
  final String label;
  final String value;
  final Color? accent;
  final bool highlight;

  const _MiniKpi({
    required this.label,
    required this.value,
    this.accent,
    this.highlight = false,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
        decoration: highlight ? GlassDecoration.darkAccent(radius: 14) : GlassDecoration.dark(radius: 14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label,
                style: const TextStyle(fontSize: 11, color: AppColors.textMuted, letterSpacing: 0.2)),
            const SizedBox(height: 4),
            Text(
              value,
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w700,
                color: accent ?? AppColors.textPrimary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
