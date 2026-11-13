import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../core/models.dart';
import '../core/theme.dart';

class ServiceItemTile extends StatelessWidget {
  final ServiceItem item;

  const ServiceItemTile({super.key, required this.item});

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat("#,##0.00", "ru_RU");
    final isAlert = item.status == "red";
    final isWarning = item.status == "yellow";

    Color statusColor = AppTheme.successGreen;
    if (isAlert) statusColor = AppTheme.alertRed;
    if (isWarning) statusColor = AppTheme.warningYellow;

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: ExpansionTile(
        tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        leading: Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(
            color: statusColor,
            shape: BoxShape.circle,
          ),
        ),
        title: Text(
          item.displayName,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: Colors.white,
          ),
        ),
        subtitle: Text(
          "Расход: ${item.currVolume} ${item.unit} • Тариф: ${item.currTariff} ₽",
          style: TextStyle(
            fontSize: 12,
            color: Colors.white.withOpacity(0.5),
          ),
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              "${currency.format(item.currTotal)} ₽",
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            if (item.deltaAbs != 0)
              Text(
                "${item.deltaAbs > 0 ? '+' : ''}${currency.format(item.deltaAbs)} ₽",
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: statusColor,
                ),
              ),
          ],
        ),
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Divider(color: Colors.white10),
                const SizedBox(height: 6),
                Text(
                  item.plainExplanation,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.white.withOpacity(0.8),
                    height: 1.4,
                  ),
                ),
                if (item.coeffSurchargeRub > 0) ...[
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: AppTheme.alertRedBg,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.warning, color: AppTheme.alertRed, size: 16),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            "Скрытый штраф / коэффициент: +${currency.format(item.coeffSurchargeRub)} ₽",
                            style: const TextStyle(
                              fontSize: 11,
                              color: AppTheme.alertRed,
                              fontWeight: FontWeight.bold,
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
    );
  }
}
