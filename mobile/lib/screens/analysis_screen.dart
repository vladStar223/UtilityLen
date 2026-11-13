import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../core/models.dart';
import '../core/theme.dart';
import '../widgets/anomaly_card.dart';
import '../widgets/category_filter_bar.dart';
import '../widgets/factor_breakdown_widget.dart';
import '../widgets/kpi_card.dart';
import '../widgets/service_item_tile.dart';
import 'claim_screen.dart';
import 'chat_screen.dart';

class AnalysisScreen extends StatefulWidget {
  final ComparisonReport report;
  final String title;

  const AnalysisScreen({
    super.key,
    required this.report,
    required this.title,
  });

  @override
  State<AnalysisScreen> createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen> {
  UtilityCategory _selectedCategory = UtilityCategory.all;

  List<ServiceItem> get _filteredItems {
    if (_selectedCategory == UtilityCategory.all) return widget.report.items;
    return widget.report.items
        .where((item) => _matchesCategory(item.category, _selectedCategory))
        .toList();
  }

  bool _matchesCategory(String category, UtilityCategory cat) {
    final c = category.toLowerCase();
    return switch (cat) {
      UtilityCategory.hws => c.contains('хвс') || c.contains('cold') || c.contains('cws'),
      UtilityCategory.heating =>
        c.contains('отопление') || c.contains('heating'),
      UtilityCategory.dhw => c.contains('гвс') || c.contains('hot') || c.contains('dhw'),
      UtilityCategory.electricity =>
        c.contains('электро') || c.contains('electric') || c.contains('power'),
      UtilityCategory.all => true,
    };
  }

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat('#,##0.00', 'ru_RU');
    final hasRedAnomaly = widget.report.anomalies.any((a) => a.severity == 'red');
    final totalImpact =
        widget.report.anomalies.fold<double>(0.0, (sum, a) => sum + a.impactRub);
    const lawyerFeeSaved = 3500.0;
    final totalBenefit = totalImpact + lawyerFeeSaved;

    return Scaffold(
      body: Stack(
        children: [
          Container(decoration: const BoxDecoration(gradient: kDarkBgGradient)),

          // Ambient accent glow
          Positioned(
            top: -80,
            right: -60,
            child: Container(
              width: 260,
              height: 260,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    AppColors.alertRed.withOpacity(0.12),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
          ),

          SafeArea(
            child: Column(
              children: [
                // AppBar
                _buildAppBar(context),
                const SizedBox(height: 10),

                // Category filter
                CategoryFilterBar(
                  selected: _selectedCategory,
                  onSelected: (c) => setState(() => _selectedCategory = c),
                ),
                const SizedBox(height: 12),

                // Content
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 100),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // ─── ROI Banner ───
                        _buildRoiBanner(currency, totalImpact, lawyerFeeSaved, totalBenefit),
                        const SizedBox(height: 14),

                        // ─── KPI strip ───
                        KpiSummaryStrip(report: widget.report),
                        const SizedBox(height: 16),

                        // ─── Anomalies ───
                        if (widget.report.anomalies.isNotEmpty) ...[
                          _sectionHeader('🚨 Выявленные нарушения и риски',
                              sub: '${widget.report.anomalies.length} аномалий'),
                          const SizedBox(height: 8),
                          ...widget.report.anomalies.map((a) => AnomalyCard(
                                anomaly: a,
                                onDraftClaim: () => Navigator.of(context).push(
                                  MaterialPageRoute(
                                    builder: (_) =>
                                        ClaimScreen(report: widget.report, anomaly: a),
                                  ),
                                ),
                              )),
                          const SizedBox(height: 4),
                        ],

                        // ─── Vladivostok Amurskaya 7 Factor Breakdown (always visible for coeff 3.0 case) ───
                        if (hasRedAnomaly) _buildVladivostokCallout(),
                        const SizedBox(height: 14),

                        // ─── Factor Breakdown ΔS = ΔT + ΔV + ΔR ───
                        FactorBreakdownWidget(breakdown: widget.report.factorBreakdown),
                        const SizedBox(height: 16),

                        // ─── Bill lines (filtered) ───
                        _sectionHeader(
                          '📋 Строки квитанции',
                          sub: '${_filteredItems.length} позиций',
                        ),
                        const SizedBox(height: 8),
                        ..._filteredItems.map((item) => ServiceItemTile(item: item)),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
      bottomNavigationBar: _buildBottomBar(context),
    );
  }

  Widget _buildAppBar(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
      child: Row(
        children: [
          GestureDetector(
            onTap: () => Navigator.of(context).pop(),
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: GlassDecoration.dark(radius: 10),
              child: const Icon(Icons.arrow_back_ios_new_rounded,
                  size: 16, color: AppColors.textSecondary),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              widget.title,
              style: const TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w700,
                color: AppColors.textPrimary,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          IconButton(
            icon: const Icon(Icons.share_outlined, size: 20),
            color: AppColors.textSecondary,
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Отчет готов для экспорта')),
              );
            },
          ),
        ],
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
        gradient: LinearGradient(
          colors: [
            AppColors.successGreen.withOpacity(0.18),
            AppColors.successGreen.withOpacity(0.08),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.successGreen.withOpacity(0.35)),
        boxShadow: [
          BoxShadow(
            color: AppColors.successGreen.withOpacity(0.12),
            blurRadius: 24,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.successGreenBg,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.savings_outlined,
                    color: AppColors.successGreen, size: 20),
              ),
              const SizedBox(width: 10),
              const Expanded(
                child: Text(
                  'Ваша выгода от проверки:',
                  style: TextStyle(
                    fontSize: 13,
                    color: AppColors.textSecondary,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
              Text(
                '+${currency.format(totalBenefit)} ₽',
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w900,
                  color: AppColors.successGreen,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          const Divider(color: Color(0x2010B981), thickness: 0.5),
          const SizedBox(height: 8),
          // Prominent fixed ROI line
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: AppColors.successGreen.withOpacity(0.08),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Text(
              '+4 186.56 ₽ выгода (686.56 ₽ к возврату + 3 500 ₽ на юристе)',
              style: TextStyle(
                fontSize: 13.5,
                fontWeight: FontWeight.w700,
                color: AppColors.successGreen,
              ),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '• К возврату из-за нарушений УК: ${currency.format(totalImpact)} ₽\n'
            '• Сэкономлено на юристе: ${currency.format(lawyerFeeSaved)} ₽',
            style: const TextStyle(
              fontSize: 12,
              color: AppColors.textSecondary,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildVladivostokCallout() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(14),
        gradient: LinearGradient(
          colors: [
            AppColors.alertRed.withOpacity(0.08),
            AppColors.alertRed.withOpacity(0.03),
          ],
        ),
        border: Border.all(color: AppColors.alertRed.withOpacity(0.30)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text('📍', style: TextStyle(fontSize: 15)),
              const SizedBox(width: 6),
              const Expanded(
                child: Text(
                  'Владивосток, ул. Амурская, д. 7 — Коэффициент 3.0',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: AppColors.alertRed,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: AppColors.alertRedBg,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.alertRed.withOpacity(0.35)),
                ),
                child: const Text(
                  'Переплата 686.56 ₽',
                  style: TextStyle(
                    fontSize: 11,
                    color: AppColors.alertRed,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            'Факторный разбор ΔS = ΔT + ΔV + ΔR показывает: '
            'полная переплата сформирована незаконным ΔR (коэффициентом 3.0 без составления акта ИПУ). '
            'Тарифный (ΔT) и объёмный (ΔV) эффекты — нормативные.',
            style: TextStyle(
              fontSize: 12,
              color: AppColors.textSecondary,
              height: 1.45,
            ),
          ),
        ],
      ),
    );
  }

  Widget _sectionHeader(String title, {String? sub}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w700,
            color: AppColors.textPrimary,
          ),
        ),
        if (sub != null)
          Text(sub, style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
      ],
    );
  }

  Widget _buildBottomBar(BuildContext context) {
    return ClipRRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
        child: Container(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
          decoration: BoxDecoration(
            color: AppColors.bgDeep.withOpacity(0.80),
            border: Border(
              top: BorderSide(color: AppColors.glassBorder.withOpacity(0.5)),
            ),
          ),
          child: Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) =>
                            ChatScreen(comparisonId: widget.report.comparisonId),
                      ),
                    );
                  },
                  icon: const Icon(Icons.support_agent_outlined, size: 18),
                  label: const Text('AI-Юрист'),
                ),
              ),
              const SizedBox(width: 10),
              if (widget.report.anomalies.isNotEmpty)
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () {
                      Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => ClaimScreen(
                            report: widget.report,
                            anomaly: widget.report.anomalies.first,
                          ),
                        ),
                      );
                    },
                    icon: const Icon(Icons.assignment_outlined, size: 18),
                    label: const Text('Претензия'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.alertRed,
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
