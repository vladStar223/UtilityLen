import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../core/models.dart';
import '../core/theme.dart';

/// ServiceItemTile with glassmorphic styling and category emoji badges
class ServiceItemTile extends StatelessWidget {
  final ServiceItem item;

  const ServiceItemTile({super.key, required this.item});

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat('#,##0.00', 'ru_RU');
    final isAlert = item.status == 'red';
    final isWarning = item.status == 'yellow';

    final statusColor = isAlert
        ? AppColors.alertRed
        : isWarning
            ? AppColors.warningYellow
            : AppColors.successGreen;

    final decoration = isAlert
        ? GlassDecoration.dark(
            radius: 14,
            extraShadows: [
              BoxShadow(
                color: AppColors.alertRed.withOpacity(0.10),
                blurRadius: 16,
                offset: const Offset(0, 3),
              ),
            ],
          )
        : GlassDecoration.dark(radius: 14);

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: decoration,
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          tilePadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
          leading: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 10,
                height: 10,
                decoration: BoxDecoration(
                  color: statusColor,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(color: statusColor.withOpacity(0.5), blurRadius: 6),
                  ],
                ),
              ),
            ],
          ),
          title: Row(
            children: [
              Text(
                _categoryEmoji(item.category),
                style: const TextStyle(fontSize: 15),
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  item.displayName,
                  style: const TextStyle(
                    fontSize: 13.5,
                    fontWeight: FontWeight.w600,
                    color: AppColors.textPrimary,
                  ),
                ),
              ),
            ],
          ),
          subtitle: Padding(
            padding: const EdgeInsets.only(top: 2),
            child: Text(
              'Расход: ${item.currVolume} ${item.unit} • Тариф: ${item.currTariff} ₽',
              style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
            ),
          ),
          trailing: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '${currency.format(item.currTotal)} ₽',
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
              if (item.deltaAbs != 0)
                Text(
                  '${item.deltaAbs > 0 ? '+' : ''}${currency.format(item.deltaAbs)} ₽',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: statusColor,
                  ),
                ),
            ],
          ),
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Divider(color: AppColors.glassBorder, thickness: 0.5),
                  const SizedBox(height: 6),
                  Text(
                    item.plainExplanation,
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppColors.textSecondary,
                      height: 1.5,
                    ),
                  ),
                  if (item.coeffSurchargeRub > 0) ...[
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: AppColors.alertRedBg,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                          color: AppColors.alertRed.withOpacity(0.35),
                        ),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.warning_rounded,
                              color: AppColors.alertRed, size: 16),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Скрытый штраф / коэффициент: '
                              '+${currency.format(item.coeffSurchargeRub)} ₽',
                              style: const TextStyle(
                                fontSize: 11.5,
                                color: AppColors.alertRed,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _categoryEmoji(String category) {
    return switch (category.toLowerCase()) {
      'хвс' || 'cold_water' || 'cws' => '💧',
      'отопление' || 'heating' => '🔥',
      'гвс' || 'hot_water' || 'dhw' => '♨️',
      'электроэнергия' || 'electricity' || 'power' => '⚡',
      _ => '📋',
    };
  }
}
