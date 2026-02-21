import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/rx_theme_ext.dart';
import '../../../core/widgets/shared_widgets.dart';
import '../../../config/routes.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});
  @override
  State<SplashScreen> createState() => _SS();
}

class _SS extends State<SplashScreen> with TickerProviderStateMixin {
  late AnimationController _c, _b;

  @override
  void initState() {
    super.initState();
    _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 900))..forward();
    _b = AnimationController(vsync: this, duration: const Duration(milliseconds: 1400));
    Future.delayed(const Duration(milliseconds: 400), () {
      if (mounted) _b.forward();
    });
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) Navigator.pushReplacementNamed(context, AppRoutes.onboarding);
    });
  }

  @override
  void dispose() {
    _c.dispose();
    _b.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: C.d0,
        body: Center(
          child: FadeTransition(
            opacity: CurvedAnimation(parent: _c, curve: Curves.easeOut),
            child: ScaleTransition(
              scale: Tween(begin: 0.85, end: 1.0).animate(CurvedAnimation(parent: _c, curve: Curves.easeOutBack)),
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                const RxLogo(size: 36),
                const SizedBox(height: 8),
                Text('YOUR AI PHARMACIST', style: GoogleFonts.outfit(color: C.t2, fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 3)),
                const SizedBox(height: 48),
                AnimatedBuilder(
                  animation: _b,
                  builder: (_, __) => Container(
                    width: 80,
                    height: 2,
                    decoration: BoxDecoration(color: C.d4, borderRadius: BorderRadius.circular(1)),
                    alignment: Alignment.centerLeft,
                    child: FractionallySizedBox(
                      widthFactor: _b.value,
                      child: Container(decoration: BoxDecoration(color: C.compute, borderRadius: BorderRadius.circular(1))),
                    ),
                  ),
                ),
              ]),
            ),
          ),
        ),
      );
}
