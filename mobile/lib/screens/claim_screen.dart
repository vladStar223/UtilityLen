import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import '../core/models.dart';
import '../core/theme.dart';

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
    final currency = NumberFormat("#,##0.00", "ru_RU");
    final impactStr = currency.format(anomaly.impactRub);
    final isCoeff3 = anomaly.code == "APPLYING_COEFF_3_0";

    // Формирование юридически выверенного текста досудебной претензии
    final recipient = isCoeff3
        ? "Руководителю КГУП «Приморский водоканал»\nИНН 2503022413, г. Владивосток, ул. Некрасовская, 122"
        : "Руководителю ООО «УК Комплексное обслуживание домов»\nг. Владивосток, ул. Башидзе, 12, оф. 17";

    final claimText = """
В: $recipient
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
Подпись: _______________ / Завражнов А.В.
""";

    return Scaffold(
      appBar: AppBar(
        title: const Text("Досудебная претензия"),
        actions: [
          IconButton(
            icon: const Icon(Icons.copy_rounded),
            tooltip: "Копировать",
            onPressed: () {
              Clipboard.setData(ClipboardData(text: claimText));
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text("Текст претензии скопирован в буфер обмена"),
                  backgroundColor: AppTheme.successGreen,
                ),
              );
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Верхняя плашка безопасности
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.darkCard,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.accentCyan.withOpacity(0.3)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.verified_user_outlined, color: AppTheme.accentCyan, size: 20),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      "Претензия сформирована автоматически на основании норм ПП РФ № 354 и ст. 157 ЖК РФ",
                      style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.8)),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Лист претензии
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: const Color(0xFF161F33),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white12),
              ),
              child: SelectableText(
                claimText,
                style: const TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 12.5,
                  height: 1.5,
                  color: Colors.white,
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Кнопки действий
            ElevatedButton.icon(
              onPressed: () {
                Clipboard.setData(ClipboardData(text: claimText));
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text("Претензия скопирована! Отправьте её в чат УК или ГИС ЖКХ"),
                    backgroundColor: AppTheme.successGreen,
                  ),
                );
              },
              icon: const Icon(Icons.copy),
              label: const Text("Скопировать для отправки в УК"),
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("Экспорт PDF заявления формируется...")),
                );
              },
              icon: const Icon(Icons.picture_as_pdf_outlined),
              label: const Text("Сохранить PDF бланк"),
              style: OutlinedButton.styleFrom(
                foregroundColor: Colors.white,
                side: const BorderSide(color: Colors.white24),
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
