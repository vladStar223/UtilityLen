import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../bloc/audit/audit_bloc.dart';
import '../bloc/audit/audit_state.dart';
import '../core/models.dart';
import '../core/theme.dart';
import '../widgets/service_item_row.dart';
import 'ai_chat_screen.dart';
import 'claim_screen.dart';

class BillDetailsScreen extends StatefulWidget {
  const BillDetailsScreen({super.key});

  @override
  State<BillDetailsScreen> createState() => _BillDetailsScreenState();
}

class _BillDetailsScreenState extends State<BillDetailsScreen> {
  int _selectedTab = 0; // 0: Услуги, 1: Перерасчёты

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AuditBloc, AuditState>(
      builder: (context, state) {
        final items = state.report?.items ?? _defaultServices();

        return Scaffold(
          backgroundColor: AppColors.background,
          appBar: AppBar(
            title: const Text('Детализация начислений'),
            leading: IconButton(
              icon: const Icon(Icons.arrow_back_rounded, color: AppColors.textPrimary),
              onPressed: () => Navigator.pop(context),
            ),
          ),
          body: Column(
            children: [
              // Segmented control
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                child: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: AppColors.primaryLight.withValues(alpha: 0.5),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: _buildTabButton(
                          title: 'Услуги',
                          isSelected: _selectedTab == 0,
                          onTap: () => setState(() => _selectedTab = 0),
                        ),
                      ),
                      Expanded(
                        child: _buildTabButton(
                          title: 'Перерасчёты',
                          isSelected: _selectedTab == 1,
                          onTap: () => setState(() => _selectedTab = 1),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // Content
              Expanded(
                child: _selectedTab == 0
                    ? ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                        itemCount: items.length,
                        itemBuilder: (ctx, i) {
                          return ServiceItemRow(
                            item: items[i],
                            initialExpanded: i == 0, // First item (ХВС) expanded by default
                          );
                        },
                      )
                    : _buildRecalculationsTab(),
              ),

              // Bottom action bar
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                decoration: BoxDecoration(
                  color: AppColors.card,
                  border: const Border(top: BorderSide(color: AppColors.border)),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.04),
                      blurRadius: 10,
                      offset: const Offset(0, -3),
                    ),
                  ],
                ),
                child: SafeArea(
                  top: false,
                  child: Row(
                    children: [
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(builder: (_) => const AiChatScreen()),
                            );
                          },
                          child: const Text('Спросить юриста'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: ElevatedButton(
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(builder: (_) => const ClaimScreen()),
                            );
                          },
                          child: const Text('Претензия'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildTabButton({
    required String title,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 38,
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Center(
          child: Text(
            title,
            style: TextStyle(
              color: isSelected ? Colors.white : AppColors.textSecondary,
              fontSize: 14,
              fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildRecalculationsTab() {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Container(
          padding: const EdgeInsets.all(18),
          decoration: FintechDecorations.card(radius: 18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      color: AppColors.warningLight,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Center(
                      child: Text('💧', style: TextStyle(fontSize: 16)),
                    ),
                  ),
                  const SizedBox(width: 10),
                  const Expanded(
                    child: Text(
                      'Перерасчёт по ХВС',
                      style: TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  const Text(
                    '+245,18 ₽',
                    style: TextStyle(
                      color: AppColors.critical,
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              const Text(
                'Основание: Код перерасчета №3 (доначисление по нормативу с повышающим коэффициентом 1.5). Требуется оспорить.',
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 13,
                  height: 1.3,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  List<ServiceItem> _defaultServices() {
    return [
      const ServiceItem(
        category: 'water_cold',
        displayName: 'Холодное водоснабжение',
        unit: 'м³',
        prevVolume: 6.0,
        currVolume: 8.2,
        prevTariff: 54.0,
        currTariff: 59.8,
        prevTotal: 324.0,
        currTotal: 735.54,
        deltaAbs: 411.54,
        deltaPct: 127.0,
        tariffDeltaRub: 47.56,
        volumeDeltaRub: 118.8,
        coeffSurchargeRub: 245.18,
        status: 'red',
        plainExplanation: 'Расход увеличился на 2,2 м³, также изменился тариф и начислен коэффициент 1.5.',
      ),
      const ServiceItem(
        category: 'heating',
        displayName: 'Отопление',
        unit: 'Гкал',
        prevVolume: 0.92,
        currVolume: 1.17,
        prevTariff: 2840.0,
        currTariff: 2840.0,
        prevTotal: 2612.8,
        currTotal: 3320.8,
        deltaAbs: 708.0,
        deltaPct: 27.1,
        tariffDeltaRub: 0.0,
        volumeDeltaRub: 708.0,
        coeffSurchargeRub: 0.0,
        status: 'yellow',
        plainExplanation: 'Сезонное увеличение тепловой нагрузки в связи с похолоданием.',
      ),
      const ServiceItem(
        category: 'water_hot',
        displayName: 'Горячая вода',
        unit: 'м³',
        prevVolume: 4.1,
        currVolume: 4.5,
        prevTariff: 215.0,
        currTariff: 215.0,
        prevTotal: 881.5,
        currTotal: 967.5,
        deltaAbs: 86.0,
        deltaPct: 9.0,
        tariffDeltaRub: 0.0,
        volumeDeltaRub: 86.0,
        coeffSurchargeRub: 0.0,
        status: 'green',
        plainExplanation: 'Незначительное увеличение объема потребления (+0.4 м³).',
      ),
      const ServiceItem(
        category: 'electricity',
        displayName: 'Электричество',
        unit: 'кВт·ч',
        prevVolume: 210.0,
        currVolume: 216.0,
        prevTariff: 4.85,
        currTariff: 4.85,
        prevTotal: 1018.5,
        currTotal: 1047.6,
        deltaAbs: 29.1,
        deltaPct: 3.0,
        tariffDeltaRub: 0.0,
        volumeDeltaRub: 29.1,
        coeffSurchargeRub: 0.0,
        status: 'green',
        plainExplanation: 'Потребление электроэнергии в пределах среднегодового уровня.',
      ),
      const ServiceItem(
        category: 'mgmt',
        displayName: 'Услуги УК и прочее',
        unit: 'м²',
        prevVolume: 44.6,
        currVolume: 44.6,
        prevTariff: 37.0,
        currTariff: 37.0,
        prevTotal: 1650.2,
        currTotal: 1650.2,
        deltaAbs: 0.0,
        deltaPct: 0.0,
        tariffDeltaRub: 0.0,
        volumeDeltaRub: 0.0,
        coeffSurchargeRub: 0.0,
        status: 'green',
        plainExplanation: 'Плата за содержание жилого помещения без изменений.',
      ),
    ];
  }
}
