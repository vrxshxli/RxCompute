import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/rx_theme_ext.dart';
import '../../../core/widgets/shared_widgets.dart';
import '../../../config/routes.dart';
import '../../theme/bloc/theme_bloc.dart';
import '../../auth/bloc/auth_bloc.dart';
import '../../auth/bloc/auth_event.dart';
import '../bloc/profile_bloc.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});
  @override
  State<ProfileScreen> createState() => _PS();
}

class _PS extends State<ProfileScreen> {
  bool _r1 = true, _r2 = true, _r3 = false;

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return BlocBuilder<ProfileBloc, ProfileState>(
      builder: (context, state) {
        final p = state.user;
        if (p == null) return const Scaffold(body: Center(child: CircularProgressIndicator()));

        return Scaffold(
          backgroundColor: r.bg,
          body: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(24, 20, 24, 40),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Center(
                  child: Column(children: [
                    Container(width: 72, height: 72, decoration: BoxDecoration(color: r.surface, borderRadius: BorderRadius.circular(20)), child: Center(child: Text(p.initials, style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 26)))),
                    const SizedBox(height: 14),
                    Text(p.name ?? '', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 24)),
                    const SizedBox(height: 4),
                    Mono('PAT00${p.id}', size: 12),
                  ]),
                ),
                const SizedBox(height: 36),
                const SecLabel('PERSONAL'),
                RxCard(
                  padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 18),
                  child: Column(children: [
                    _R(l: 'NAME', v: p.name ?? ''),
                    _dv(r),
                    _R(l: 'AGE', v: '${p.age ?? ''}'),
                    _dv(r),
                    _R(l: 'GENDER', v: p.gender == 'M' ? 'Male' : p.gender == 'F' ? 'Female' : p.gender ?? ''),
                    _dv(r),
                    _R(l: 'PHONE', v: p.phone),
                    _dv(r),
                    _R(l: 'ALLERGIES', v: p.allergyList.join(', ')),
                  ]),
                ),
                const SizedBox(height: 28),
                const SecLabel('APPEARANCE'),
                BlocBuilder<ThemeBloc, ThemeState>(
                  builder: (context, themeState) => RxCard(
                    padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 18),
                    child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                      Row(children: [
                        Icon(themeState.isDark ? Icons.dark_mode_rounded : Icons.light_mode_rounded, color: r.text1, size: 18),
                        const SizedBox(width: 12),
                        Text('DARK MODE', style: GoogleFonts.outfit(color: r.text1, fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 0.8)),
                      ]),
                      Switch(value: themeState.isDark, onChanged: (_) => context.read<ThemeBloc>().add(ToggleThemeEvent())),
                    ]),
                  ),
                ),
                const SizedBox(height: 28),
                const SecLabel('NOTIFICATIONS'),
                RxCard(
                  padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 18),
                  child: Column(children: [
                    _Tg(l: 'REFILL REMINDERS', v: _r1, f: (v) => setState(() => _r1 = v)),
                    _dv(r),
                    _Tg(l: 'ORDER UPDATES', v: _r2, f: (v) => setState(() => _r2 = v)),
                    _dv(r),
                    _Tg(l: 'HEALTH ALERTS', v: _r3, f: (v) => setState(() => _r3 = v)),
                  ]),
                ),
                const SizedBox(height: 28),
                const SecLabel('DATA & PRIVACY'),
                RxCard(
                  padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 18),
                  child: Column(children: [
                    _A(ic: Icons.verified_user_outlined, l: 'MANAGE CONSENT', fn: () {}),
                    _dv(r),
                    _A(ic: Icons.download_rounded, l: 'DOWNLOAD DATA', fn: () {}),
                    _dv(r),
                    _A(ic: Icons.delete_outline_rounded, l: 'DELETE ACCOUNT', c: C.err, fn: () {}),
                  ]),
                ),
                const SizedBox(height: 28),
                const SecLabel('ABOUT'),
                RxCard(
                  padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 18),
                  child: Column(children: [
                    _A(ic: Icons.info_outline_rounded, l: 'VERSION 1.0.0'),
                    _dv(r),
                    _A(ic: Icons.analytics_outlined, l: 'LANGFUSE TRACES', fn: () {}),
                    _dv(r),
                    _A(ic: Icons.description_outlined, l: 'TERMS OF SERVICE', fn: () {}),
                  ]),
                ),
                const SizedBox(height: 32),
                SizedBox(
                  width: double.infinity,
                  child: RxBtn(
                    label: 'Sign Out',
                    outlined: true,
                    onPressed: () {
                      context.read<AuthBloc>().add(LogoutEvent());
                      Navigator.pushNamedAndRemoveUntil(context, AppRoutes.login, (_) => false);
                    },
                  ),
                ),
              ]),
            ),
          ),
        );
      },
    );
  }

  Widget _dv(Rx r) => Container(height: 1, color: r.border);
}

class _R extends StatelessWidget {
  final String l, v;
  const _R({required this.l, required this.v});
  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 14),
      child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Text(l, style: GoogleFonts.outfit(color: r.text3, fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 1.5)),
        Row(children: [Text(v, style: GoogleFonts.outfit(color: r.text1, fontSize: 14)), const SizedBox(width: 8), Icon(Icons.edit_outlined, color: r.text3, size: 14)]),
      ]),
    );
  }
}

class _Tg extends StatelessWidget {
  final String l;
  final bool v;
  final ValueChanged<bool> f;
  const _Tg({required this.l, required this.v, required this.f});
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text(l, style: GoogleFonts.outfit(color: context.rx.text1, fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 0.8)),
          Switch(value: v, onChanged: f),
        ]),
      );
}

class _A extends StatelessWidget {
  final IconData ic;
  final String l;
  final Color? c;
  final VoidCallback? fn;
  const _A({required this.ic, required this.l, this.c, this.fn});
  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    final col = c ?? r.text1;
    return GestureDetector(
      onTap: fn,
      behavior: HitTestBehavior.opaque,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 14),
        child: Row(children: [
          Icon(ic, color: col, size: 18),
          const SizedBox(width: 12),
          Expanded(child: Text(l, style: GoogleFonts.outfit(color: col, fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 0.8))),
          if (fn != null) Icon(Icons.chevron_right_rounded, color: r.text3, size: 18),
        ]),
      ),
    );
  }
}
