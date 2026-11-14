import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../bloc/audit/audit_bloc.dart';
import '../bloc/audit/audit_event.dart';
import '../core/api_client.dart';
import '../core/models.dart';
import '../core/theme.dart';
import '../widgets/bill_verification_sheet.dart';
import 'main_scaffold.dart';

/// Экран детального просмотра квитанции (из галереи, камеры или примеров)
/// с реальной отправкой на валидацию в бэкенд и интерактивной верификацией
class ReceiptViewerScreen extends StatefulWidget {
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
  State<ReceiptViewerScreen> createState() => _ReceiptViewerScreenState();
}

class _ReceiptViewerScreenState extends State<ReceiptViewerScreen> {
  final ApiClient _apiClient = ApiClient();
  bool _isLoading = false;
  BillUploadResponse? _uploadResponse;
  String? _errorMessage;

  late String _displayProvider;
  late String _displayAddress;
  late double _displayAmount;
  late String _displayPeriod;

  @override
  void initState() {
    super.initState();
    _displayProvider = widget.provider;
    _displayAddress = widget.address;
    _displayAmount = widget.amount;
    _displayPeriod = widget.period;

    if (widget.filePath != null && widget.filePath!.isNotEmpty) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _analyzeFile(File(widget.filePath!));
      });
    } else {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _analyzeSampleCase(widget.caseId);
      });
    }
  }

  Future<void> _analyzeSampleCase(String caseId) async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    // Имитация реалистичной работы нейросети для записи видео и демо
    await Future.delayed(const Duration(milliseconds: 1100));
    if (!mounted) return;

    final sampleResponse = _apiClient.buildSampleResponse(caseId);

    setState(() {
      _isLoading = false;
      _uploadResponse = sampleResponse;
      final data = sampleResponse.extractedData;
      if (data != null) {
        _displayProvider = data.providerName;
        _displayAddress = data.address;
        _displayAmount = data.totalAmount;
        _displayPeriod = data.period;
      }
    });

    if (mounted) {
      BillVerificationSheet.show(
        context,
        response: sampleResponse,
        onRetake: () => Navigator.pop(context),
      );
    }
  }

  Future<void> _analyzeFile(File file) async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final response = await _apiClient.uploadBillFile(file);
      if (!mounted) return;

      setState(() {
        _isLoading = false;
        _uploadResponse = response;
        if (response.isValidBill) {
          final data = response.extractedData;
          if (data != null) {
            _displayProvider = data.providerName;
            _displayAddress = data.address;
            _displayAmount = data.totalAmount;
            _displayPeriod = data.period;
          }
        } else {
          _errorMessage = response.errorMessage ??
              'Загруженный файл не опознан как квитанция ЖКХ.';
        }
      });

      if (response.isValidBill && mounted) {
        // Показываем интерактивную шторку верификации данных
        BillVerificationSheet.show(
          context,
          response: response,
          onRetake: () => Navigator.pop(context),
        );
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isLoading = false;
        _errorMessage = 'Не удалось связаться с сервером. Проверьте соединение.';
      });
      _showConnectionErrorDialog();
    }
  }

  void _showConnectionErrorDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.wifi_off_rounded, color: AppColors.warning),
            SizedBox(width: 8),
            Text('Связь с сервером'),
          ],
        ),
        content: const Text(
          'Бэкенд временно недоступен или отсутствует подключение к сети.\n\n'
          'Вы можете повторить попытку или запустить аудит на эталонном образце Владивостока (ул. Амурская, д. 7).',
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              if (widget.filePath != null) {
                _analyzeFile(File(widget.filePath!));
              }
            },
            child: const Text('Повторить'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              _analyzeSampleCase(widget.caseId);
            },
            child: const Text('Демо-режим'),
          ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        elevation: 0,
        title: Text(
          widget.title,
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
              child: _buildBottomCardContent(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBottomCardContent() {
    // 1. Loading state
    if (_isLoading) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 16),
        child: Row(
          children: [
            const SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(
                strokeWidth: 2.5,
                color: AppColors.primary,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: const [
                  Text(
                    'Анализируем квитанцию на сервере...',
                    style: TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  SizedBox(height: 2),
                  Text(
                    'Проверяем реквизиты, поставщика и начисления',
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
      );
    }

    // 2. Error state: Document is NOT a utility bill
    if (_uploadResponse != null && !_uploadResponse!.isValidBill) {
      return Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.error.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.error.withValues(alpha: 0.3)),
            ),
            child: Row(
              children: [
                const Icon(Icons.cancel_rounded, color: AppColors.error, size: 22),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Документ не опознан как квитанция ЖКХ',
                        style: TextStyle(
                          color: AppColors.error,
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        _errorMessage ?? 'В файле не найдены начисления за коммунальные услуги.',
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.arrow_back_rounded, size: 18),
                  label: const Text('Назад'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.camera_alt_rounded, size: 18),
                  label: const Text('Переснять'),
                ),
              ),
            ],
          ),
        ],
      );
    }

    // 3. Normal / Valid state
    final isValid = _uploadResponse?.isValidBill ?? true;

    return Column(
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
              child: Row(
                children: [
                  const Icon(Icons.check_circle_rounded, color: AppColors.success, size: 14),
                  const SizedBox(width: 5),
                  Text(
                    isValid ? 'Документ проверен' : 'Квитанция из базы',
                    style: const TextStyle(
                      color: AppColors.success,
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),
            Text(
              '${_displayAmount.toStringAsFixed(2).replaceAll('.', ',')} ₽',
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
          _displayProvider,
          style: const TextStyle(
            color: AppColors.textPrimary,
            fontSize: 15,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 3),
        Text(
          '$_displayAddress · $_displayPeriod',
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 13,
          ),
        ),
        const SizedBox(height: 16),
        ElevatedButton.icon(
          onPressed: () {
            if (_uploadResponse != null && _uploadResponse!.isValidBill) {
              BillVerificationSheet.show(
                context,
                response: _uploadResponse!,
                onRetake: () => Navigator.pop(context),
              );
            } else {
              context.read<AuditBloc>().add(LoadAuditDataEvent(caseId: widget.caseId));
              Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(builder: (_) => const MainScaffold()),
                (route) => false,
              );
            }
          },
          icon: const Icon(Icons.analytics_rounded, size: 20),
          label: const Text('Проверить данные и запустить аудит'),
        ),
      ],
    );
  }

  Widget _buildImage() {
    if (widget.filePath != null && widget.filePath!.isNotEmpty) {
      final file = File(widget.filePath!);
      if (file.existsSync()) {
        return Image.file(
          file,
          fit: BoxFit.contain,
          errorBuilder: (_, __, ___) => _buildFallback(),
        );
      }
    }

    if (widget.assetPath != null && widget.assetPath!.isNotEmpty) {
      return Image.asset(
        widget.assetPath!,
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
            widget.title,
            style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Text(
            '$_displayProvider\n$_displayAddress',
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.white70, fontSize: 13),
          ),
        ],
      ),
    );
  }
}
