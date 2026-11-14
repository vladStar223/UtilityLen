import 'package:flutter/material.dart';
import '../core/permission_service.dart';
import '../core/theme.dart';
import '../screens/receipt_viewer_screen.dart';

/// Модальный диалог выбора квитанции: Галерея телефона или Камера
class ReceiptUploadBottomSheet extends StatelessWidget {
  const ReceiptUploadBottomSheet({super.key});

  static Future<void> show(BuildContext context) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const ReceiptUploadBottomSheet(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
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
            // Drag handle
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

            const Text(
              'Загрузить квитанцию',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 20,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 6),
            const Text(
              'Выберите способ добавления документа для факторного аудита начислений',
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 13,
                height: 1.3,
              ),
            ),
            const SizedBox(height: 20),

            // 1. Выбрать из галереи телефона
            _buildOptionTile(
              icon: Icons.photo_library_rounded,
              iconColor: AppColors.primary,
              title: 'Выбрать из галереи телефона',
              subtitle: 'Фотографии, скриншоты или сканы квитанций',
              onTap: () async {
                Navigator.pop(context);
                final picked = await PermissionService.pickReceiptFromGallery(context);
                if (picked != null && context.mounted) {
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
              },
            ),
            const SizedBox(height: 12),

            // 2. Сделать снимок камерой
            _buildOptionTile(
              icon: Icons.photo_camera_rounded,
              iconColor: AppColors.warning,
              title: 'Сфотографировать квитанцию',
              subtitle: 'Быстрый снимок бумажной квитанции камерой',
              onTap: () async {
                Navigator.pop(context);
                final picked = await PermissionService.takeReceiptPhoto(context);
                if (picked != null && context.mounted) {
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
              },
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }


  Widget _buildOptionTile({
    required IconData icon,
    required Color iconColor,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.border),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(18),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            child: Row(
              children: [
                Container(
                  width: 46,
                  height: 46,
                  decoration: BoxDecoration(
                    color: iconColor.withValues(alpha: 0.12),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(icon, color: iconColor, size: 24),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        subtitle,
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
                const Icon(
                  Icons.arrow_forward_ios_rounded,
                  color: AppColors.textSecondary,
                  size: 16,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
