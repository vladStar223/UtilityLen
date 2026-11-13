import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'core/theme.dart';
import 'screens/home_scanner_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);
  runApp(const UtilityLensApp());
}

class UtilityLensApp extends StatelessWidget {
  const UtilityLensApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'UtilityLens Mobile',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const HomeScannerScreen(),
    );
  }
}
