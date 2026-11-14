import 'package:flutter/material.dart';
import '../core/models.dart';
import '../core/theme.dart';

class ServiceItemRow extends StatefulWidget {
  final ServiceItem item;
  final bool initialExpanded;

  const ServiceItemRow({
    super.key,
    required this.item,
    this.initialExpanded = false,
  });

  @override
  State<ServiceItemRow> createState() => _ServiceItemRowState();
}

class _ServiceItemRowState extends State<ServiceItemRow> {
  late bool _expanded;

  @override
  void initState() {
    super.initState();
    _expanded = widget.initialExpanded;
  }

  @override
  Widget build(BuildContext context) {
    final item = widget.item;
    final isIncrease = item.deltaPct > 0;
    final badgeColor = item.deltaPct > 50
        ? AppColors.critical
        : (item.deltaPct > 15 ? AppColors.warning : AppColors.primary);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: FintechDecorations.card(radius: 18),
      child: Column(
        children: [
          InkWell(
            onTap: () {
              setState(() {
                _expanded = !_expanded;
              });
            },
            borderRadius: BorderRadius.circular(18),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      _buildIcon(item.category),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          item.displayName,
                          style: const TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: badgeColor.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          '${isIncrease ? '+' : ''}${item.deltaPct.toStringAsFixed(1)}%',
                          style: TextStyle(
                            color: badgeColor,
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '${isIncrease ? '+' : ''}${item.deltaAbs.toStringAsFixed(2).replaceAll('.', ',')} ₽',
                        style: TextStyle(
                          color: item.deltaPct > 50 ? AppColors.critical : AppColors.textPrimary,
                          fontSize: 20,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      Icon(
                        _expanded ? Icons.keyboard_arrow_up_rounded : Icons.keyboard_arrow_down_rounded,
                        color: AppColors.textSecondary,
                        size: 22,
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Было: ${item.prevTotal.toStringAsFixed(0)} ₽ (${item.prevVolume} ${item.unit} · ${item.prevTariff} ₽)',
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 12,
                        ),
                      ),
                      Text(
                        'Стало: ${item.currTotal.toStringAsFixed(0)} ₽',
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          if (_expanded) ...[
            Container(
              margin: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.primaryLight.withValues(alpha: 0.4),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(
                    Icons.info_outline_rounded,
                    color: AppColors.primary,
                    size: 18,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Почему изменилась сумма?',
                          style: TextStyle(
                            color: AppColors.primary,
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 3),
                        Text(
                          item.plainExplanation.isNotEmpty
                              ? item.plainExplanation
                              : 'Расход изменился на ${(item.currVolume - item.prevVolume).toStringAsFixed(1)} ${item.unit}, тариф составил ${item.currTariff} ₽/${item.unit}.',
                          style: const TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 12,
                            height: 1.3,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildIcon(String category) {
    String emoji = '💧';
    if (category.contains('heat') || category.contains('отоп')) emoji = '🔥';
    if (category.contains('hot') || category.contains('гвс')) emoji = '♨️';
    if (category.contains('elect') || category.contains('свет') || category.contains('элек')) emoji = '⚡';
    if (category.contains('mgmt') || category.contains('ук') || category.contains('содерж')) emoji = '🏢';

    return Container(
      width: 32,
      height: 32,
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Center(
        child: Text(
          emoji,
          style: const TextStyle(fontSize: 16),
        ),
      ),
    );
  }
}
