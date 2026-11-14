import 'package:flutter_test/flutter_test.dart';
import 'package:utilitylens_mobile/main.dart';

void main() {
  testWidgets('UtilityLensApp smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const UtilityLensApp());
    expect(find.byType(UtilityLensApp), findsOneWidget);
  });
}
