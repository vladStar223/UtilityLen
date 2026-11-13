import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../core/models.dart';
import '../core/theme.dart';

/// Glassmorphic anomaly card — ported from web/components/anomalies.py
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
    final currency = NumberFormat('#,##0.00', 'ru_RU');
    final isRed = anomaly.severity == 'red';
    final statusStyle = isRed ? StatusBadgeStyle.error : StatusBadgeStyle.warning;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            statusStyle.color.withOpacity(0.10),
            statusStyle.color.withOpacity(0.04),
          ],
        ),
        border: Border.all(
          color: statusStyle.color.withOpacity(0.35),
          width: 1.2,
        ),
        boxShadow: [
          BoxShadow(
            color: statusStyle.color.withOpacity(0.12),
            blurRadius: 20,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header row: icon + title + impact badge
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(7),
                  decoration: BoxDecoration(
                    color: statusStyle.color.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(
                    isRed ? Icons.error_outline_rounded : Icons.warning_amber_rounded,
                    color: statusStyle.color,
                    size: 18,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    anomaly.title,
                    style: TextStyle(
                      fontSize: 13.5,
                      fontWeight: FontWeight.w700,
                      color: statusStyle.color,
                      height: 1.3,
                    ),
                  ),
                ),
                if (anomaly.impactRub > 0)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: statusStyle.color,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      '+${currency.format(anomaly.impactRub)} ₽',
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w800,
                        color: Colors.white,
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 10),

            // Category badge
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: statusStyle.badgeDecoration,
              child: Text(
                _categoryLabel(anomaly.serviceCategory),
                style: statusStyle.labelStyle,
              ),
            ),
            const SizedBox(height: 10),

            // Hint text
            Text(
              anomaly.hint,
              style: const TextStyle(
                fontSize: 12.5,
                color: AppColors.textSecondary,
                height: 1.45,
              ),
            ),

            // Draft claim CTA for red anomalies
            if (onDraftClaim != null && isRed) ...[
              const SizedBox(height: 14),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: onDraftClaim,
                  icon: const Icon(Icons.description_outlined, size: 16),
                  label: const Text('Составить досудебную претензию'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.alertRed,
                    foregroundColor: Colors.white,
                    elevation: 0,
                    padding: const EdgeInsets.symmetric(vertical: 11),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                    textStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  String _categoryLabel(String category) {
    return switch (category.toLowerCase()) {
      'хвс' || 'cold_water' || 'cws' => '💧 ХВС',
      'отопление' || 'heating' => '🔥 Отопление',
      'гвс' || 'hot_water' || 'dhw' => '♨️ ГВС',
      'электроэнергия' || 'electricity' || 'power' => '⚡ Электроэнергия',
      _ => anomaly.serviceCategory.isNotEmpty ? anomaly.serviceCategory.toUpperCase() : 'ЖКУ',
    };
  }
}
