import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import '../core/models.dart';
import '../core/theme.dart';

/// Glassmorphic досудебная претензия screen with 1-click copy
class ClaimScreen extends StatelessWidget {
  final ComparisonReport report;
  final AnomalyItem anomaly;

  const ClaimScreen({
    super.key,
    required this.report,
    required this.anomaly,
  });

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat('#,##0.00', 'ru_RU');
    final impactStr = currency.format(anomaly.impactRub);
    final isCoeff3 = anomaly.code == 'APPLYING_COEFF_3_0';

    final recipient = isCoeff3
        ? 'Руководителю КГУП «Приморский водоканал»\nИНН 2503022413, г. Владивосток, ул. Некрасовская, 122'
        : 'Руководителю ООО «УК Комплексное обслуживание домов»\nг. Владивосток, ул. Башидзе, 12, оф. 17';

    final claimText = '''В: $recipient
ОТ: Завражнова Александра Владимировича
АДРЕС: г. Владивосток, ул. Амурская, д. 7, кв. 13
ЛИЦЕВОЙ СЧЕТ: 105-0713-8

ПРЕТЕНЗИЯ
о перерасчете необоснованно начисленной платы за ЖКУ

В платежном документе за расчетный период ${report.summary.currPeriod} г. по моему лицевому счету была начислена плата за услугу «${anomaly.serviceCategory.toUpperCase()}» с применением повышенного коэффициента в размере ${isCoeff3 ? '3.0' : '1.5'}, что привело к необоснованной переплате в размере $impactStr руб.

Согласно ч. 1 ст. 157 Жилищного кодекса РФ и Постановлению Правительства РФ № 354 (п. 60(1)), применение повышающего коэффициента допускается исключительно при наличии надлежащим образом оформленного двустороннего Акта обследования на предмет установления отсутствия технической возможности установки индивидуального прибора учета (ИПУ) либо Акта об отказе в допуске к прибору учета.

Указанный Акт составлен не был, требование о допуске в установленном законом порядке мне не направлялось. Таким образом, применение штрафного коэффициента является незаконным.

На основании изложенного, руководствуясь Законом РФ «О защите прав потребителей» и п. 155(1) Правил предоставления коммунальных услуг (ПП РФ № 354),

ТРЕБУЮ:
1. Произвести перерасчет размера платы за расчетный период ${report.summary.currPeriod} г., исключив повышающий коэффициент на сумму $impactStr руб.
2. Отразить скорректированную сумму перерасчета в следующем платежном документе.
3. В случае отказа оставляю за собой право обратиться с жалобой в Государственную жилищную инспекцию (ГЖИ Приморского края) и прокуратуру г. Владивостока.

Дата: ${DateFormat('dd.MM.yyyy').format(DateTime.now())} г.
Подпись: _______________ / Завражнов А.В.''';

    return Scaffold(
      body: Stack(
        children: [
          Container(decoration: const BoxDecoration(gradient: kDarkBgGradient)),

          SafeArea(
            child: Column(
              children: [
                // AppBar
                _buildAppBar(context, claimText),
                const SizedBox(height: 8),

                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // Recipient header
                        if (isCoeff3) _buildRecipientBadge(),
                        const SizedBox(height: 14),

                        // Legal validation badge
                        _buildLegalBadge(),
                        const SizedBox(height: 14),

                        // Claim document
                        _buildClaimDocument(claimText),
                        const SizedBox(height: 20),

                        // 1-click copy button (prominent)
                        _buildCopyButton(context, claimText),
                        const SizedBox(height: 10),

                        // PDF export (secondary)
                        _buildPdfButton(context),
                      ],
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

  Widget _buildAppBar(BuildContext context, String claimText) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
      child: Row(
        children: [
          GestureDetector(
            onTap: () => Navigator.of(context).pop(),
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: GlassDecoration.dark(radius: 10),
              child: const Icon(Icons.arrow_back_ios_new_rounded,
                  size: 16, color: AppColors.textSecondary),
            ),
          ),
          const SizedBox(width: 10),
          const Expanded(
            child: Text(
              'Досудебная претензия',
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w700,
                color: AppColors.textPrimary,
              ),
            ),
          ),
          // 1-click copy in AppBar too
          GestureDetector(
            onTap: () => _copyAndNotify(context, claimText),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
              decoration: BoxDecoration(
                color: AppColors.lavender.withOpacity(0.15),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.lavender.withOpacity(0.35)),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.copy_rounded, size: 15, color: AppColors.lavender),
                  SizedBox(width: 5),
                  Text(
                    '1 клик',
                    style: TextStyle(
                      fontSize: 12,
                      color: AppColors.lavender,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRecipientBadge() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppColors.alertRed.withOpacity(0.10),
            AppColors.alertRed.withOpacity(0.04),
          ],
        ),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.alertRed.withOpacity(0.30)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppColors.alertRedBg,
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.business_outlined,
                color: AppColors.alertRed, size: 18),
          ),
          const SizedBox(width: 10),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Адресат',
                  style: TextStyle(
                    fontSize: 11,
                    color: AppColors.textMuted,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Text(
                  'КГУП «Приморский водоканал»',
                  style: TextStyle(
                    fontSize: 13.5,
                    fontWeight: FontWeight.w700,
                    color: AppColors.alertRed,
                  ),
                ),
                Text(
                  'ИНН 2503022413, г. Владивосток',
                  style: TextStyle(
                    fontSize: 11.5,
                    color: AppColors.textMuted,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLegalBadge() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: GlassDecoration.dark(radius: 12),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(7),
            decoration: BoxDecoration(
              color: AppColors.successGreenBg,
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.verified_user_outlined,
                color: AppColors.successGreen, size: 17),
          ),
          const SizedBox(width: 10),
          const Expanded(
            child: Text(
              'Претензия сформирована автоматически на основании норм '
              'ПП РФ № 354 и ст. 157 ЖК РФ',
              style: TextStyle(
                fontSize: 12,
                color: AppColors.textSecondary,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildClaimDocument(String claimText) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF0E1626),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.glassBorder),
      ),
      child: SelectableText(
        claimText,
        style: const TextStyle(
          fontFamily: 'monospace',
          fontSize: 12.5,
          height: 1.6,
          color: AppColors.textPrimary,
          letterSpacing: 0.1,
        ),
      ),
    );
  }

  Widget _buildCopyButton(BuildContext context, String claimText) {
    return ElevatedButton.icon(
      onPressed: () => _copyAndNotify(context, claimText),
      icon: const Icon(Icons.copy_all_rounded, size: 18),
      label: const Text('Скопировать для отправки в КГУП «Приморский водоканал»'),
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.lavender,
        foregroundColor: AppColors.bgDeep,
        padding: const EdgeInsets.symmetric(vertical: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        textStyle: const TextStyle(
          fontSize: 13.5,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }

  Widget _buildPdfButton(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: () {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Экспорт PDF заявления формируется...')),
        );
      },
      icon: const Icon(Icons.picture_as_pdf_outlined, size: 18),
      label: const Text('Сохранить PDF бланк'),
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.textSecondary,
        side: const BorderSide(color: AppColors.glassBorder),
        padding: const EdgeInsets.symmetric(vertical: 13),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
    );
  }

  void _copyAndNotify(BuildContext context, String text) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text(
          '✅ Текст претензии скопирован — отправьте в чат УК или ГИС ЖКХ',
        ),
        backgroundColor: AppColors.successGreen,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        margin: const EdgeInsets.all(16),
      ),
    );
  }
}

