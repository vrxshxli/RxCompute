import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/rx_theme_ext.dart';
import 'home_tab.dart';
import '../../chat/screens/chat_screen.dart';
import '../../medicine/screens/medicine_brain_screen.dart';
import '../../profile/screens/profile_screen.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key});
  @override
  State<MainShell> createState() => _MS();
}

class _MS extends State<MainShell> {
  int _i = 0;
  final _screens = const [HomeTab(), ChatScreen(), MedicineBrainScreen(), ProfileScreen()];

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return Scaffold(
      body: IndexedStack(index: _i, children: _screens),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(color: r.card, border: Border(top: BorderSide(color: r.border, width: 0.5))),
        child: SafeArea(
          top: false,
          child: SizedBox(
            height: 64,
            child: Row(children: [
              _Tab(ic: Icons.home_rounded, lb: 'HOME', on: _i == 0, fn: () => setState(() => _i = 0)),
              _Tab(ic: Icons.chat_bubble_rounded, lb: 'CHAT', on: _i == 1, fn: () => setState(() => _i = 1)),
              _Tab(ic: Icons.medication_rounded, lb: 'MEDS', on: _i == 2, fn: () => setState(() => _i = 2)),
              _Tab(ic: Icons.person_rounded, lb: 'PROFILE', on: _i == 3, fn: () => setState(() => _i = 3)),
            ]),
          ),
        ),
      ),
    );
  }
}

class _Tab extends StatelessWidget {
  final IconData ic;
  final String lb;
  final bool on;
  final VoidCallback fn;
  const _Tab({required this.ic, required this.lb, required this.on, required this.fn});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: GestureDetector(
        onTap: fn,
        behavior: HitTestBehavior.opaque,
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
            decoration: BoxDecoration(color: on ? C.rx.withOpacity(0.08) : Colors.transparent, borderRadius: BorderRadius.circular(16)),
            child: Icon(ic, size: 20, color: on ? C.rx : context.rx.text3),
          ),
          const SizedBox(height: 3),
          Text(lb, style: GoogleFonts.outfit(fontSize: 9, fontWeight: on ? FontWeight.w700 : FontWeight.w500, color: on ? C.rx : context.rx.text3, letterSpacing: 1.2)),
        ]),
      ),
    );
  }
}
