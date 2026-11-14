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
  String _selectedCategoryFilter = 'Все начисления';

  void _showFilterSheet(BuildContext context) {
    final categories = ['Все начисления', 'Холодная вода (ХВС)', 'Отопление', 'Электроэнергия', 'Водоотведение'];

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setSheetState) => Container(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
          decoration: const BoxDecoration(
            color: AppColors.card,
            borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
          ),
          child: SafeArea(
            top: false,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 44,
                    height: 4,
                    decoration: BoxDecoration(
                      color: AppColors.border,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 18),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Параметры аналитики',
                      style: TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close_rounded, size: 20),
                      onPressed: () => Navigator.pop(ctx),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                const Text(
                  'Срез услуг',
                  style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 10),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: categories.map((cat) {
                    final isSel = _selectedCategoryFilter == cat;
                    return ChoiceChip(
                      label: Text(cat),
                      selected: isSel,
                      onSelected: (selected) {
                        if (selected) {
                          setSheetState(() => _selectedCategoryFilter = cat);
                          setState(() => _selectedCategoryFilter = cat);
                        }
                      },
                      selectedColor: AppColors.primaryLight,
                      labelStyle: TextStyle(
                        color: isSel ? AppColors.primary : AppColors.textPrimary,
                        fontWeight: isSel ? FontWeight.w700 : FontWeight.w500,
                        fontSize: 12,
                      ),
                      backgroundColor: AppColors.background,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                        side: BorderSide(
                          color: isSel ? AppColors.primary : AppColors.border,
                        ),
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 20),
                ElevatedButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('Применить'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AuditBloc, AuditState>(
      builder: (context, state) {
        final trends = state.monthlyTrends.isNotEmpty
            ? state.monthlyTrends
            : const [
                MonthlyTrendItem(monthLabel: 'Июн', amount: 4200),
                MonthlyTrendItem(monthLabel: 'Июл', amount: 4800),
                MonthlyTrendItem(monthLabel: 'Авг', amount: 5100),
                MonthlyTrendItem(monthLabel: 'Сен', amount: 5200),
                MonthlyTrendItem(monthLabel: 'Окт', amount: 5420),
                MonthlyTrendItem(monthLabel: 'Ноя', amount: 6890.5),
              ];

        final List<MonthlyTrendItem> visibleTrends;
        if (_selectedPeriodIndex == 0 && trends.length >= 3) {
          visibleTrends = trends.sublist(trends.length - 3);
        } else if (_selectedPeriodIndex == 1 && trends.length >= 6) {
          visibleTrends = trends.sublist(trends.length - 6);
        } else {
          visibleTrends = trends;
        }

        final deltaPct = state.report?.summary.deltaPct ?? 27.1;
        final deltaSign = deltaPct > 0 ? '+' : '';
        final isCriticalRise = deltaPct > 15;
        final deltaColor = isCriticalRise ? AppColors.critical : AppColors.success;

        return Scaffold(
          backgroundColor: AppColors.background,
          appBar: AppBar(
            title: const Text('Аналитика'),
            actions: [
              IconButton(
                icon: const Icon(Icons.tune_rounded, color: AppColors.textPrimary),
                tooltip: 'Параметры аналитики',
                onPressed: () => _showFilterSheet(context),
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
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Динамика общей суммы',
                          style: TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        if (_selectedCategoryFilter != 'Все начисления')
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: AppColors.primaryLight,
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              _selectedCategoryFilter,
                              style: const TextStyle(
                                color: AppColors.primary,
                                fontSize: 10,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '$deltaSign${deltaPct.toStringAsFixed(1).replaceAll('.', ',')}%',
                      style: TextStyle(
                        color: deltaColor,
                        fontSize: 22,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const Text(
                      'к предыдущему периоду',
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 12,
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Chart area
                    SizedBox(
                      height: 180,
                      child: CustomPaint(
                        size: const Size(double.infinity, 180),
                        painter: _TrendChartPainter(trends: visibleTrends),
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

              Row(
                children: [
                  Expanded(
                    child: _buildTrendBox(
                      emoji: '🔥',
                      title: 'Отопление',
                      changeText: '+38%',
                      subtitle: 'в ноябре',
                      color: AppColors.warning,
                      bgColor: AppColors.warningLight,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildTrendBox(
                      emoji: '💧',
                      title: 'Холодная вода',
                      changeText: '+127%',
                      subtitle: 'включен коэфф. 1,5!',
                      color: AppColors.critical,
                      bgColor: AppColors.criticalLight,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
            ],
          ),
        );
      },
    );
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
          color: isSelected ? AppColors.card : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.05),
                    blurRadius: 6,
                    offset: const Offset(0, 2),
                  ),
                ]
              : null,
        ),
        child: Center(
          child: Text(
            title,
            style: TextStyle(
              color: isSelected ? AppColors.primary : AppColors.textSecondary,
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
        color: bgColor,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(emoji, style: const TextStyle(fontSize: 20)),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            changeText,
            style: TextStyle(
              color: color,
              fontSize: 20,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            subtitle,
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

    final amounts = trends.map((t) => t.amount).toList();
    final minAmount = amounts.reduce((a, b) => a < b ? a : b) * 0.85;
    final maxAmount = amounts.reduce((a, b) => a > b ? a : b) * 1.15;
    final range = (maxAmount - minAmount) > 0 ? (maxAmount - minAmount) : 1.0;

    final bottomY = size.height - 24;
    const topY = 28.0;
    final availableHeight = bottomY - topY;

    // Draw horizontal dashed grid lines
    final gridPaint = Paint()
      ..color = AppColors.border
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    for (int i = 0; i < 3; i++) {
      final y = topY + (availableHeight / 2) * i;
      canvas.drawLine(Offset(0, y), Offset(size.width, y), gridPaint);
    }

    // Calculate (x, y) coordinates for each point
    final pointCount = trends.length;
    final stepX = pointCount > 1 ? size.width / (pointCount - 1) : size.width;
    final points = <Offset>[];

    for (int i = 0; i < pointCount; i++) {
      final x = i * stepX;
      final normalized = (trends[i].amount - minAmount) / range;
      final y = bottomY - (normalized * availableHeight);
      points.add(Offset(x, y));
    }

    // Draw month labels at the bottom
    for (int i = 0; i < pointCount; i++) {
      final textSpan = TextSpan(
        text: trends[i].monthLabel,
        style: const TextStyle(
          color: AppColors.textSecondary,
          fontSize: 11,
          fontWeight: FontWeight.w500,
        ),
      );
      final textPainter = TextPainter(
        text: textSpan,
        textDirection: TextDirection.ltr,
      )..layout();

      final labelX = points[i].dx - (textPainter.width / 2);
      textPainter.paint(canvas, Offset(labelX.clamp(0.0, size.width - textPainter.width), size.height - 14));
    }

    // Draw smooth cubic spline curve
    final path = Path();
    path.moveTo(points.first.dx, points.first.dy);

    for (int i = 0; i < points.length - 1; i++) {
      final p0 = points[i];
      final p1 = points[i + 1];
      final midX = (p0.dx + p1.dx) / 2;
      path.cubicTo(midX, p0.dy, midX, p1.dy, p1.dx, p1.dy);
    }

    // Draw gradient fill under the curve
    final fillPath = Path.from(path)
      ..lineTo(points.last.dx, bottomY)
      ..lineTo(points.first.dx, bottomY)
      ..close();

    final fillPaint = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [
          AppColors.primary.withValues(alpha: 0.22),
          AppColors.primary.withValues(alpha: 0.0),
        ],
      ).createShader(Rect.fromLTWH(0, 0, size.width, bottomY));

    canvas.drawPath(fillPath, fillPaint);

    // Draw curve stroke line
    final strokePaint = Paint()
      ..color = AppColors.primary
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round;

    canvas.drawPath(strokePath(path), strokePaint);

    // Draw peak point on last item
    final lastPoint = points.last;
    final dotPaint = Paint()..color = AppColors.primary;
    final whiteRingPaint = Paint()..color = Colors.white;

    canvas.drawCircle(lastPoint, 6, dotPaint);
    canvas.drawCircle(lastPoint, 3, whiteRingPaint);

    // Draw tooltip tag above peak with dynamic amount
    final lastAmount = trends.last.amount;
    final formattedAmount = lastAmount >= 1000
        ? '${lastAmount.toStringAsFixed(0).replaceAllMapped(RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'), (m) => '${m[1]} ')} ₽'
        : '${lastAmount.toStringAsFixed(2).replaceAll('.', ',')} ₽';

    final bubbleWidth = (formattedAmount.length * 8.5) + 16.0;
    final bubbleRect = RRect.fromRectAndRadius(
      Rect.fromCenter(center: Offset(lastPoint.dx - 10, lastPoint.dy - 24), width: bubbleWidth, height: 24),
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

    final tipTextSpan = TextSpan(
      text: formattedAmount,
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
    tipPainter.paint(
      canvas,
      Offset(lastPoint.dx - 10 - (tipPainter.width / 2), lastPoint.dy - 30),
    );
  }

  Path strokePath(Path path) => path;

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
