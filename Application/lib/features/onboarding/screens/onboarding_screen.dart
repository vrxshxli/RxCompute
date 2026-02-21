import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/shared_widgets.dart';
import '../../../config/routes.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});
  @override
  State<OnboardingScreen> createState() => _S();
}

class _S extends State<OnboardingScreen> {
  final _pc = PageController();
  int _p = 0;
  void _go() => Navigator.pushReplacementNamed(context, AppRoutes.login);
  @override
  void dispose() {
    _pc.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: C.d1,
        body: SafeArea(
          child: Column(children: [
            Align(
              alignment: Alignment.topRight,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(0, 16, 24, 0),
                child: GestureDetector(onTap: _go, child: Text('SKIP', style: GoogleFonts.outfit(color: C.t2, fontSize: 12, fontWeight: FontWeight.w700, letterSpacing: 2))),
              ),
            ),
            Expanded(
              child: PageView(
                controller: _pc,
                onPageChanged: (i) => setState(() => _p = i),
                children: const [
                  _Pg(icon: Icons.chat_bubble_rounded, color: C.compute, t1: 'TALK TO YOUR', t2: 'AI Pharmacist', desc: 'Order medicines using natural language.\nVoice and text both work.'),
                  _Pg(icon: Icons.verified_user_rounded, color: C.ok, t1: 'SMART SAFETY', t2: 'Always On', desc: 'Every order checked for prescriptions,\ninteractions, and stock.'),
                  _Pg(icon: Icons.notifications_active_rounded, color: C.warn, t1: 'NEVER RUN', t2: 'Out Again', desc: 'We predict when medicines run out\nand remind you before it happens.'),
                ],
              ),
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(
                3,
                (i) => AnimatedContainer(
                  duration: const Duration(milliseconds: 300),
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  width: i == _p ? 28 : 8,
                  height: 4,
                  decoration: BoxDecoration(color: i == _p ? C.rx : C.d4, borderRadius: BorderRadius.circular(2)),
                ),
              ),
            ),
            const SizedBox(height: 36),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
              child: RxBtn(
                label: _p == 2 ? 'Get Started' : 'Continue',
                onPressed: () {
                  if (_p < 2) {
                    _pc.nextPage(duration: const Duration(milliseconds: 350), curve: Curves.easeInOut);
                  } else {
                    _go();
                  }
                },
              ),
            ),
          ]),
        ),
      );
}

class _Pg extends StatelessWidget {
  final IconData icon;
  final Color color;
  final String t1, t2, desc;
  const _Pg({required this.icon, required this.color, required this.t1, required this.t2, required this.desc});
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32),
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Container(
            width: 88,
            height: 88,
            decoration: BoxDecoration(color: color.withOpacity(0.08), borderRadius: BorderRadius.circular(24)),
            child: Icon(icon, size: 40, color: color),
          ),
          const SizedBox(height: 48),
          Text(t1, style: GoogleFonts.outfit(color: C.t1, fontSize: 14, fontWeight: FontWeight.w700, letterSpacing: 3)),
          const SizedBox(height: 4),
          Text(t2, style: GoogleFonts.dmSerifDisplay(color: C.tw, fontSize: 42, height: 1.05)),
          const SizedBox(height: 20),
          Text(desc, textAlign: TextAlign.center, style: GoogleFonts.outfit(color: C.t1, fontSize: 15, height: 1.6)),
        ]),
      );
}
