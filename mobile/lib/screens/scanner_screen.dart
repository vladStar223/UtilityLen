import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../bloc/audit/audit_bloc.dart';
import '../bloc/audit/audit_event.dart';
import '../core/permission_service.dart';
import '../core/theme.dart';
import '../widgets/receipt_upload_bottom_sheet.dart';
import 'main_scaffold.dart';
import 'receipt_viewer_screen.dart';

/// Экран фотосъемки и сканирования квитанции ЖКХ (без QR-кодов, прямой захват документа)
class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen>
    with SingleTickerProviderStateMixin {
  bool _torchOn = false;
  bool _isProcessing = false;
  late AnimationController _animController;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2200),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  Future<void> _pickFromGallery() async {
    final picked = await PermissionService.pickReceiptFromGallery(context);
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
  }

  Future<void> _takePhoto() async {
    final picked = await PermissionService.takeReceiptPhoto(context);
    if (picked != null && mounted) {
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => ReceiptViewerScreen(
            filePath: picked.path,
            title: 'Снимок с камеры',
            provider: 'Сфотографированная квитанция',
            address: 'г. Владивосток',
          ),
        ),
      );
    }
  }

  Future<void> _simulateFastCapture() async {
    if (_isProcessing) return;
    setState(() {
      _isProcessing = true;
    });

    await Future.delayed(const Duration(milliseconds: 700));
    if (!mounted) return;

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
                    Icons.check_circle_rounded,
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
                        'Квитанция успешно захвачена!',
                        style: TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      Text(
                        'Данные распознаны · Приморский водоканал',
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
      _isProcessing = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Viewfinder background with document guide
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
                      Icons.description_rounded,
                      size: 160,
                      color: Colors.white24,
                    ),
                  ),
                ),
              ),
            ),
          ),

          // Main capture overlay
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
                          'Поместите квитанцию\nв рамку для съемки',
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

                // Document-shaped Viewfinder (A4 / Bill aspect ratio)
                GestureDetector(
                  onTap: _takePhoto,
                  child: Container(
                    width: 270,
                    height: 360,
                    decoration: BoxDecoration(
                      color: Colors.transparent,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(
                        color: AppColors.primaryLight.withValues(alpha: 0.7),
                        width: 2.0,
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

                        // Animated scanning frame highlight
                        AnimatedBuilder(
                          animation: _animController,
                          builder: (context, _) {
                            return Positioned(
                              top: 20 + _animController.value * 310,
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

                        // Center tap hint
                        Center(
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                            decoration: BoxDecoration(
                              color: Colors.black54,
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: Text(
                              _isProcessing ? 'Обработка...' : 'Нажмите для\nфотосъемки',
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

                // Bottom actions row: Gallery, Big Shutter, Samples
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      // Gallery button
                      Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            onPressed: _pickFromGallery,
                            iconSize: 28,
                            style: IconButton.styleFrom(
                              backgroundColor: const Color(0xFF232033),
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.all(12),
                            ),
                            icon: const Icon(Icons.photo_library_rounded),
                          ),
                          const SizedBox(height: 6),
                          const Text(
                            'Галерея',
                            style: TextStyle(color: Colors.white70, fontSize: 12),
                          ),
                        ],
                      ),

                      // Large Shutter Button (Сделать снимок)
                      GestureDetector(
                        onTap: _takePhoto,
                        child: Container(
                          width: 76,
                          height: 76,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: const LinearGradient(
                              colors: [AppColors.primary, AppColors.primaryGradientEnd],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                            ),
                            border: Border.all(color: Colors.white, width: 4),
                            boxShadow: [
                              BoxShadow(
                                color: AppColors.primary.withValues(alpha: 0.5),
                                blurRadius: 18,
                                spreadRadius: 3,
                              ),
                            ],
                          ),
                          child: const Center(
                            child: Icon(
                              Icons.camera_alt_rounded,
                              color: Colors.white,
                              size: 34,
                            ),
                          ),
                        ),
                      ),

                      // Samples button
                      Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            onPressed: () => ReceiptUploadBottomSheet.show(context),
                            iconSize: 28,
                            style: IconButton.styleFrom(
                              backgroundColor: const Color(0xFF232033),
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.all(12),
                            ),
                            icon: const Icon(Icons.folder_special_rounded),
                          ),
                          const SizedBox(height: 6),
                          const Text(
                            'Образцы',
                            style: TextStyle(color: Colors.white70, fontSize: 12),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),

                // Fast test hint button
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: TextButton.icon(
                    onPressed: _simulateFastCapture,
                    icon: const Icon(Icons.flash_auto_rounded, size: 16, color: Colors.white60),
                    label: const Text(
                      'Демо-захват квитанции Владивостока',
                      style: TextStyle(color: Colors.white60, fontSize: 12),
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
        width: 26,
        height: 26,
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
