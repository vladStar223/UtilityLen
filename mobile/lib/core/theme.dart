import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Design system tokens for UtilityLens
/// Style: Light Glassmorphism + Modern Fintech
class AppColors {
  AppColors._();

  // ── Основные цвета по спецификации ─────────────
  static const Color background     = Color(0xFFF7F7FF); // Основной фон
  static const Color card           = Color(0xFFFFFFFF); // Карточки / Surface
  static const Color primary        = Color(0xFF6046E8); // Основной фиолетовый
  static const Color primaryLight   = Color(0xFFEAE6FF); // Светло-фиолетовый
  static const Color textPrimary    = Color(0xFF171735); // Основной текст
  static const Color textSecondary  = Color(0xFF777895); // Вторичный текст
  static const Color critical       = Color(0xFFEF476F); // Критическая ошибка
  static const Color error          = critical;
  static const Color warning        = Color(0xFFFFB938); // Предупреждение
  static const Color success        = Color(0xFF24B47E); // Успешный результат
  static const Color border         = Color(0xFFE7E6F2); // Границы

  // ── Дополнительные гармоничные оттенки ──────────
  static const Color criticalLight  = Color(0xFFFFF0F3); // Фон предупреждений
  static const Color warningLight   = Color(0xFFFFF9EB); // Фон желтых алертов
  static const Color successLight   = Color(0xFFE9FAF3); // Фон успешного документа
  static const Color primaryGradientEnd = Color(0xFF7C66FF);

  // ── Dark theme tokens для Onboarding и Сканера ──
  static const Color darkBackground = Color(0xFF171520);
  static const Color darkSurface    = Color(0xFF242038);
  static const Color darkGlass      = Color(0x33FFFFFF);
  static const Color darkText       = Color(0xFFFFFFFF);
  static const Color darkTextSub    = Color(0xFFB4B0C7);
}

class AppTheme {
  AppTheme._();

  static ThemeData get lightTheme {
    final baseText = GoogleFonts.interTextTheme();

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: AppColors.background,
      primaryColor: AppColors.primary,
      colorScheme: const ColorScheme.light(
        primary: AppColors.primary,
        secondary: AppColors.primaryLight,
        surface: AppColors.card,
        error: AppColors.critical,
        onPrimary: Colors.white,
        onSecondary: AppColors.primary,
        onSurface: AppColors.textPrimary,
        onError: Colors.white,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        iconTheme: IconThemeData(color: AppColors.textPrimary),
        titleTextStyle: TextStyle(
          color: AppColors.textPrimary,
          fontSize: 18,
          fontWeight: FontWeight.w700,
        ),
      ),
      cardTheme: CardTheme(
        color: AppColors.card,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: const BorderSide(color: AppColors.border, width: 1),
        ),
        margin: EdgeInsets.zero,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primary,
          foregroundColor: Colors.white,
          elevation: 0,
          minimumSize: const Size(double.infinity, 50),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(18),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.primary,
          side: const BorderSide(color: AppColors.border, width: 1.2),
          minimumSize: const Size(double.infinity, 48),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(18),
          ),
          textStyle: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      textTheme: baseText.copyWith(
        displayLarge: const TextStyle(
          color: AppColors.textPrimary,
          fontSize: 32,
          fontWeight: FontWeight.w800,
        ),
        displayMedium: const TextStyle(
          color: AppColors.textPrimary,
          fontSize: 26,
          fontWeight: FontWeight.w700,
        ),
        titleLarge: const TextStyle(
          color: AppColors.textPrimary,
          fontSize: 20,
          fontWeight: FontWeight.w700,
        ),
        titleMedium: const TextStyle(
          color: AppColors.textPrimary,
          fontSize: 16,
          fontWeight: FontWeight.w600,
        ),
        bodyLarge: const TextStyle(
          color: AppColors.textPrimary,
          fontSize: 15,
          fontWeight: FontWeight.w400,
        ),
        bodyMedium: const TextStyle(
          color: AppColors.textSecondary,
          fontSize: 13,
          fontWeight: FontWeight.w400,
        ),
        labelLarge: const TextStyle(
          color: AppColors.primary,
          fontSize: 14,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

/// Helpers for Glassmorphic & Fintech cards
class FintechDecorations {
  FintechDecorations._();

  static BoxDecoration card({
    Color? color,
    Color? borderColor,
    double radius = 20,
    bool withShadow = true,
  }) {
    return BoxDecoration(
      color: color ?? AppColors.card,
      borderRadius: BorderRadius.circular(radius),
      border: Border.all(color: borderColor ?? AppColors.border, width: 1),
      boxShadow: withShadow
          ? [
              const BoxShadow(
                color: Color(0x0A6046E8),
                blurRadius: 18,
                offset: Offset(0, 6),
              ),
            ]
          : null,
    );
  }

  static BoxDecoration heroPurpleCard({double radius = 22}) {
    return BoxDecoration(
      gradient: const LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [
          AppColors.primary,
          AppColors.primaryGradientEnd,
        ],
      ),
      borderRadius: BorderRadius.circular(radius),
      boxShadow: [
        BoxShadow(
          color: AppColors.primary.withValues(alpha: 0.28),
          blurRadius: 24,
          offset: const Offset(0, 10),
        ),
      ],
    );
  }

  static BoxDecoration alertCard({double radius = 18}) {
    return BoxDecoration(
      color: AppColors.criticalLight,
      borderRadius: BorderRadius.circular(radius),
      border: Border.all(
        color: AppColors.critical.withValues(alpha: 0.25),
        width: 1,
      ),
    );
  }
}
