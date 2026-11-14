import 'package:flutter/material.dart';
import '../core/theme.dart';
import '../widgets/receipt_upload_bottom_sheet.dart';
import 'scanner_screen.dart';

class OnboardingScreen extends StatelessWidget {
  const OnboardingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.darkBackground,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: Column(
            children: [
              const Spacer(flex: 1),

              // Brand logo icon
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [AppColors.primary, AppColors.primaryGradientEnd],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(24),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withValues(alpha: 0.4),
                      blurRadius: 20,
                      offset: const Offset(0, 8),
                    ),
                  ],
                ),
                child: const Center(
                  child: Icon(
                    Icons.home_work_rounded,
                    color: Colors.white,
                    size: 42,
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Title & subtitle
              const Text(
                'UtilityLens',
                style: TextStyle(
                  color: AppColors.darkText,
                  fontSize: 32,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.5,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Аудит квитанций ЖКХ\nи AI-юрист в кармане',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: AppColors.darkTextSub,
                  fontSize: 16,
                  height: 1.3,
                  fontWeight: FontWeight.w400,
                ),
              ),
              const SizedBox(height: 36),

              // Bullets
              _buildBullet('Проверьте начисления'),
              const SizedBox(height: 14),
              _buildBullet('Найдите переплаты'),
              const SizedBox(height: 14),
              _buildBullet('Защитите свои права'),

              const Spacer(flex: 2),

              // Action buttons
              ElevatedButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const ScannerScreen()),
                  );
                },
                icon: const Icon(Icons.photo_camera_rounded, size: 20),
                label: const Text('Сканировать квитанцию'),
              ),
              const SizedBox(height: 12),

              OutlinedButton.icon(
                onPressed: () {
                  ReceiptUploadBottomSheet.show(context);
                },
                style: OutlinedButton.styleFrom(
                  backgroundColor: AppColors.darkSurface.withValues(alpha: 0.6),
                  foregroundColor: Colors.white,
                  side: BorderSide(color: Colors.white.withValues(alpha: 0.15)),
                ),
                icon: const Icon(Icons.upload_file_rounded, size: 20),
                label: const Text('Загрузить фото / PDF'),
              ),
              const SizedBox(height: 16),

              TextButton(
                onPressed: () {
                  ReceiptUploadBottomSheet.show(context);
                },
                child: const Text(
                  'Пример квитанции →',
                  style: TextStyle(
                    color: AppColors.primaryLight,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              const SizedBox(height: 10),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildBullet(String text) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 22,
          height: 22,
          decoration: BoxDecoration(
            color: AppColors.primary.withValues(alpha: 0.25),
            shape: BoxShape.circle,
          ),
          child: const Center(
            child: Icon(
              Icons.check_rounded,
              color: AppColors.primaryLight,
              size: 14,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Text(
          text,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 15,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
}
