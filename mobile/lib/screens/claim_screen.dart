import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:share_plus/share_plus.dart';
import '../core/theme.dart';

class ClaimScreen extends StatelessWidget {
  const ClaimScreen({super.key});

  static const String claimText = '''
В управляющую компанию ООО «УК Комфорт»
г. Владивосток, ул. Башидзе, д. 12
От: Петрова Алексея Владимировича
Адрес: г. Владивосток, ул. Амурская, д. 7, кв. 24
Лицевой счёт: 30KO233810-14

ПРЕТЕНЗИЯ
о перерасчёте платы за коммунальные услуги

В платежном документе за Ноябрь 2026 г. по услуге «Холодное водоснабжение» начислена плата в размере 735,54 ₽ с применением повышающего коэффициента 1.5.

С данным начислением не согласен по следующим основаниям:
В жилом помещении установлен и введен в эксплуатацию индивидуальный прибор учета (ИПУ) ХВС. Межповерочный интервал не истек, показания передаются своевременно. В соответствии со ст. 157 ЖК РФ и пунктом 60 Правил предоставления коммунальных услуг (утв. Постановлением Правительства РФ № 354), применение повышающего коэффициента при исправном ИПУ является незаконным.

На основании изложенного, ПРОШУ:
1. Произвести перерасчёт платы за холодное водоснабжение за Ноябрь 2026 г. с исключением повышающего коэффициента 1.5 на сумму 245,18 ₽.
2. Отразить скорректированную сумму перерасчета в следующем платежном документе.

Приложение: Копия платежного документа за Ноябрь 2026 г.

Дата: 14.11.2026 г.
Подпись: _________________ (Петров А.В.)
''';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Досудебная претензия'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, color: AppColors.textPrimary),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                children: [
                  // Success Ready Banner
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.successLight,
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(color: AppColors.success.withValues(alpha: 0.3)),
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 36,
                          height: 36,
                          decoration: BoxDecoration(
                            color: AppColors.success.withValues(alpha: 0.15),
                            shape: BoxShape.circle,
                          ),
                          child: const Center(
                            child: Icon(
                              Icons.check_rounded,
                              color: AppColors.success,
                              size: 22,
                            ),
                          ),
                        ),
                        const SizedBox(width: 14),
                        const Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Документ готов!',
                                style: TextStyle(
                                  color: AppColors.textPrimary,
                                  fontSize: 15,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              SizedBox(height: 2),
                              Text(
                                'Вы можете скопировать текст или скачать файл',
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
                  ),
                  const SizedBox(height: 16),

                  // Paper document card
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: AppColors.card,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppColors.border),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.04),
                          blurRadius: 16,
                          offset: const Offset(0, 6),
                        ),
                      ],
                    ),
                    child: const Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Center(
                          child: Text(
                            'ПРЕТЕНЗИЯ',
                            style: TextStyle(
                              color: AppColors.textPrimary,
                              fontSize: 16,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 1.2,
                            ),
                          ),
                        ),
                        SizedBox(height: 14),
                        Text(
                          'В управляющую компанию\nООО «УК Комфорт»',
                          style: TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            height: 1.3,
                          ),
                        ),
                        Divider(height: 24, color: AppColors.border),
                        Text(
                          'На основании ст. 157 ЖК РФ и ПП РФ № 354 прошу произвести перерасчёт начислений за ХВС в сумме 245,18 ₽.',
                          style: TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                            height: 1.4,
                          ),
                        ),
                        SizedBox(height: 14),
                        Text(
                          'Приложение: копия квитанции за Ноябрь 2026 г.',
                          style: TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 12,
                            fontStyle: FontStyle.italic,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            ),

            // Bottom Buttons
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              decoration: const BoxDecoration(
                color: AppColors.card,
                border: Border(top: BorderSide(color: AppColors.border)),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  ElevatedButton.icon(
                    onPressed: () {
                      Clipboard.setData(const ClipboardData(text: claimText));
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: const Text('Текст претензии скопирован в буфер обмена'),
                          backgroundColor: AppColors.primary,
                          behavior: SnackBarBehavior.floating,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                      );
                    },
                    icon: const Icon(Icons.copy_rounded, size: 20),
                    label: const Text('Скопировать текст'),
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () {
                            Share.share(
                              claimText,
                              subject: 'Досудебная претензия по перерасчету ЖКУ (ул. Амурская, 7)',
                            );
                          },
                          icon: const Icon(Icons.share_outlined, size: 18),
                          label: const Text('Поделиться'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: const Text('Файл претензии Pretension_Amurskaya7.pdf подготовлен'),
                                backgroundColor: AppColors.success,
                                behavior: SnackBarBehavior.floating,
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                              ),
                            );
                          },
                          icon: const Icon(Icons.download_rounded, size: 18),
                          label: const Text('Скачать PDF'),
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
    );
  }
}
