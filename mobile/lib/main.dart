import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'bloc/audit/audit_bloc.dart';
import 'bloc/audit/audit_event.dart';
import 'bloc/chat/chat_bloc.dart';
import 'bloc/profile/profile_bloc.dart';
import 'core/api_client.dart';
import 'core/theme.dart';
import 'screens/main_scaffold.dart';
import 'screens/onboarding_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
    ),
  );

  runApp(const UtilityLensApp());
}

class UtilityLensApp extends StatelessWidget {
  const UtilityLensApp({super.key});

  @override
  Widget build(BuildContext context) {
    final apiClient = ApiClient();

    return MultiBlocProvider(
      providers: [
        BlocProvider<AuditBloc>(
          create: (_) => AuditBloc(apiClient: apiClient)
            ..add(const LoadAuditDataEvent(caseId: 'case_04_vladivostok_coeff3')),
        ),
        BlocProvider<ChatBloc>(
          create: (_) => ChatBloc(apiClient: apiClient),
        ),
        BlocProvider<ProfileBloc>(
          create: (_) => ProfileBloc(),
        ),
      ],
      child: MaterialApp(
        title: 'UtilityLens',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        home: const MainScaffold(),
      ),
    );
  }
}
