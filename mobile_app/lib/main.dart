import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'providers/auth_provider.dart';
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

    return MaterialApp(
      title: 'Quran Center',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF2C5AA0)), // Primary Color from Flask App
        useMaterial3: true,
        fontFamily: 'NotoNaskhArabic', // Assuming we add this font
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
