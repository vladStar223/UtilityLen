import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:image_picker/image_picker.dart';
import '../bloc/audit/audit_bloc.dart';
import '../bloc/audit/audit_event.dart';
import '../core/theme.dart';
import '../widgets/receipt_upload_bottom_sheet.dart';
import 'main_scaffold.dart';
import 'receipt_viewer_screen.dart';

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen>
    with SingleTickerProviderStateMixin {
  bool _torchOn = false;
  bool _isScanning = false;
  late AnimationController _animController;
  final ImagePicker _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  Future<void> _pickFromGallery() async {
    try {
      final picked = await _picker.pickImage(source: ImageSource.gallery);
      if (picked != null && mounted) {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => ReceiptViewerScreen(
              filePath: picked.path,
              title: 'Квитанция из галереи',
              provider: 'Квитанция ЖКХ (из галереи)',
              address: 'г. Владивосток',
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Ошибка доступа к галерее: $e')),
        );
      }
    }
  }

  Future<void> _takePhoto() async {
    try {
      final picked = await _picker.pickImage(source: ImageSource.camera);
      if (picked != null && mounted) {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => ReceiptViewerScreen(
              filePath: picked.path,
              title: 'Снимок с камеры',
              provider: 'Квитанция ЖКХ',
              address: 'г. Владивосток',
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Ошибка камеры: $e')),
        );
      }
    }
  }

  Future<void> _simulateLiveScan() async {
    if (_isScanning) return;
    setState(() {
      _isScanning = true;
    });

    // Realistic scanning delay
    await Future.delayed(const Duration(milliseconds: 900));

    if (!mounted) return;

    // Show recognition sheet
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isDismissible: false,
      builder: (ctx) => Container(
        padding: const EdgeInsets.all(24),
        decoration: const BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: AppColors.success.withValues(alpha: 0.15),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.qr_code_scanner_rounded,
                    color: AppColors.success,
                    size: 26,
                  ),
                ),
                const SizedBox(width: 14),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'QR-код успешно распознан!',
                        style: TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      Text(
                        'ГОСТ Р 56042-2014 · Приморский водоканал',
                        style: TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 18),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppColors.background,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.border),
              ),
              child: const Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Поставщик:', style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                      Text('КГУП «Примводоканал»', style: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w600, fontSize: 13)),
                    ],
                  ),
                  SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Адрес:', style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                      Text('ул. Амурская, д. 7', style: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w600, fontSize: 13)),
                    ],
                  ),
                  SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Сумма к оплате:', style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                      Text('1 437,50 ₽', style: TextStyle(color: AppColors.primary, fontWeight: FontWeight.w800, fontSize: 16)),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                context.read<AuditBloc>().add(const LoadAuditDataEvent(caseId: 'case_04_vladivostok_coeff3'));
                Navigator.pop(ctx);
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (_) => const MainScaffold()),
                );
              },
              child: const Text('Перейти к результатам аудита'),
            ),
          ],
        ),
      ),
    );

    setState(() {
      _isScanning = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Simulated live viewfinder background
          Positioned.fill(
            child: Container(
              color: const Color(0xFF13121A),
              child: Center(
                child: Opacity(
                  opacity: 0.28,
                  child: Image.asset(
                    'assets/receipts/receipt_vladivostok_1.webp',
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => const Icon(
                      Icons.document_scanner_rounded,
                      size: 160,
                      color: Colors.white24,
                    ),
                  ),
                ),
              ),
            ),
          ),

          // Main scanner overlay
          SafeArea(
            child: Column(
              children: [
                // Top control bar
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.arrow_back_rounded, color: Colors.white),
                        onPressed: () => Navigator.pop(context),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        decoration: BoxDecoration(
                          color: Colors.black54,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: Colors.white12),
                        ),
                        child: const Text(
                          'Наведите камеру\nна QR-код квитанции',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      IconButton(
                        icon: Icon(
                          _torchOn ? Icons.flash_on_rounded : Icons.flash_off_rounded,
                          color: _torchOn ? AppColors.warning : Colors.white,
                        ),
                        onPressed: () {
                          setState(() {
                            _torchOn = !_torchOn;
                          });
                        },
                      ),
                    ],
                  ),
                ),

                const Spacer(),

                // Center viewfinder with animated laser line
                GestureDetector(
                  onTap: _simulateLiveScan,
                  child: Container(
                    width: 260,
                    height: 260,
                    decoration: BoxDecoration(
                      color: Colors.transparent,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(
                        color: AppColors.primaryLight.withValues(alpha: 0.6),
                        width: 2.5,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: AppColors.primary.withValues(alpha: 0.35),
                          blurRadius: 28,
                          spreadRadius: 2,
                        ),
                      ],
                    ),
                    child: Stack(
                      children: [
                        // Corner brackets
                        _buildCorner(Alignment.topLeft, top: true, left: true),
                        _buildCorner(Alignment.topRight, top: true, right: true),
                        _buildCorner(Alignment.bottomLeft, bottom: true, left: true),
                        _buildCorner(Alignment.bottomRight, bottom: true, right: true),

                        // Animated laser scanning line
                        AnimatedBuilder(
                          animation: _animController,
                          builder: (context, _) {
                            return Positioned(
                              top: 20 + _animController.value * 210,
                              left: 12,
                              right: 12,
                              child: Container(
                                height: 2.5,
                                decoration: BoxDecoration(
                                  color: AppColors.primaryLight,
                                  boxShadow: [
                                    BoxShadow(
                                      color: AppColors.primary.withValues(alpha: 0.9),
                                      blurRadius: 10,
                                      spreadRadius: 2,
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),

                        // Center scan hint
                        Center(
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                            decoration: BoxDecoration(
                              color: Colors.black45,
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: Text(
                              _isScanning ? 'Распознавание...' : 'Нажмите для\nсканирования',
                              textAlign: TextAlign.center,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const Spacer(),

                // Bottom actions row: Camera / Gallery / Samples
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  child: Row(
                    children: [
                      // Camera button
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _takePhoto,
                          style: OutlinedButton.styleFrom(
                            backgroundColor: const Color(0xFF232033),
                            foregroundColor: Colors.white,
                            side: const BorderSide(color: Colors.white24),
                            padding: const EdgeInsets.symmetric(vertical: 14),
                          ),
                          icon: const Icon(Icons.camera_alt_rounded, size: 20),
                          label: const Text('Камера'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      // Gallery button
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _pickFromGallery,
                          style: OutlinedButton.styleFrom(
                            backgroundColor: const Color(0xFF232033),
                            foregroundColor: Colors.white,
                            side: const BorderSide(color: Colors.white24),
                            padding: const EdgeInsets.symmetric(vertical: 14),
                          ),
                          icon: const Icon(Icons.photo_library_rounded, size: 20),
                          label: const Text('Галерея'),
                        ),
                      ),
                    ],
                  ),
                ),

                // Upload photo / samples bottom card
                Padding(
                  padding: const EdgeInsets.only(left: 20, right: 20, bottom: 20),
                  child: Container(
                    decoration: BoxDecoration(
                      color: const Color(0xFF232033),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: Colors.white12),
                    ),
                    child: Material(
                      color: Colors.transparent,
                      child: InkWell(
                        onTap: () => ReceiptUploadBottomSheet.show(context),
                        borderRadius: BorderRadius.circular(20),
                        child: const Padding(
                          padding: EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                          child: Row(
                            children: [
                              Icon(
                                Icons.folder_special_rounded,
                                color: AppColors.primaryLight,
                                size: 24,
                              ),
                              SizedBox(width: 14),
                              Expanded(
                                child: Text(
                                  'Образцы квитанций Владивостока',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 14,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                              Icon(
                                Icons.chevron_right_rounded,
                                color: Colors.white54,
                                size: 22,
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCorner(
    Alignment alignment, {
    bool top = false,
    bool bottom = false,
    bool left = false,
    bool right = false,
  }) {
    return Align(
      alignment: alignment,
      child: Container(
        width: 24,
        height: 24,
        decoration: BoxDecoration(
          border: Border(
            top: top ? const BorderSide(color: Colors.white, width: 4) : BorderSide.none,
            bottom: bottom ? const BorderSide(color: Colors.white, width: 4) : BorderSide.none,
            left: left ? const BorderSide(color: Colors.white, width: 4) : BorderSide.none,
            right: right ? const BorderSide(color: Colors.white, width: 4) : BorderSide.none,
          ),
        ),
      ),
    );
  }
}
