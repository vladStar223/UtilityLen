import 'package:flutter/material.dart';
import '../core/permission_service.dart';
import '../core/theme.dart';
import '../screens/receipt_viewer_screen.dart';

/// Модальный диалог выбора квитанции: Галерея телефона, Камера или Образцы Владивостока
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
                final picked = await PermissionService.pickReceiptFromGallery(context);
                if (picked != null && context.mounted) {
                  Navigator.pop(context);
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
                final picked = await PermissionService.takeReceiptPhoto(context);
                if (picked != null && context.mounted) {
                  Navigator.pop(context);
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
            const SizedBox(height: 12),

            // 3. Образцы реальных квитанций Владивостока (ул. Амурская)
            _buildOptionTile(
              icon: Icons.folder_special_rounded,
              iconColor: AppColors.success,
              title: 'Образцы квитанций Владивостока',
              subtitle: 'Реальные квитанции КГУП «Примводоканал» с переплатой',
              onTap: () {
                Navigator.pop(context);
                _showSampleReceiptsPicker(context);
              },
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  void _showSampleReceiptsPicker(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Container(
        height: MediaQuery.of(ctx).size.height * 0.75,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
        decoration: const BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
        ),
        child: Column(
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
            const SizedBox(height: 16),
            const Text(
              'Образцы квитанций (Приморье)',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 18,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 4),
            const Text(
              'Выберите документ для детального просмотра и факторного аудита',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: ListView(
                children: [
                  _buildSampleCard(
                    context: ctx,
                    title: 'КГУП «Приморский водоканал»',
                    address: 'г. Владивосток, ул. Амурская, д. 7',
                    period: 'Сентябрь 2026',
                    sum: '1 437,50 ₽',
                    anomaly: 'Штрафной коэффициент 3.0 (+686,56 ₽)',
                    asset: 'assets/receipts/receipt_vladivostok_1.webp',
                    caseId: 'case_04_vladivostok_coeff3',
                  ),
                  const SizedBox(height: 12),
                  _buildSampleCard(
                    context: ctx,
                    title: 'ДЭК «Дальэнергосбыт» / ХВС',
                    address: 'г. Владивосток, ул. Амурская, д. 7',
                    period: 'Ноябрь 2026',
                    sum: '6 890,50 ₽',
                    anomaly: 'Штрафной коэффициент 1.5 (+245,18 ₽)',
                    asset: 'assets/receipts/receipt_vladivostok_2.webp',
                    caseId: 'case_02_coeff_15',
                  ),
                  const SizedBox(height: 12),
                  _buildSampleCard(
                    context: ctx,
                    title: 'АО «Дальневосточная РКЦ»',
                    address: 'г. Владивосток, Океанский проспект',
                    period: 'Октябрь 2026',
                    sum: '5 420,00 ₽',
                    anomaly: 'Начисления в норме (без штрафов)',
                    asset: 'assets/receipts/receipt_vladivostok_3.webp',
                    caseId: 'case_01_heating_spike',
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSampleCard({
    required BuildContext context,
    required String title,
    required String address,
    required String period,
    required String sum,
    required String anomaly,
    required String asset,
    required String caseId,
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
          onTap: () {
            Navigator.pop(context);
            final cleanSum = sum.replaceAll(' ', '').replaceAll(',', '.').replaceAll(RegExp(r'[^\d.]'), '');
            final parsedAmount = double.tryParse(cleanSum) ?? 1437.50;
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => ReceiptViewerScreen(
                  assetPath: asset,
                  title: title,
                  period: period,
                  amount: parsedAmount,
                  provider: title,
                  address: address,
                  caseId: caseId,
                ),
              ),
            );
          },
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Row(
              children: [
                ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: Image.asset(
                    asset,
                    width: 60,
                    height: 70,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => Container(
                      width: 60,
                      height: 70,
                      color: AppColors.primaryLight,
                      child: const Icon(Icons.receipt_long_rounded, color: AppColors.primary),
                    ),
                  ),
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
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '$period · $sum',
                        style: const TextStyle(
                          color: AppColors.primary,
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        anomaly,
                        style: const TextStyle(
                          color: AppColors.critical,
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right_rounded, color: AppColors.textSecondary),
              ],
            ),
          ),
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
