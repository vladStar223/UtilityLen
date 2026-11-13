import 'dart:ui';
import 'package:flutter/material.dart';

// ─────────────────────────────────────────────
// Design Tokens — mirrors web/styles.py palette
// ─────────────────────────────────────────────
class AppColors {
  AppColors._();

  // ── Dark background gradient stops ──────────
  static const Color bgDeep    = Color(0xFF0D0C14); // darkest
  static const Color bgMid     = Color(0xFF171520);
  static const Color bgTop     = Color(0xFF2E2640); // lightest stop

  // ── Accent / brand ──────────────────────────
  static const Color lavender  = Color(0xFFC4B5FD); // primary accent
  static const Color violet    = Color(0xFFA78BFA); // secondary accent

  // ── Text ────────────────────────────────────
  static const Color textPrimary   = Color(0xFFF1F5F9);
  static const Color textSecondary = Color(0xFFCBD5E1);
  static const Color textMuted     = Color(0xFF94A3B8);

  // ── Glass surface ───────────────────────────
  static const Color glassFill    = Color(0x0FFFFFFF); // rgba(255,255,255,0.06)
  static const Color glassBorder  = Color(0x24FFFFFF); // rgba(255,255,255,0.14)

  // ── Status / traffic-light ───────────────────
  static const Color alertRed      = Color(0xFFEF4444);
  static const Color alertRedBg    = Color(0x20EF4444);
  static const Color warningYellow = Color(0xFFF59E0B);
  static const Color warningYellowBg = Color(0x20F59E0B);
  static const Color successGreen  = Color(0xFF10B981);
  static const Color successGreenBg = Color(0x2010B981);

  // ── Light theme equivalents ──────────────────
  static const Color lightBg       = Color(0xFFF8F7FF);
  static const Color lightSurface  = Color(0xFFFFFFFF);
  static const Color lightBorder   = Color(0xFFE2E8F0);
  static const Color lightText     = Color(0xFF1E1B30);
  static const Color lightTextSub  = Color(0xFF64748B);
}

// ─────────────────────────────────────────────
// Glassmorphic BoxDecoration factory
// ─────────────────────────────────────────────
class GlassDecoration {
  GlassDecoration._();

  /// Standard dark glass card — matches web rgba(255,255,255,0.06) + blur
  static BoxDecoration dark({
    double radius = 20,
    List<BoxShadow>? extraShadows,
  }) =>
      BoxDecoration(
        borderRadius: BorderRadius.circular(radius),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color(0x14FFFFFF), // rgba(255,255,255,0.08)
            Color(0x06FFFFFF), // rgba(255,255,255,0.025)
          ],
        ),
        border: Border.all(
          color: AppColors.glassBorder,
          width: 1.0,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.35),
            blurRadius: 24,
            offset: const Offset(0, 8),
          ),
          BoxShadow(
            color: AppColors.violet.withOpacity(0.08),
            blurRadius: 40,
            spreadRadius: -4,
          ),
          ...?extraShadows,
        ],
      );

  /// Elevated accent glass — used for highlighted/focused cards
  static BoxDecoration darkAccent({double radius = 20}) => BoxDecoration(
        borderRadius: BorderRadius.circular(radius),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppColors.lavender.withOpacity(0.12),
            AppColors.violet.withOpacity(0.06),
          ],
        ),
        border: Border.all(
          color: AppColors.lavender.withOpacity(0.30),
          width: 1.0,
        ),
        boxShadow: [
          BoxShadow(
            color: AppColors.violet.withOpacity(0.20),
            blurRadius: 32,
            offset: const Offset(0, 6),
          ),
        ],
      );

  /// Light-theme glass card
  static BoxDecoration light({double radius = 20}) => BoxDecoration(
        borderRadius: BorderRadius.circular(radius),
        color: AppColors.lightSurface.withOpacity(0.80),
        border: Border.all(
          color: AppColors.lightBorder,
          width: 1.0,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
        ],
      );
}

// ─────────────────────────────────────────────
// Status badge styling — traffic-light
// ─────────────────────────────────────────────
enum StatusSeverity { ok, warning, error }

class StatusBadgeStyle {
  final Color color;
  final Color background;
  final String defaultLabel;

  const StatusBadgeStyle._({
    required this.color,
    required this.background,
    required this.defaultLabel,
  });

  static const StatusBadgeStyle ok = StatusBadgeStyle._(
    color: AppColors.successGreen,
    background: AppColors.successGreenBg,
    defaultLabel: 'OK',
  );

  static const StatusBadgeStyle warning = StatusBadgeStyle._(
    color: AppColors.warningYellow,
    background: AppColors.warningYellowBg,
    defaultLabel: 'Warning',
  );

  static const StatusBadgeStyle error = StatusBadgeStyle._(
    color: AppColors.alertRed,
    background: AppColors.alertRedBg,
    defaultLabel: 'Anomaly',
  );

  static StatusBadgeStyle fromSeverity(StatusSeverity s) => switch (s) {
        StatusSeverity.ok      => ok,
        StatusSeverity.warning => warning,
        StatusSeverity.error   => error,
      };

