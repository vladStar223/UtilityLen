import 'dart:ui';
import 'package:flutter/material.dart';
import '../core/api_client.dart';
import '../core/models.dart';
import '../core/theme.dart';
import '../widgets/category_filter_bar.dart';
import 'analysis_screen.dart';

class HomeScannerScreen extends StatefulWidget {
  const HomeScannerScreen({super.key});

  @override
  State<HomeScannerScreen> createState() => _HomeScannerScreenState();
}

class _HomeScannerScreenState extends State<HomeScannerScreen> {
  final ApiClient _apiClient = ApiClient();
  List<CaseItem> _cases = [];
  bool _isLoading = false;
  UtilityCategory _selectedCategory = UtilityCategory.all;

  @override
  void initState() {
    super.initState();
    _loadCases();
  }

  Future<void> _loadCases() async {
    final list = await _apiClient.getCases();
    if (mounted) setState(() => _cases = list);
  }

  void _analyzeCase(String caseId, String caseTitle) async {
    setState(() => _isLoading = true);
    try {
      final report = await _apiClient.compareBills(caseId: caseId);
      if (mounted) {
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => AnalysisScreen(report: report, title: caseTitle),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          // Background gradient
          Container(
            decoration: const BoxDecoration(gradient: kDarkBgGradient),
          ),

          // Ambient glow top
          Positioned(
            top: -100,
            left: MediaQuery.of(context).size.width * 0.2,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    AppColors.violet.withOpacity(0.18),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
          ),

          SafeArea(
            child: Column(
              children: [
                // Custom AppBar
                _buildAppBar(),
                const SizedBox(height: 8),

                // Category filter carousel
                CategoryFilterBar(
                  selected: _selectedCategory,
                  onSelected: (cat) => setState(() => _selectedCategory = cat),
                ),
                const SizedBox(height: 16),

                // Scrollable body
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 32),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // Scanner card
                        _buildScannerCard(),
                        const SizedBox(height: 20),

                        // Section header
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text(
                              '📍 Реальные квитанции (Владивосток)',
                              style: TextStyle(
                                fontSize: 15,
                                fontWeight: FontWeight.w700,
                                color: AppColors.textPrimary,
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: AppColors.glassFill,
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(color: AppColors.glassBorder),
                              ),
                              child: const Text(
                                'Приморье',
                                style: TextStyle(
                                  fontSize: 11,
                                  color: AppColors.textMuted,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),

                        // Top Vladivostok Amurskaya 7 featured card
                        _buildVladivostokHeroCard(),
                        const SizedBox(height: 10),

                        // ROI teaser banner
                        _buildRoiTeaserBanner(),
                        const SizedBox(height: 14),

                        // Other cases
                        ..._cases
                            .where((c) => c.caseId != 'case_04_vladivostok_coeff3')
                            .map((c) => _buildCaseCard(c)),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Loading overlay
          if (_isLoading)
            BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 4, sigmaY: 4),
              child: Container(
                color: Colors.black.withOpacity(0.5),
                child: const Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      CircularProgressIndicator(
                        color: AppColors.lavender,
                        strokeWidth: 3,
                      ),
                      SizedBox(height: 18),
                      Text(
                        'Детерминированный факторный аудит...',
                        style: TextStyle(
                          color: AppColors.textPrimary,
                          fontWeight: FontWeight.w600,
                          fontSize: 15,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildAppBar() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
      child: Row(
        children: [
          // Logo pill
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: GlassDecoration.darkAccent(radius: 12),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.qr_code_scanner, size: 18, color: AppColors.lavender),
                SizedBox(width: 6),
                Text(
                  'UtilityLens',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.3,
                  ),
                ),
              ],
            ),
          ),
          const Spacer(),
          // Status pill
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: AppColors.successGreenBg,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.successGreen.withOpacity(0.35)),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.shield_outlined, size: 13, color: AppColors.successGreen),
                SizedBox(width: 4),
                Text(
                  'Владивосток',
                  style: TextStyle(
                    fontSize: 11,
                    color: AppColors.successGreen,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildScannerCard() {
    return Container(
      height: 230,
      decoration: GlassDecoration.dark(
        radius: 20,
        extraShadows: [
          BoxShadow(
            color: AppColors.violet.withOpacity(0.12),
            blurRadius: 32,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Stack(
        children: [
          // Corner scan guides
          ..._buildScanCorners(),
          Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    color: AppColors.lavender.withOpacity(0.10),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.lavender.withOpacity(0.35)),
                  ),
                  child: const Icon(
                    Icons.document_scanner_outlined,
                    size: 42,
                    color: AppColors.lavender,
                  ),
                ),
                const SizedBox(height: 14),
                const Text(
                  'Наведите камеру на QR-код ГОСТ',
                  style: TextStyle(
                    fontSize: 14.5,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Или выберите файл квитанции из галереи',
                  style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                ),
              ],
            ),
          ),
          Positioned(
            bottom: 14,
            left: 14,
            right: 14,
            child: Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => _analyzeCase(
                      'case_04_vladivostok_coeff3',
                      'Квитанция Водоканала (ул. Амурская)',
                    ),
                    icon: const Icon(Icons.camera_alt, size: 15),
                    label: const Text('Сканировать'),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  onPressed: () => _analyzeCase(
                    'case_04_vladivostok_coeff3',
                    'Квитанция из галереи',
                  ),
                  icon: const Icon(Icons.photo_library_outlined),
                  style: IconButton.styleFrom(
                    backgroundColor: AppColors.glassFill,
                    foregroundColor: AppColors.textSecondary,
                    side: const BorderSide(color: AppColors.glassBorder),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildScanCorners() {
    const color = AppColors.lavender;
    const thickness = 2.5;
    const size = 22.0;
    final corners = [
      [0.0, 0.0, true, true],
      [0.0, 1.0, true, false],
      [1.0, 0.0, false, true],
      [1.0, 1.0, false, false],
    ];
    return corners.map((c) {
      final top = c[0] == 0 ? 12.0 : null;
      final bottom = c[1] == 0 ? 12.0 : null;
      final left = c[2] as bool ? 12.0 : null;
      final right = c[3] as bool ? 12.0 : null;
      return Positioned(
        top: top,
        bottom: bottom,
        left: left,
        right: right,
        child: SizedBox(
          width: size,
          height: size,
          child: CustomPaint(
            painter: _CornerPainter(
              topLeft: c[2] as bool && c[0] == 0,
              topRight: !(c[2] as bool) && c[0] == 0,
              bottomLeft: c[2] as bool && c[1] == 0,
              bottomRight: !(c[2] as bool) && c[1] == 0,
              color: color,
              thickness: thickness,
            ),
          ),
        ),
      );
    }).toList();
  }

  Widget _buildVladivostokHeroCard() {
    return GestureDetector(
      onTap: () => _analyzeCase(
        'case_04_vladivostok_coeff3',
        'Владивосток: ул. Амурская, д. 7 (Коэфф. 3.0)',
      ),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(18),
          gradient: const LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF3D0A0A), Color(0xFF2D1826)],
          ),
          border: Border.all(color: AppColors.alertRed.withOpacity(0.55), width: 1.5),
          boxShadow: [
            BoxShadow(
              color: AppColors.alertRed.withOpacity(0.18),
              blurRadius: 24,
              offset: const Offset(0, 6),
            ),
          ],
        ),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                // Red alarm badge
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.alertRed,
                    borderRadius: BorderRadius.circular(7),
                  ),
                  child: const Text(
                    '🚨 КРАСНАЯ ТРЕВОГА • ШТРАФ 3.0',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
                const Spacer(),
                const Text(
                  '+686.56 ₽',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w900,
                    color: AppColors.alertRed,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            const Text(
              'КГУП «Приморский водоканал» (💧 ХВС)',
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w700,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              'г. Владивосток, ул. Амурская, д. 7, кв. 13',
              style: TextStyle(
                fontSize: 12,
                color: AppColors.textSecondary.withOpacity(0.85),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Незаконное 3-кратное завышение норматива без акта ИПУ',
              style: TextStyle(
                fontSize: 12,
                color: Colors.white.withOpacity(0.65),
              ),
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                const Icon(Icons.arrow_forward_ios_rounded,
                    size: 12, color: AppColors.alertRed),
                const SizedBox(width: 4),
                Text(
                  'Нажмите для полного факторного разбора (ΔS = ΔT + ΔV + ΔR)',
                  style: TextStyle(
                    fontSize: 11,
                    color: AppColors.alertRed.withOpacity(0.80),
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRoiTeaserBanner() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppColors.successGreen.withOpacity(0.12),
            AppColors.successGreen.withOpacity(0.06),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.successGreen.withOpacity(0.30)),
      ),
      child: Row(
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
          const SizedBox(width: 12),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '+4 186.56 ₽ выгода',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                    color: AppColors.successGreen,
                  ),
                ),
                Text(
                  '686.56 ₽ к возврату + 3 500 ₽ на юристе',
                  style: TextStyle(
                    fontSize: 11.5,
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          const Icon(Icons.chevron_right_rounded,
              color: AppColors.successGreen, size: 20),
        ],
      ),
    );
  }

  Widget _buildCaseCard(CaseItem item) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: GlassDecoration.dark(radius: 14),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: AppColors.lavender.withOpacity(0.12),
            borderRadius: BorderRadius.circular(10),
          ),
          child: const Icon(Icons.receipt_long_rounded,
              color: AppColors.lavender, size: 20),
        ),
        title: Text(
          item.title,
          style: const TextStyle(
            fontSize: 13.5,
            fontWeight: FontWeight.w600,
            color: AppColors.textPrimary,
          ),
        ),
        subtitle: Text(
          item.description,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
        ),
        trailing: const Icon(Icons.chevron_right_rounded, color: AppColors.glassBorder),
        onTap: () => _analyzeCase(item.caseId, item.title),
      ),
    );
  }
}

/// Custom painter for scanner-corner decorations
class _CornerPainter extends CustomPainter {
  final bool topLeft, topRight, bottomLeft, bottomRight;
  final Color color;
  final double thickness;

  const _CornerPainter({
    required this.topLeft,
    required this.topRight,
    required this.bottomLeft,
    required this.bottomRight,
    required this.color,
    required this.thickness,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = thickness
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    const len = 14.0;
    if (topLeft) {
      canvas.drawLine(Offset.zero, const Offset(len, 0), paint);
      canvas.drawLine(Offset.zero, const Offset(0, len), paint);
    }
    if (topRight) {
      canvas.drawLine(Offset(size.width, 0), Offset(size.width - len, 0), paint);
      canvas.drawLine(Offset(size.width, 0), Offset(size.width, len), paint);
    }
    if (bottomLeft) {
      canvas.drawLine(Offset(0, size.height), Offset(len, size.height), paint);
      canvas.drawLine(Offset(0, size.height), Offset(0, size.height - len), paint);
    }
    if (bottomRight) {
      canvas.drawLine(
          Offset(size.width, size.height), Offset(size.width - len, size.height), paint);
      canvas.drawLine(
          Offset(size.width, size.height), Offset(size.width, size.height - len), paint);
    }
  }

  @override
  bool shouldRepaint(_CornerPainter old) => false;
}
