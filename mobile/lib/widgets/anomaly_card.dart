import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../core/models.dart';
import '../core/theme.dart';

class AnomalyCard extends StatelessWidget {
  final AnomalyItem anomaly;
  final VoidCallback? onDraftClaim;

  const AnomalyCard({
    super.key,
    required this.anomaly,
    this.onDraftClaim,
  });

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat("#,##0.00", "ru_RU");
    final isRed = anomaly.severity == "red";

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isRed ? AppTheme.alertRedBg : AppTheme.warningYellowBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: (isRed ? AppTheme.alertRed : AppTheme.warningYellow).withOpacity(0.4),
          width: 1.2,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                isRed ? Icons.error_outline : Icons.warning_amber_rounded,
                color: isRed ? AppTheme.alertRed : AppTheme.warningYellow,
                size: 20,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  anomaly.title,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: isRed ? AppTheme.alertRed : AppTheme.warningYellow,
                  ),
                ),
              ),
              if (anomaly.impactRub > 0)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.alertRed,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    "+${currency.format(anomaly.impactRub)} ₽",
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            anomaly.hint,
            style: TextStyle(
              fontSize: 12,
              color: Colors.white.withOpacity(0.85),
              height: 1.4,
            ),
          ),
          if (onDraftClaim != null && isRed) ...[
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: onDraftClaim,
                icon: const Icon(Icons.description_outlined, size: 16),
                label: const Text("Составить досудебную претензию"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.alertRed,
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  textStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