  BoxDecoration get badgeDecoration => BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.40), width: 1),
      );

  TextStyle get labelStyle => TextStyle(
        color: color,
        fontSize: 11,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.5,
      );
}

// ─────────────────────────────────────────────
// App-wide RadialGradient background
// ─────────────────────────────────────────────
const LinearGradient kDarkBgGradient = LinearGradient(
  begin: Alignment.topCenter,
  end: Alignment.bottomCenter,
  colors: [
    AppColors.bgTop,  // #2e2640
    AppColors.bgMid,  // #171520
    AppColors.bgDeep, // #0d0c14
  ],
  stops: [0.0, 0.45, 1.0],
);

// ─────────────────────────────────────────────
// ThemeData builders
// ─────────────────────────────────────────────
class AppTheme {
  AppTheme._();

  // ── Kept for backward-compat ─────────────────
  static const Color primaryBlue     = AppColors.lavender;
  static const Color accentCyan      = AppColors.violet;
  static const Color darkBackground  = AppColors.bgDeep;
  static const Color darkCard        = Color(0xFF1E1B2E);
  static const Color darkSurface     = Color(0xFF16131F);
  static const Color alertRed        = AppColors.alertRed;
  static const Color alertRedBg      = AppColors.alertRedBg;
  static const Color warningYellow   = AppColors.warningYellow;
  static const Color warningYellowBg = AppColors.warningYellowBg;
  static const Color successGreen    = AppColors.successGreen;
  static const Color successGreenBg  = AppColors.successGreenBg;

  // ── Dark theme ───────────────────────────────
  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: AppColors.bgDeep,
      colorScheme: ColorScheme.dark(
        primary: AppColors.lavender,
        secondary: AppColors.violet,
        surface: darkCard,
        onSurface: AppColors.textPrimary,
        onPrimary: AppColors.bgDeep,
        error: AppColors.alertRed,
      ),
      textTheme: _textTheme(AppColors.textPrimary, AppColors.textSecondary),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          color: AppColors.textPrimary,
          fontSize: 18,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.2,
        ),
        iconTheme: IconThemeData(color: AppColors.textPrimary),
      ),
      cardTheme: CardTheme(
        color: Colors.transparent,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: const BorderSide(color: AppColors.glassBorder, width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.lavender,
          foregroundColor: AppColors.bgDeep,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.lavender,
          side: const BorderSide(color: AppColors.lavender, width: 1),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.glassFill,
        hintStyle: const TextStyle(color: AppColors.textMuted),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.glassBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.glassBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.lavender, width: 1.5),
        ),
      ),
      dividerColor: AppColors.glassBorder,
      iconTheme: const IconThemeData(color: AppColors.textSecondary),
      chipTheme: ChipThemeData(
        backgroundColor: AppColors.glassFill,
        labelStyle: const TextStyle(color: AppColors.textPrimary, fontSize: 12),
        side: const BorderSide(color: AppColors.glassBorder),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    );
  }

  // ── Light theme ──────────────────────────────
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: AppColors.lightBg,
      colorScheme: const ColorScheme.light(
        primary: AppColors.violet,
        secondary: AppColors.lavender,
        surface: AppColors.lightSurface,
        onSurface: AppColors.lightText,
        error: AppColors.alertRed,
      ),
      textTheme: _textTheme(AppColors.lightText, AppColors.lightTextSub),
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.lightSurface,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          color: AppColors.lightText,
          fontSize: 18,
          fontWeight: FontWeight.w600,
        ),
        iconTheme: IconThemeData(color: AppColors.lightText),
      ),
      cardTheme: CardTheme(
        color: AppColors.lightSurface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: const BorderSide(color: AppColors.lightBorder),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.violet,
          foregroundColor: Colors.white,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.lightSurface,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.lightBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.lightBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.violet, width: 1.5),
        ),
      ),
      dividerColor: AppColors.lightBorder,
    );
  }

  static TextTheme _textTheme(Color primary, Color secondary) => TextTheme(
        displayLarge:  TextStyle(color: primary,   fontWeight: FontWeight.w700, fontSize: 32),
        displayMedium: TextStyle(color: primary,   fontWeight: FontWeight.w700, fontSize: 26),
        headlineMedium:TextStyle(color: primary,   fontWeight: FontWeight.w600, fontSize: 20),
        titleLarge:    TextStyle(color: primary,   fontWeight: FontWeight.w600, fontSize: 18),
        titleMedium:   TextStyle(color: primary,   fontWeight: FontWeight.w500, fontSize: 16),
        bodyLarge:     TextStyle(color: primary,   fontWeight: FontWeight.w400, fontSize: 15),
        bodyMedium:    TextStyle(color: secondary, fontWeight: FontWeight.w400, fontSize: 13),
        labelSmall:    TextStyle(color: secondary, fontWeight: FontWeight.w500, fontSize: 11, letterSpacing: 0.5),
      );
}
