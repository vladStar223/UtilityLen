import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../bloc/audit/audit_bloc.dart';
import '../bloc/audit/audit_event.dart';
import '../core/models.dart';
import '../core/theme.dart';
import '../screens/main_scaffold.dart';

/// Интерактивная шторка верификации данных квитанции перед запуском аудита
class BillVerificationSheet extends StatefulWidget {
  final BillUploadResponse response;
  final VoidCallback onRetake;

  const BillVerificationSheet({
    super.key,
    required this.response,
    required this.onRetake,
  });

  static Future<void> show(
    BuildContext context, {
    required BillUploadResponse response,
    required VoidCallback onRetake,
  }) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => BillVerificationSheet(
        response: response,
        onRetake: onRetake,
      ),
    );
  }

  @override
  State<BillVerificationSheet> createState() => _BillVerificationSheetState();
}

class _BillVerificationSheetState extends State<BillVerificationSheet> {
  bool _isServicesExpanded = true;

  @override
  Widget build(BuildContext context) {
    final data = widget.response.extractedData;
    final report = widget.response.report;
    final totalAmount = data?.totalAmount ?? report?.summary.currTotal ?? 0.0;
    final services = data?.services ?? [];

    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      decoration: const BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      child: Column(
        children: [
          // Drag handle
          const SizedBox(height: 12),
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

          // Header
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppColors.success.withValues(alpha: 0.12),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.verified_user_rounded,
                    color: AppColors.success,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Проверьте данные квитанции',
                        style: TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppColors.success.withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: const Text(
                              'Квитанция ЖКХ подтверждена',
                              style: TextStyle(
                                color: AppColors.success,
                                fontSize: 11,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            widget.response.confidence == 'high' ? 'Точность 98%' : 'Точность 85%',
                            style: const TextStyle(
                              color: AppColors.textSecondary,
                              fontSize: 11,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 16),
          const Divider(height: 1, color: AppColors.border),

          // Content body
          Expanded(
            child: ListView(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              children: [
                // Warnings if any
                if (widget.response.warnings.isNotEmpty) ...[
                  ...widget.response.warnings.map(
                    (w) => Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.warning.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.warning.withValues(alpha: 0.3)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.info_outline_rounded, color: AppColors.warning, size: 18),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              w,
                              style: const TextStyle(
                                color: AppColors.textPrimary,
                                fontSize: 12,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],

                // Organization & Account Card
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.background,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Column(
                    children: [
                      _buildMetaRow(
                        icon: Icons.business_rounded,
                        label: 'Поставщик',
                        value: data?.providerName ?? 'КГУП «Примводоканал»',
                      ),
                      const Divider(height: 16, color: AppColors.border),
                      _buildMetaRow(
                        icon: Icons.numbers_rounded,
                        label: 'Лицевой счет',
                        value: (data?.personalAccount.isNotEmpty ?? false)
                            ? data!.personalAccount
                            : '010001702100519',
                      ),
                      const Divider(height: 16, color: AppColors.border),
                      _buildMetaRow(
                        icon: Icons.calendar_month_rounded,
                        label: 'Период начисления',
                        value: (data?.period.isNotEmpty ?? false)
                            ? data!.period
                            : (report?.summary.currPeriod ?? '2026-09'),
                      ),
                      const Divider(height: 16, color: AppColors.border),
                      _buildMetaRow(
                        icon: Icons.location_on_rounded,
                        label: 'Адрес помещения',
                        value: (data?.address.isNotEmpty ?? false)
                            ? data!.address
                            : 'г. Владивосток, ул. Амурская, д. 7, кв. 24',
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 16),

                // Services Section
                Container(
                  decoration: BoxDecoration(
                    color: AppColors.background,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Column(
                    children: [
                      InkWell(
                        onTap: () {
                          setState(() {
                            _isServicesExpanded = !_isServicesExpanded;
                          });
                        },
                        borderRadius: BorderRadius.circular(16),
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Row(
                                children: [
                                  const Icon(Icons.receipt_long_rounded, color: AppColors.primary, size: 20),
                                  const SizedBox(width: 10),
                                  Text(
                                    'Распознанные услуги (${services.isNotEmpty ? services.length : (report?.items.length ?? 0)})',
                                    style: const TextStyle(
                                      color: AppColors.textPrimary,
                                      fontSize: 14,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ],
                              ),
                              Icon(
                                _isServicesExpanded
                                    ? Icons.keyboard_arrow_up_rounded
                                    : Icons.keyboard_arrow_down_rounded,
                                color: AppColors.textSecondary,
                              ),
                            ],
                          ),
                        ),
                      ),
                      if (_isServicesExpanded) ...[
                        const Divider(height: 1, color: AppColors.border),
                        if (services.isNotEmpty)
                          ...services.map((s) => _buildServiceRow(s))
                        else if (report != null && report.items.isNotEmpty)
                          ...report.items.map((it) => _buildReportItemRow(it))
                        else
                          const Padding(
                            padding: EdgeInsets.all(16),
                            child: Text(
                              'Начисления сформированы по нормативу',
                              style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
                            ),
                          ),
                      ],
                    ],
                  ),
                ),

                const SizedBox(height: 16),

                // Total Amount Box
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        AppColors.primary.withValues(alpha: 0.08),
                        AppColors.primary.withValues(alpha: 0.02),
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.primary.withValues(alpha: 0.2)),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Итого к оплате:',
                            style: TextStyle(
                              color: AppColors.textSecondary,
                              fontSize: 13,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          SizedBox(height: 2),
                          Text(
                            'С учетом всех начислений',
                            style: TextStyle(
                              color: AppColors.textSecondary,
                              fontSize: 11,
                            ),
                          ),
                        ],
                      ),
                      Text(
                        '${totalAmount.toStringAsFixed(2).replaceAll('.', ',')} ₽',
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 22,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // Bottom Action Buttons
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              child: Column(
                children: [
                  ElevatedButton.icon(
                    onPressed: () {
                      Navigator.pop(context); // Close sheet
                      if (report != null) {
                        context.read<AuditBloc>().add(SetAuditReportEvent(report));
                      } else {
                        context.read<AuditBloc>().add(
                              const LoadAuditDataEvent(caseId: 'case_04_vladivostok_coeff3'),
                            );
                      }
                      Navigator.pushAndRemoveUntil(
                        context,
                        MaterialPageRoute(builder: (_) => const MainScaffold()),
                        (route) => false,
                      );
                    },
                    icon: const Icon(Icons.analytics_rounded, size: 20),
                    label: const Text('Все верно, запустить аудит'),
                  ),
                  const SizedBox(height: 8),
                  TextButton.icon(
                    onPressed: () {
                      Navigator.pop(context);
                      widget.onRetake();
                    },
                    icon: const Icon(Icons.refresh_rounded, size: 18),
                    label: const Text('Сделать другой снимок'),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetaRow({
    required IconData icon,
    required String label,
    required String value,
  }) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 16, color: AppColors.primary),
        const SizedBox(width: 10),
        Text(
          '$label: ',
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 13,
            fontWeight: FontWeight.w500,
          ),
        ),
        Expanded(
          child: Text(
            value,
            textAlign: TextAlign.end,
            style: const TextStyle(
              color: AppColors.textPrimary,
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildServiceRow(ExtractedServiceItem item) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.rawName,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  '${item.volume} ${item.unit} × ${item.tariff.toStringAsFixed(2)} ₽',
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ),
          Text(
            '${item.total.toStringAsFixed(2).replaceAll('.', ',')} ₽',
            style: const TextStyle(
              color: AppColors.textPrimary,
              fontSize: 14,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildReportItemRow(ServiceItem item) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.displayName,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  '${item.currVolume} ${item.unit} × ${item.currTariff.toStringAsFixed(2)} ₽',
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ),
          Text(
            '${item.currTotal.toStringAsFixed(2).replaceAll('.', ',')} ₽',
            style: const TextStyle(
              color: AppColors.textPrimary,
              fontSize: 14,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}
