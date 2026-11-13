import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
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
    final currencyFormat = NumberFormat("#,##0.00", "ru_RU");
    final isPositiveDelta = (deltaAmount ?? 0) > 0;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: TextStyle(
                fontSize: 13,
                color: Colors.white.withOpacity(0.6),
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 8),
            Row(
              crossAxisAlignment: CrossAxisAlignment.baseline,
              textBaseline: TextBaseline.alphabetic,
              children: [
                Text(
                  "${currencyFormat.format(amount)} ₽",
                  style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
            if (deltaAmount != null) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: isAlert
                      ? AppTheme.alertRedBg
                      : (isPositiveDelta
                          ? AppTheme.warningYellowBg
                          : AppTheme.successGreenBg),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  "${isPositiveDelta ? '+' : ''}${currencyFormat.format(deltaAmount)} ₽ (${isPositiveDelta ? '+' : ''}${deltaPct?.toStringAsFixed(1)}%)",
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: isAlert
                        ? AppTheme.alertRed
                        : (isPositiveDelta
                            ? AppTheme.warningYellow
                            : AppTheme.successGreen),
                  ),
                ),
              ),
            ],
            if (subtitle != null) ...[
              const SizedBox(height: 6),
              Text(
                subtitle!,
                style: TextStyle(
                  fontSize: 11,
                  color: Colors.white.withOpacity(0.4),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
