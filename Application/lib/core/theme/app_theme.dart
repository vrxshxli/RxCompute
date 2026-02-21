import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'app_colors.dart';

class AppTheme {
  AppTheme._();
  static String get _display => GoogleFonts.dmSerifDisplay().fontFamily!;
  static String get _body => GoogleFonts.outfit().fontFamily!;
  static String get _mono => GoogleFonts.jetBrainsMono().fontFamily!;

  static ThemeData get dark => _build(Brightness.dark);
  static ThemeData get light => _build(Brightness.light);

  static ThemeData _build(Brightness b) {
    final dk = b == Brightness.dark;
    final bg = dk ? C.d1 : C.l0;
    final card = dk ? C.d2 : C.l1;
    final border = dk ? C.d4 : C.l3;
    final t1 = dk ? C.tw : C.tb;
    final t2 = dk ? C.t1 : C.t3;
    final t3 = dk ? C.t2 : C.t4;
    final input = dk ? C.d3 : C.l1;

    return ThemeData(
      brightness: b, useMaterial3: true, scaffoldBackgroundColor: bg, fontFamily: _body,
      colorScheme: ColorScheme(
        brightness: b, primary: C.rx, onPrimary: Colors.white,
        secondary: C.compute, onSecondary: Colors.white,
        surface: card, onSurface: t1, error: C.err, onError: Colors.white,
      ),
      textTheme: TextTheme(
        headlineLarge: GoogleFonts.dmSerifDisplay(fontSize: 36, fontWeight: FontWeight.w400, color: t1, height: 1.05, letterSpacing: -0.5),
        headlineMedium: GoogleFonts.dmSerifDisplay(fontSize: 28, fontWeight: FontWeight.w400, color: t1, height: 1.1),
        headlineSmall: GoogleFonts.dmSerifDisplay(fontSize: 22, fontWeight: FontWeight.w400, color: t1, height: 1.15),
        titleLarge: GoogleFonts.outfit(fontSize: 17, fontWeight: FontWeight.w600, color: t1, letterSpacing: 0.1),
        titleMedium: GoogleFonts.outfit(fontSize: 15, fontWeight: FontWeight.w600, color: t1),
        titleSmall: GoogleFonts.outfit(fontSize: 13, fontWeight: FontWeight.w600, color: t1),
        bodyLarge: GoogleFonts.outfit(fontSize: 15, fontWeight: FontWeight.w400, color: t1, height: 1.55),
        bodyMedium: GoogleFonts.outfit(fontSize: 14, fontWeight: FontWeight.w400, color: t1, height: 1.55),
        bodySmall: GoogleFonts.outfit(fontSize: 13, fontWeight: FontWeight.w400, color: t2, height: 1.5),
        labelLarge: GoogleFonts.outfit(fontSize: 12, fontWeight: FontWeight.w700, color: t3, letterSpacing: 1.5),
        labelMedium: GoogleFonts.outfit(fontSize: 11, fontWeight: FontWeight.w600, color: t3, letterSpacing: 1.0),
        labelSmall: GoogleFonts.outfit(fontSize: 10, fontWeight: FontWeight.w600, color: t3, letterSpacing: 1.2),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: bg, foregroundColor: t1, elevation: 0, scrolledUnderElevation: 0, centerTitle: true,
        titleTextStyle: GoogleFonts.outfit(fontSize: 16, fontWeight: FontWeight.w600, color: t1),
        systemOverlayStyle: SystemUiOverlayStyle(
          statusBarColor: Colors.transparent,
          statusBarIconBrightness: dk ? Brightness.light : Brightness.dark),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true, fillColor: input,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide(color: border)),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide(color: border)),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: C.compute, width: 1.5)),
        hintStyle: GoogleFonts.outfit(color: t3, fontSize: 14),
      ),
      dividerTheme: DividerThemeData(color: border, thickness: 1, space: 0),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.all(Colors.white),
        trackColor: WidgetStateProperty.resolveWith((s) => s.contains(WidgetState.selected) ? C.compute : (dk ? C.d5 : C.l4)),
        trackOutlineColor: WidgetStateProperty.all(Colors.transparent),
      ),
    );
  }
}
