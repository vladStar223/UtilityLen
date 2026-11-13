import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../core/models.dart';
import '../core/theme.dart';
import '../widgets/anomaly_card.dart';
import '../widgets/factor_breakdown_widget.dart';
import '../widgets/kpi_card.dart';
import '../widgets/service_item_tile.dart';
import 'claim_screen.dart';
import 'chat_screen.dart';

class AnalysisScreen extends StatelessWidget {
  final ComparisonReport report;
  final String title;

  const AnalysisScreen({
    super.key,
    required this.report,
    required this.title,
  });

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat("#,##0.00", "ru_RU");
    final hasRedAnomaly = report.anomalies.any((a) => a.severity == "red");
    final totalImpact = report.anomalies.fold<double>(0.0, (sum, a) => sum + a.impactRub);
    const lawyerFeeSaved = 3500.0;
    final totalBenefit = totalImpact + lawyerFeeSaved;

    return Scaffold(
      appBar: AppBar(
        title: Text(title, overflow: TextOverflow.ellipsis),
        actions: [
          IconButton(
            icon: const Icon(Icons.share_outlined),
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text("Отчет готов для экспорта")),
              );
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Зеленый баннер ROI пользователя
            _buildRoiBanner(currency, totalImpact, lawyerFeeSaved, totalBenefit),
            const SizedBox(height: 16),

            // Верхние KPI карточки
            Row(
              children: [
                Expanded(
                  child: KpiCard(
                    title: "Было (${report.summary.prevPeriod})",
                    amount: report.summary.prevTotal,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: KpiCard(
                    title: "Стало (${report.summary.currPeriod})",
                    amount: report.summary.currTotal,
                    deltaAmount: report.summary.deltaAbs,
                    deltaPct: report.summary.deltaPct,
                    isAlert: hasRedAnomaly,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Список выявленных аномалий
            if (report.anomalies.isNotEmpty) ...[
              const Text(
                "🚨 Выявленные нарушения и риски",
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
              ),
              const SizedBox(height: 8),
              ...report.anomalies.map((a) {
                return AnomalyCard(
                  anomaly: a,
                  onDraftClaim: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => ClaimScreen(report: report, anomaly: a),
                      ),
                    );
                  },
                );
              }),
              const SizedBox(height: 12),
            ],

            // Факторный разбор изменения дельты
            FactorBreakdownWidget(breakdown: report.factorBreakdown),
            const SizedBox(height: 16),

            // Детализация по услугам квитанции
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  "📋 Строки квитанции",
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                Text(
                  "${report.items.length} позиций",
                  style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.5)),
                ),
              ],
            ),
            const SizedBox(height: 8),
            ...report.items.map((item) => ServiceItemTile(item: item)),
            const SizedBox(height: 80), // место под плавающие кнопки
          ],
        ),
      ),
      bottomSheet: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppTheme.darkBackground,
          border: Border(top: BorderSide(color: Colors.white.withOpacity(0.08))),
        ),
        child: Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => ChatScreen(comparisonId: report.comparisonId),
                    ),
                  );
                },
                icon: const Icon(Icons.support_agent_outlined),
                label: const Text("AI-Юрист"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryBlue,
                ),
              ),
            ),
            const SizedBox(width: 8),
            if (report.anomalies.isNotEmpty)
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => ClaimScreen(
                          report: report,
                          anomaly: report.anomalies.first,
                        ),
                      ),
                    );
                  },
                  icon: const Icon(Icons.assignment_outlined),
                  label: const Text("Претензия"),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.alertRed,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildRoiBanner(
    NumberFormat currency,
    double totalImpact,
    double lawyerFeeSaved,
    double totalBenefit,
  ) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF064E3B), Color(0xFF047857)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.successGreen.withOpacity(0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.savings_outlined, color: Colors.white, size: 22),
              const SizedBox(width: 8),
              const Text(
                "Ваша выгода от проверки:",
                style: TextStyle(fontSize: 14, color: Colors.white70, fontWeight: FontWeight.w500),
              ),
              const Spacer(),
              Text(
                "+${currency.format(totalBenefit)} ₽",
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            "• К возврату из-за нарушений УК: ${currency.format(totalImpact)} ₽\n"
            "• Сэкономлено на юристе: ${currency.format(lawyerFeeSaved)} ₽",
            style: const TextStyle(fontSize: 12, color: Colors.white, height: 1.4),
          ),
        ],
      ),
    );
  }
}
