import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../bloc/audit/audit_bloc.dart';
import '../bloc/audit/audit_state.dart';
import '../core/models.dart';
import '../core/theme.dart';

class AnalyticsScreen extends StatefulWidget {
  const AnalyticsScreen({super.key});

  @override
  State<AnalyticsScreen> createState() => _AnalyticsScreenState();
}

class _AnalyticsScreenState extends State<AnalyticsScreen> {
  int _selectedPeriodIndex = 1; // 0: 3 мес, 1: 6 мес, 2: 12 мес

  int get _windowMonths {
    switch (_selectedPeriodIndex) {
      case 0:
        return 3;
      case 2:
        return 12;
      case 1:
      default:
        return 6;
    }
  }

  /// Группируем квитанции за один и тот же месяц (например, Водоканал + ДЭК за август),
  /// суммируя amount по совпадающему monthLabel. Порядок первой встречи сохраняется.
  List<MonthlyTrendItem> _aggregateByMonth(List<MonthlyTrendItem> items) {
    final order = <String>[];
    final sums = <String, double>{};
    for (final item in items) {
      final key = item.monthLabel;
      if (!sums.containsKey(key)) {
        order.add(key);
        sums[key] = 0.0;
      }
      sums[key] = (sums[key] ?? 0.0) + item.amount;
    }
    return [
      for (final key in order) MonthlyTrendItem(monthLabel: key, amount: sums[key] ?? 0.0),
    ];
  }

