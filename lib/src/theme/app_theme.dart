import 'package:flutter/material.dart';

/// Colours the Material scheme has no slot for. Read with `AppColors.of(context)`.
@immutable
class AppColors extends ThemeExtension<AppColors> {
  const AppColors({required this.pay, required this.muted, required this.headerFill});

  /// Money: pay per entry, per day and per job.
  final Color pay;

  /// Secondary text such as dates and counts.
  final Color muted;

  /// Background of day headers and summary strips.
  final Color headerFill;

  static AppColors of(BuildContext context) => Theme.of(context).extension<AppColors>()!;

  @override
  AppColors copyWith({Color? pay, Color? muted, Color? headerFill}) => AppColors(
        pay: pay ?? this.pay,
        muted: muted ?? this.muted,
        headerFill: headerFill ?? this.headerFill,
      );

  @override
  AppColors lerp(ThemeExtension<AppColors>? other, double t) {
    if (other is! AppColors) return this;
    return AppColors(
      pay: Color.lerp(pay, other.pay, t)!,
      muted: Color.lerp(muted, other.muted, t)!,
      headerFill: Color.lerp(headerFill, other.headerFill, t)!,
    );
  }
}

/// The Time Tracker look: Material 3, seeded from one teal brand colour, light and dark.
class AppTheme {
  static const brand = Color(0xFF0F766E);
  static const radius = 16.0;

  static ThemeData light() => _build(Brightness.light);
  static ThemeData dark() => _build(Brightness.dark);

  static ThemeData _build(Brightness brightness) {
    final scheme = ColorScheme.fromSeed(seedColor: brand, brightness: brightness);
    final isDark = brightness == Brightness.dark;
    final shape = RoundedRectangleBorder(borderRadius: BorderRadius.circular(radius));
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: isDark ? scheme.surface : scheme.surfaceContainerLowest,
      appBarTheme: AppBarTheme(
        backgroundColor: scheme.surface,
        foregroundColor: scheme.onSurface,
        surfaceTintColor: scheme.surfaceTint,
        centerTitle: false,
        elevation: 0,
        scrolledUnderElevation: 2,
        titleTextStyle: TextStyle(fontSize: 22, fontWeight: FontWeight.w700, color: scheme.onSurface),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: scheme.surfaceContainerLow,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radius),
          side: BorderSide(color: scheme.outlineVariant),
        ),
        margin: EdgeInsets.zero,
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(minimumSize: const Size(64, 48), shape: shape),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: scheme.primary,
          foregroundColor: scheme.onPrimary,
          minimumSize: const Size(64, 48),
          shape: shape,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(minimumSize: const Size(64, 48), shape: shape),
      ),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: scheme.primary,
        foregroundColor: scheme.onPrimary,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: scheme.surfaceContainerHighest.withValues(alpha: 0.5),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
      ),
      sliderTheme: SliderThemeData(
        trackHeight: 6,
        showValueIndicator: ShowValueIndicator.onDrag,
        activeTrackColor: scheme.primary,
        inactiveTrackColor: scheme.primaryContainer,
      ),
      navigationBarTheme: NavigationBarThemeData(indicatorColor: scheme.primaryContainer),
      navigationRailTheme: NavigationRailThemeData(indicatorColor: scheme.primaryContainer),
      dividerTheme: DividerThemeData(color: scheme.outlineVariant, space: 1),
      extensions: [
        AppColors(
          pay: isDark ? const Color(0xFF6EE7B7) : const Color(0xFF047857),
          muted: scheme.onSurfaceVariant,
          headerFill: scheme.primaryContainer.withValues(alpha: isDark ? 0.35 : 0.55),
        ),
      ],
    );
  }
}
