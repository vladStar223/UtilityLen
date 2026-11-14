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
                    const Text(
                      '+27,1%',
                      style: TextStyle(
                        color: AppColors.success,
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

    const maxVal = 8000.0;
    const minVal = 2000.0;

    // Draw horizontal dashed grid lines (2k, 4k, 6k, 8k)
    final gridPaint = Paint()
      ..color = AppColors.border.withValues(alpha: 0.6)
      ..strokeWidth = 1;

    for (int i = 0; i <= 3; i++) {
      final y = height - (i * (height / 3));
      canvas.drawLine(Offset(25, y), Offset(width, y), gridPaint);

      // Y-axis label text
      final label = '${(minVal + (i * 2000)).toInt() ~/ 1000}k';
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
    final stepX = (width - 45) / (trends.length - 1);

    for (int i = 0; i < trends.length; i++) {
      final x = 35 + (i * stepX);
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

    // Draw gradient fill area
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

    // Draw peak point on last item
    final lastPoint = points.last;
    final dotPaint = Paint()..color = AppColors.primary;
    final whiteRingPaint = Paint()..color = Colors.white;

    canvas.drawCircle(lastPoint, 6, dotPaint);
    canvas.drawCircle(lastPoint, 3, whiteRingPaint);

    // Draw tooltip tag "6 890 ₽" above peak
    final bubbleRect = RRect.fromRectAndRadius(
      Rect.fromCenter(center: Offset(lastPoint.dx - 10, lastPoint.dy - 24), width: 68, height: 24),
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

    const tipTextSpan = TextSpan(
      text: '6 890 ₽',
      style: TextStyle(
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

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
