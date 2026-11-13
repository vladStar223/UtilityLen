import 'package:flutter/material.dart';
import '../core/api_client.dart';
import '../core/models.dart';
import '../core/theme.dart';
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

  @override
  void initState() {
    super.initState();
    _loadCases();
  }

  Future<void> _loadCases() async {
    final list = await _apiClient.getCases();
    if (mounted) {
      setState(() => _cases = list);
    }
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
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: AppTheme.primaryBlue,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.qr_code_scanner, size: 18, color: Colors.white),
            ),
            const SizedBox(width: 8),
            const Text("UtilityLens Mobile"),
          ],
        ),
      ),
      body: Stack(
        children: [
          SingleChildScrollView(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Видоискатель сканера квитанции
                _buildScannerCard(),
                const SizedBox(height: 24),

                // Заголовок быстрых кейсов
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      "📍 Реальные квитанции (Владивосток)",
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    Text(
                      "Приморье",
                      style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.5)),
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                // Карточка топ-кейса с коэффициентом 3.0 (ул. Амурская)
                _buildTopVladivostokCaseCard(),
                const SizedBox(height: 12),

                // Список других кейсов
                ..._cases.where((c) => c.caseId != "case_04_vladivostok_coeff3").map((c) {
                  return _buildCaseCard(c);
                }),
              ],
            ),
          ),
          if (_isLoading)
            Container(
              color: Colors.black54,
              child: const Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    CircularProgressIndicator(color: AppTheme.accentCyan),
                    SizedBox(height: 16),
                    Text(
                      "Детерминированный факторный аудит...",
                      style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildScannerCard() {
    return Container(
      height: 240,
      decoration: BoxDecoration(
        color: AppTheme.darkCard,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppTheme.accentCyan.withOpacity(0.3), width: 1.5),
      ),
      child: Stack(
        children: [
          Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 90,
                  height: 90,
                  decoration: BoxDecoration(
                    color: AppTheme.primaryBlue.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppTheme.accentCyan.withOpacity(0.4)),
                  ),
                  child: const Icon(
                    Icons.document_scanner_outlined,
                    size: 48,
                    color: AppTheme.accentCyan,
                  ),
                ),
                const SizedBox(height: 16),
                const Text(
                  "Наведите камеру на QR-код ГОСТ",
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  "Или выберите файл квитанции из галереи",
                  style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.5)),
                ),
              ],
            ),
          ),
          Positioned(
            bottom: 12,
            left: 16,
            right: 16,
            child: Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => _analyzeCase(
                      "case_04_vladivostok_coeff3",
                      "Квитанция Водоканала (ул. Амурская)",
                    ),
                    icon: const Icon(Icons.camera_alt, size: 16),
                    label: const Text("Сканировать"),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  onPressed: () => _analyzeCase(
                    "case_04_vladivostok_coeff3",
                    "Квитанция из галереи",
                  ),
                  icon: const Icon(Icons.photo_library_outlined),
                  style: IconButton.styleFrom(
                    backgroundColor: Colors.white10,
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTopVladivostokCaseCard() {
    return Card(
      color: const Color(0xFF2D1826),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppTheme.alertRed, width: 1.5),
      ),
      child: InkWell(
        onTap: () => _analyzeCase(
          "case_04_vladivostok_coeff3",
          "Владивосток: ул. Амурская, д. 7 (Коэфф. 3.0)",
        ),
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppTheme.alertRed,
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: const Text(
                      "КРАСНАЯ ТРЕВОГА • ШТРАФ 3.0",
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                  ),
                  const Spacer(),
                  const Text(
                    "+686.56 ₽",
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.alertRed,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              const Text(
                "КГУП «Приморский водоканал» (ХВС)",
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white),
              ),
              const SizedBox(height: 4),
              Text(
                "г. Владивосток, ул. Амурская, д. 7, кв. 13 • Незаконное 3-кратное завышение норматива без акта",
                style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.7)),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCaseCard(CaseItem item) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: AppTheme.primaryBlue.withOpacity(0.15),
            borderRadius: BorderRadius.circular(10),
          ),
          child: const Icon(Icons.receipt_long, color: AppTheme.accentCyan, size: 20),
        ),
        title: Text(
          item.title,
          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Colors.white),
        ),
        subtitle: Text(
          item.description,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.5)),
        ),
        trailing: const Icon(Icons.chevron_right, color: Colors.white30),
        onTap: () => _analyzeCase(item.caseId, item.title),
      ),
    );
  }
}
