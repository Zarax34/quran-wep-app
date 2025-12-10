import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'providers/auth_provider.dart';
import 'services/sync_service.dart'; // Import to ensure provider is created
import 'ui/screens/login_screen.dart';
import 'ui/screens/dashboard_screen.dart';

void main() {
  runApp(const ProviderScope(child: MyApp()));
}

class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);

    // Watch sync service to initialize connectivity listener
    ref.watch(syncServiceProvider);

    return MaterialApp(
      title: 'Quran Center',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF2C5AA0)),
        useMaterial3: true,
        // fontFamily: 'NotoNaskhArabic', // Ensure this font is added if used
      ),
      locale: const Locale('ar', ''),
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [
        Locale('ar', ''),
        Locale('en', ''),
      ],
      home: authState.status == AuthStatus.authenticated
          ? const DashboardScreen()
          : const LoginScreen(),
    );
  }
}
