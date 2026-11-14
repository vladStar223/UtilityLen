import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../bloc/audit/audit_bloc.dart';
import '../bloc/audit/audit_state.dart';
import '../core/models.dart';
import '../core/theme.dart';
import '../widgets/receipt_upload_bottom_sheet.dart';
import 'bill_details_screen.dart';
import 'receipt_viewer_screen.dart';

class ReceiptsScreen extends StatelessWidget {
  const ReceiptsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AuditBloc, AuditState>(
      builder: (context, state) {
        final list = [
          const ReceiptHistoryItem(
            id: 'rec_nov_2026',
            period: 'Ноябрь 2026',
            totalAmount: 6890.50,
            providerName: 'Примводоканал · ДЭК',
            hasOverpayment: true,
            overpaymentAmount: 245.18,
          ),
          ...state.history,
        ];

        return Scaffold(
          backgroundColor: AppColors.background,
          appBar: AppBar(
            title: const Text('Квитанции'),
            actions: [
              IconButton(
                icon: const Icon(Icons.add_rounded, color: AppColors.primary, size: 28),
                tooltip: 'Загрузить квитанцию',
                onPressed: () {
                  ReceiptUploadBottomSheet.show(context);
                },
              ),
            ],
          ),
          body: ListView.separated(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            itemCount: list.length,
            separatorBuilder: (_, __) => const SizedBox(height: 12),
            itemBuilder: (ctx, i) {
              final item = list[i];
              return _buildReceiptCard(context, item, i);
            },
          ),
        );
      },
    );
  }

  Widget _buildReceiptCard(BuildContext context, ReceiptHistoryItem item, int index) {
    final assetName = (index % 2 == 0)
        ? 'assets/receipts/receipt_vladivostok_1.webp'
        : 'assets/receipts/receipt_vladivostok_2.webp';

    return Container(
      decoration: FintechDecorations.card(radius: 20),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () {
            _showReceiptActionDialog(context, item, assetName);
          },
          borderRadius: BorderRadius.circular(20),
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      item.period,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    Text(
                      '${item.totalAmount.toStringAsFixed(2).replaceAll('.', ',')} ₽',
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 18,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      item.providerName,
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 13,
                      ),
                    ),
                    if (item.hasOverpayment)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: AppColors.criticalLight,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          'Переплата +${item.overpaymentAmount.toStringAsFixed(0)} ₽',
                          style: const TextStyle(
                            color: AppColors.critical,
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _showReceiptActionDialog(BuildContext context, ReceiptHistoryItem item, String asset) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Container(
        padding: const EdgeInsets.all(24),
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
              Text(
                'Квитанция за ${item.period}',
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '${item.providerName} · ${item.totalAmount.toStringAsFixed(2)} ₽',
                style: const TextStyle(color: AppColors.textSecondary, fontSize: 13),
              ),
              const SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(ctx);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ReceiptViewerScreen(
                        assetPath: asset,
                        title: 'Квитанция ${item.period}',
                        amount: item.totalAmount,
                        provider: item.providerName,
                        address: 'г. Владивосток, ул. Амурская, д. 7',
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.image_search_rounded, size: 20),
                label: const Text('Просмотреть оригинал квитанции'),
              ),
              const SizedBox(height: 10),
              OutlinedButton.icon(
                onPressed: () {
                  Navigator.pop(ctx);
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const BillDetailsScreen()),
                  );
                },
                icon: const Icon(Icons.analytics_rounded, size: 20),
                label: const Text('Открыть детализацию начислений'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
