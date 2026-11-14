import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../bloc/audit/audit_bloc.dart';
import '../bloc/audit/audit_event.dart';
import '../core/theme.dart';
import 'main_scaffold.dart';

/// Экран детального просмотра квитанции (из галереи, камеры или примеров)
class ReceiptViewerScreen extends StatelessWidget {
  final String? assetPath;
  final String? filePath;
  final String title;
  final String period;
  final double amount;
  final String provider;
  final String address;
  final String caseId;

  const ReceiptViewerScreen({
    super.key,
    this.assetPath,
    this.filePath,
    this.title = 'Квитанция на ЖКУ',
    this.period = 'Сентябрь 2026',
    this.amount = 1437.50,
    this.provider = 'КГУП «Приморский водоканал»',
    this.address = 'г. Владивосток, ул. Амурская, д. 7',
    this.caseId = 'case_04_vladivostok_coeff3',
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        elevation: 0,
        title: Text(
          title,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 17,
            fontWeight: FontWeight.w600,
          ),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.zoom_in_rounded, color: Colors.white70),
            tooltip: 'Масштабирование',
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Используйте жест двумя пальцами для масштабирования'),
                  duration: Duration(seconds: 2),
                ),
              );
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Interactive image viewer with pinch-to-zoom
          Expanded(
            child: InteractiveViewer(
              minScale: 0.8,
              maxScale: 4.0,
              clipBehavior: Clip.none,
              child: Center(
                child: _buildImage(),
              ),
            ),
          ),

          // Bottom card with extracted receipt data and Audit CTA
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
            decoration: BoxDecoration(
              color: AppColors.card,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.15),
                  blurRadius: 20,
                  offset: const Offset(0, -4),
                ),
              ],
            ),
            child: SafeArea(
              top: false,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppColors.success.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppColors.success.withValues(alpha: 0.3)),
                        ),
                        child: const Row(
                          children: [
                            Icon(Icons.check_circle_rounded, color: AppColors.success, size: 14),
                            SizedBox(width: 5),
                            Text(
                              'ГОСТ Р 56042-2014',
                              style: TextStyle(
                                color: AppColors.success,
                                fontSize: 11,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Text(
                        '${amount.toStringAsFixed(2).replaceAll('.', ',')} ₽',
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 20,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    provider,
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    address,
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 13,
                    ),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: () {
                      context.read<AuditBloc>().add(LoadAuditDataEvent(caseId: caseId));
                      Navigator.pushAndRemoveUntil(
                        context,
                        MaterialPageRoute(builder: (_) => const MainScaffold()),
                        (route) => false,
                      );
                    },
                    icon: const Icon(Icons.analytics_rounded, size: 20),
                    label: const Text('Запустить факторный аудит'),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildImage() {
    if (filePath != null && filePath!.isNotEmpty) {
      final file = File(filePath!);
      if (file.existsSync()) {
        return Image.file(
          file,
          fit: BoxFit.contain,
          errorBuilder: (_, __, ___) => _buildFallback(),
        );
      }
    }

    if (assetPath != null && assetPath!.isNotEmpty) {
      return Image.asset(
        assetPath!,
        fit: BoxFit.contain,
        errorBuilder: (_, __, ___) => _buildFallback(),
      );
    }

    return _buildFallback();
  }

  Widget _buildFallback() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: const Color(0xFF1E1E28),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.receipt_long_rounded, size: 80, color: AppColors.primaryLight),
          const SizedBox(height: 16),
          Text(
            title,
            style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Text(
            '$provider\n$address',
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.white70, fontSize: 13),
          ),
        ],
      ),
    );
  }
}