  /// Берём окно последних N месяцев из агрегированного списка.
  List<MonthlyTrendItem> _windowed(List<MonthlyTrendItem> items, int months) {
    if (items.length <= months) return items;
    return items.sublist(items.length - months);
  }

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AuditBloc, AuditState>(
      builder: (context, state) {
        final allTrends = _aggregateByMonth(state.monthlyTrends);
        final trends = _windowed(allTrends, _windowMonths);

        // Динамика общей суммы: сравнение последнего месяца с предыдущим.
        String deltaText;
        Color deltaColor;
        if (trends.length >= 2) {
          final last = trends.last.amount;
          final prev = trends[trends.length - 2].amount;
          final deltaPct = prev != 0 ? ((last - prev) / prev) * 100.0 : 0.0;
          final sign = deltaPct >= 0 ? '+' : '';
          deltaText = '$sign${deltaPct.toStringAsFixed(1).replaceAll('.', ',')}%';
          deltaColor = deltaPct >= 0 ? AppColors.critical : AppColors.success;
        } else {
          deltaText = '—';
          deltaColor = AppColors.textSecondary;
        }

        final trendBoxes = _buildTrendBoxes(state.report);

        return Scaffold(
          backgroundColor: AppColors.background,
          appBar: AppBar(
            title: const Text('Аналитика'),
            actions: [
              IconButton(
                icon: const Icon(Icons.tune_rounded, color: AppColors.textPrimary),
                onPressed: () {},
              ),
            ],
          ),
          body: ListView(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            children: [
              // Period selector tabs
              Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: AppColors.primaryLight.withValues(alpha: 0.5),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: _buildPeriodChip(
                        title: '3 мес',
                        isSelected: _selectedPeriodIndex == 0,
                        onTap: () => setState(() => _selectedPeriodIndex = 0),
                      ),
                    ),
                    Expanded(
                      child: _buildPeriodChip(
                        title: '6 мес',
                        isSelected: _selectedPeriodIndex == 1,
                        onTap: () => setState(() => _selectedPeriodIndex = 1),
                      ),
                    ),
                    Expanded(
                      child: _buildPeriodChip(
                        title: '12 мес',
                        isSelected: _selectedPeriodIndex == 2,
                        onTap: () => setState(() => _selectedPeriodIndex = 2),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Total Sum Dynamics Card with Chart
              Container(
                padding: const EdgeInsets.all(20),
                decoration: FintechDecorations.card(radius: 22),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Динамика общей суммы',
                      style: TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      deltaText,
                      style: TextStyle(
                        color: deltaColor,
                        fontSize: 22,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const Text(
                      'к предыдущему месяцу',
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 12,
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Chart area
                    SizedBox(
                      height: 180,
                      child: trends.isEmpty
                          ? const Center(
                              child: Text(
                                'Нет данных для отображения графика',
                                style: TextStyle(
                                  color: AppColors.textSecondary,
                                  fontSize: 13,
                                ),
                              ),
                            )
                          : CustomPaint(
                              size: const Size(double.infinity, 180),
                              painter: _TrendChartPainter(trends: trends),
                            ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Key Trends Section
              const Text(
                'Ключевые тенденции',
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 12),

              if (trendBoxes.isEmpty)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.card,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: const Text(
                    'Пока нет данных для выявления тенденций. Загрузите квитанцию, чтобы увидеть анализ.',
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 13,
                    ),
                  ),
                )
              else
                Row(
                  children: [
                    for (int i = 0; i < trendBoxes.length; i++) ...[
                      if (i > 0) const SizedBox(width: 12),
                      Expanded(child: trendBoxes[i]),
                    ],
                  ],
                ),
              const SizedBox(height: 16),
            ],
          ),
        );
      },
    );
  }

  /// Формирует до двух карточек ключевых тенденций из report.items:
  /// берём услуги с наибольшим приростом по deltaPct (положительным).
  List<Widget> _buildTrendBoxes(ComparisonReport? report) {
    if (report == null || report.items.isEmpty) return const [];

    final items = [...report.items]
      ..sort((a, b) => b.deltaPct.compareTo(a.deltaPct));

    final result = <Widget>[];
    for (final item in items.take(2)) {
      if (item.deltaPct <= 0) continue;

      final isCritical = item.deltaPct >= 100 || item.coeffSurchargeRub > 0;
      final color = isCritical ? AppColors.critical : AppColors.warning;
      final bgColor = isCritical ? AppColors.criticalLight : AppColors.warningLight;

      final emoji = _emojiForCategory(item.category);
      final changeText =
          '${item.deltaPct >= 0 ? '+' : ''}${item.deltaPct.toStringAsFixed(0)}%';
      final subtitle = item.coeffSurchargeRub > 0
          ? 'штрафной коэфф., +${item.coeffSurchargeRub.toStringAsFixed(0)} ₽'
          : 'рост начисления';

      result.add(_buildTrendBox(
        emoji: emoji,
        title: item.displayName,
        changeText: changeText,
        subtitle: subtitle,
        color: color,
        bgColor: bgColor,
      ));
    }
    return result;
  }

  String _emojiForCategory(String category) {
    switch (category) {
      case 'heating':
        return '🔥';
      case 'cold_water':
        return '💧';
      case 'hot_water':
        return '🚿';
      case 'electricity':
        return '⚡';
      case 'drainage':
        return '🌊';
      case 'gas':
        return '🔥';
      default:
        return '📊';
    }
  }

  Widget _buildPeriodChip({
    required String title,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 38,
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Center(
          child: Text(
            title,
            style: TextStyle(
              color: isSelected ? Colors.white : AppColors.textSecondary,
              fontSize: 13,
              fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTrendBox({
    required String emoji,
    required String title,
    required String changeText,
    required String subtitle,
    required Color color,
    required Color bgColor,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(emoji, style: const TextStyle(fontSize: 18)),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  title,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            changeText,
            style: TextStyle(
              color: color,
              fontSize: 22,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            subtitle,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 11,
            ),
          ),
        ],
      ),
    );
  }
}

class _TrendChartPainter extends CustomPainter {
  final List<MonthlyTrendItem> trends;

  _TrendChartPainter({required this.trends});

  @override
  void paint(Canvas canvas, Size size) {
    if (trends.isEmpty) return;

    final width = size.width;
    final height = size.height - 30; // Leave space for month labels

    // Динамический диапазон значений с padding 15%.
    double rawMin = trends.first.amount;
    double rawMax = trends.first.amount;
    for (final t in trends) {
      if (t.amount < rawMin) rawMin = t.amount;
      if (t.amount > rawMax) rawMax = t.amount;
    }

    double minVal;
    double maxVal;
    if (rawMax == rawMin) {
      // Всего одна точка или все одинаковые — задаём диапазон вокруг значения.
      final base = rawMax.abs() > 0 ? rawMax.abs() : 1.0;
      minVal = rawMin - base * 0.15;
      maxVal = rawMax + base * 0.15;
    } else {
      final span = rawMax - rawMin;
      final padding = span * 0.15;
      minVal = rawMin - padding;
      maxVal = rawMax + padding;
    }
    if (minVal < 0 && rawMin >= 0) minVal = 0; // не уходим ниже нуля, если данные неотрицательные
    if (maxVal == minVal) maxVal = minVal + 1; // страховка от деления на ноль

    // Draw horizontal dashed grid lines (4 деления: 0..3)
    final gridPaint = Paint()
      ..color = AppColors.border.withValues(alpha: 0.6)
      ..strokeWidth = 1;

    const gridDivisions = 3;
    for (int i = 0; i <= gridDivisions; i++) {
      final y = height - (i * (height / gridDivisions));
      canvas.drawLine(Offset(25, y), Offset(width, y), gridPaint);

      // Y-axis label text: значение, соответствующее делению.
      final value = minVal + (i * (maxVal - minVal) / gridDivisions);
      final label = _formatAxisLabel(value);
      final textSpan = TextSpan(
        text: label,
        style: const TextStyle(color: AppColors.textSecondary, fontSize: 10),
      );
      final textPainter = TextPainter(
        text: textSpan,
        textDirection: TextDirection.ltr,
      )..layout();
      textPainter.paint(canvas, Offset(0, y - 6));
    }

    // Compute point coordinates
    final points = <Offset>[];
    final stepX = trends.length > 1
        ? (width - 45) / (trends.length - 1)
        : 0.0;

    for (int i = 0; i < trends.length; i++) {
      final x = trends.length > 1 ? 35 + (i * stepX) : width / 2;
      final normalized = (trends[i].amount - minVal) / (maxVal - minVal);
      final y = height - (normalized * height);
      points.add(Offset(x, y));

      // Month label
      final textSpan = TextSpan(
        text: trends[i].monthLabel,
        style: TextStyle(
          color: i == trends.length - 1 ? AppColors.primary : AppColors.textSecondary,
          fontSize: 11,
          fontWeight: i == trends.length - 1 ? FontWeight.w700 : FontWeight.w500,
        ),
      );
      final textPainter = TextPainter(
        text: textSpan,
        textDirection: TextDirection.ltr,
      )..layout();
      textPainter.paint(canvas, Offset(x - (textPainter.width / 2), height + 10));
    }

    // Draw gradient fill area (нужно минимум 2 точки)
    if (points.length >= 2) {
      final path = Path();
      path.moveTo(points.first.dx, height);
      path.lineTo(points.first.dx, points.first.dy);

      for (int i = 0; i < points.length - 1; i++) {
        final p1 = points[i];
        final p2 = points[i + 1];
        final controlX = (p1.dx + p2.dx) / 2;
        path.cubicTo(controlX, p1.dy, controlX, p2.dy, p2.dx, p2.dy);
      }

      path.lineTo(points.last.dx, height);
      path.close();

      final fillPaint = Paint()
        ..shader = LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            AppColors.primary.withValues(alpha: 0.28),
            AppColors.primary.withValues(alpha: 0.0),
          ],
        ).createShader(Rect.fromLTWH(0, 0, width, height));

      canvas.drawPath(path, fillPaint);

      // Draw smooth curve stroke
      final strokePath = Path();
      strokePath.moveTo(points.first.dx, points.first.dy);
      for (int i = 0; i < points.length - 1; i++) {
        final p1 = points[i];
        final p2 = points[i + 1];
        final controlX = (p1.dx + p2.dx) / 2;
        strokePath.cubicTo(controlX, p1.dy, controlX, p2.dy, p2.dx, p2.dy);
      }

      final strokePaint = Paint()
        ..color = AppColors.primary
        ..strokeWidth = 3
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round;

      canvas.drawPath(strokePath, strokePaint);
    }

    // Draw peak point on last item
    final lastPoint = points.last;
    final dotPaint = Paint()..color = AppColors.primary;
    final whiteRingPaint = Paint()..color = Colors.white;

    canvas.drawCircle(lastPoint, 6, dotPaint);
    canvas.drawCircle(lastPoint, 3, whiteRingPaint);

    // Draw tooltip tag "{amount} ₽" above peak — реальное значение trends.last.amount.
    final tipText = _formatTooltip(trends.last.amount);
    final tipTextSpan = TextSpan(
      text: tipText,
      style: const TextStyle(
        color: AppColors.textPrimary,
        fontSize: 11,
        fontWeight: FontWeight.w800,
      ),
    );
    final tipPainter = TextPainter(
      text: tipTextSpan,
      textDirection: TextDirection.ltr,
    )..layout();

    final bubbleWidth = tipPainter.width + 16;
    final bubbleHeight = tipPainter.height + 10;
    final bubbleCenter = Offset(lastPoint.dx - 10, lastPoint.dy - bubbleHeight - 2);

    final bubbleRect = RRect.fromRectAndRadius(
      Rect.fromCenter(center: bubbleCenter, width: bubbleWidth, height: bubbleHeight),
      const Radius.circular(8),
    );
    canvas.drawRRect(bubbleRect, Paint()..color = AppColors.card);
    canvas.drawRRect(
      bubbleRect,
      Paint()
        ..color = AppColors.primary
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1,
    );

    tipPainter.paint(
      canvas,
      Offset(bubbleCenter.dx - (tipPainter.width / 2), bubbleCenter.dy - (tipPainter.height / 2)),
    );
  }

  String _formatAxisLabel(double value) {
    if (value.abs() >= 1000) {
      final k = value / 1000.0;
      // 5.4k, 12k и т.п.
      final formatted = k.abs() >= 10
          ? k.toStringAsFixed(0)
          : k.toStringAsFixed(1).replaceAll('.0', '');
      return '${formatted}k';
    }
    return value.toStringAsFixed(0);
  }

  String _formatTooltip(double value) {
    // 6 890 ₽ — пробелы как разделители тысяч.
    final intPart = value.round();
    final str = intPart.toString();
    final buf = StringBuffer();
    for (int i = 0; i < str.length; i++) {
      if (i > 0 && (str.length - i) % 3 == 0) buf.write(' ');
      buf.write(str[i]);
    }
    return '${buf.toString()} ₽';
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
