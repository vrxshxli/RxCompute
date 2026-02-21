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
  void initState() {
    super.initState();
    // Load profile from backend when screen opens
    context.read<ProfileBloc>().add(LoadProfileEvent());
  }

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return BlocBuilder<ProfileBloc, ProfileState>(
      builder: (context, state) {
        // ─── Loading ─────────────────────────────────
        if (state.isLoading && state.user == null) {
          return Scaffold(
            backgroundColor: r.bg,
            body: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const CircularProgressIndicator(),
                  const SizedBox(height: 16),
                  Text('Loading profile...', style: GoogleFonts.outfit(color: r.text2, fontSize: 14)),
                ],
              ),
            ),
          );
        }

        // ─── Error (no user data) ─────────────────────
        if (state.error != null && state.user == null) {
          return Scaffold(
            backgroundColor: r.bg,
            body: Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.error_outline_rounded, color: C.err, size: 48),
                    const SizedBox(height: 16),
                    Text(state.error!, textAlign: TextAlign.center, style: GoogleFonts.outfit(color: r.text2, fontSize: 14)),
                    const SizedBox(height: 24),
                    RxBtn(
                      label: 'Retry',
                      onPressed: () => context.read<ProfileBloc>().add(LoadProfileEvent()),
                    ),
                  ],
                ),
              ),
            ),
          );
        }

        final p = state.user;
        if (p == null) {
          return Scaffold(
            backgroundColor: r.bg,
            body: const Center(child: CircularProgressIndicator()),
          );
        }

        return Scaffold(
          backgroundColor: r.bg,
          body: SafeArea(
            child: RefreshIndicator(
              color: C.rx,
              onRefresh: () async {
                context.read<ProfileBloc>().add(LoadProfileEvent());
                // Wait a bit for the state to update
                await Future.delayed(const Duration(milliseconds: 500));
              },
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(24, 20, 24, 40),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  // ─── Profile Header ──────────────────────
                  Center(
                    child: Column(children: [
                      // Profile picture or initials
                      if (p.profilePicture != null && p.profilePicture!.isNotEmpty)
                        Container(
                          width: 80,
                          height: 80,
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(22),
                            border: Border.all(color: C.rx.withOpacity(0.3), width: 2),
                          ),
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(20),
                            child: Image.network(
                              p.profilePicture!,
                              fit: BoxFit.cover,
                              errorBuilder: (_, __, ___) => Container(
                                color: r.surface,
                                child: Center(
                                  child: Text(
                                    p.initials,
                                    style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 28),
                                  ),
                                ),
                              ),
                            ),
                          ),
                        )
                      else
                        Container(
                          width: 80,
                          height: 80,
                          decoration: BoxDecoration(
                            color: r.surface,
                            borderRadius: BorderRadius.circular(22),
                            border: Border.all(color: r.border),
                          ),
                          child: Center(
                            child: Text(
                              p.initials,
                              style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 28),
                            ),
                          ),
                        ),
                      const SizedBox(height: 14),
                      Text(
                        p.name ?? 'User',
                        style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 24),
                      ),
                      const SizedBox(height: 4),
                      Mono('PAT00${p.id}', size: 12),
                      if (p.email != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          p.email!,
                          style: GoogleFonts.outfit(color: r.text2, fontSize: 13),
                        ),
                      ],
                    ]),
                  ),

                  const SizedBox(height: 36),

                  // ─── Personal Details ────────────────────
                  const SecLabel('PERSONAL'),
                  RxCard(
                    padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 18),
                    child: Column(children: [
                      _InfoRow(label: 'NAME', value: p.name ?? '—'),
                      _divider(r),
                      _InfoRow(label: 'AGE', value: p.age != null ? '${p.age}' : '—'),
                      _divider(r),
                      _InfoRow(
                        label: 'GENDER',
                        value: _formatGender(p.gender),
                      ),
                      _divider(r),
                      _InfoRow(
                        label: 'PHONE',
                        value: p.phone ?? '—',
                      ),
                      _divider(r),
                      _InfoRow(
                        label: 'EMAIL',
                        value: p.email ?? '—',
                      ),
                    ]),
                  ),

                  const SizedBox(height: 28),

                  // ─── Health Info ──────────────────────────
                  const SecLabel('HEALTH'),
                  RxCard(
                    padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 18),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      // Allergies
                      Text(
                        'ALLERGIES',
                        style: GoogleFonts.outfit(
                          color: r.text3,
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.5,
                        ),
                      ),
                      const SizedBox(height: 8),
                      if (p.allergyList.isNotEmpty)
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: p.allergyList
                              .map((a) => _Tag(text: a, color: C.err))
                              .toList(),
                        )
                      else
                        Text('None', style: GoogleFonts.outfit(color: r.text2, fontSize: 14)),

                      const SizedBox(height: 18),
                      Container(height: 1, color: r.border),
                      const SizedBox(height: 14),

                      // Conditions
                      Text(
                        'CONDITIONS',
                        style: GoogleFonts.outfit(
                          color: r.text3,
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.5,
                        ),
                      ),
                      const SizedBox(height: 8),
                      if (p.conditionList.isNotEmpty)
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: p.conditionList
                              .map((c) => _Tag(text: c, color: C.warn))
                              .toList(),
                        )
                      else
                        Text('None', style: GoogleFonts.outfit(color: r.text2, fontSize: 14)),
                    ]),
                  ),

                  const SizedBox(height: 28),

                  // ─── Appearance ──────────────────────────
                  const SecLabel('APPEARANCE'),
                  BlocBuilder<ThemeBloc, ThemeState>(
                    builder: (context, themeState) => RxCard(
                      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 18),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(children: [
                            Icon(
                              themeState.isDark ? Icons.dark_mode_rounded : Icons.light_mode_rounded,
                              color: r.text1,
                              size: 18,
                            ),
                            const SizedBox(width: 12),
                            Text(
                              'DARK MODE',
                              style: GoogleFonts.outfit(
                                color: r.text1,
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                letterSpacing: 0.8,
                              ),
                            ),
                          ]),
                          Switch(
                            value: themeState.isDark,
                            onChanged: (_) => context.read<ThemeBloc>().add(ToggleThemeEvent()),
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 28),

                  // ─── Notifications ──────────────────────
                  const SecLabel('NOTIFICATIONS'),
                  RxCard(
                    padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 18),
                    child: Column(children: [
                      _ToggleRow(label: 'REFILL REMINDERS', value: _r1, onChanged: (v) => setState(() => _r1 = v)),
                      _divider(r),
                      _ToggleRow(label: 'ORDER UPDATES', value: _r2, onChanged: (v) => setState(() => _r2 = v)),
                      _divider(r),
                      _ToggleRow(label: 'HEALTH ALERTS', value: _r3, onChanged: (v) => setState(() => _r3 = v)),
                    ]),
                  ),

                  const SizedBox(height: 28),

                  // ─── Data & Privacy ─────────────────────
                  const SecLabel('DATA & PRIVACY'),
                  RxCard(
                    padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 18),
                    child: Column(children: [
                      _ActionRow(icon: Icons.verified_user_outlined, label: 'MANAGE CONSENT', onTap: () {}),
                      _divider(r),
                      _ActionRow(icon: Icons.download_rounded, label: 'DOWNLOAD DATA', onTap: () {}),
                      _divider(r),
                      _ActionRow(icon: Icons.delete_outline_rounded, label: 'DELETE ACCOUNT', color: C.err, onTap: () {}),
                    ]),
                  ),

                  const SizedBox(height: 28),

                  // ─── About ──────────────────────────────
                  const SecLabel('ABOUT'),
                  RxCard(
                    padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 18),
                    child: Column(children: [
                      _ActionRow(icon: Icons.info_outline_rounded, label: 'VERSION 1.0.0'),
                      _divider(r),
                      _ActionRow(icon: Icons.description_outlined, label: 'TERMS OF SERVICE', onTap: () {}),
                    ]),
                  ),

                  const SizedBox(height: 32),

                  // ─── Sign Out ───────────────────────────
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
          ),
        );
      },
    );
  }

  String _formatGender(String? g) {
    if (g == null || g.isEmpty) return '—';
    final lower = g.toLowerCase();
    if (lower == 'm' || lower == 'male') return 'Male';
    if (lower == 'f' || lower == 'female') return 'Female';
    if (lower == 'other') return 'Other';
    // Return as-is if it's already a readable format
    return g;
  }

  Widget _divider(Rx r) => Container(height: 1, color: r.border);
}

// ─── Info Row ─────────────────────────────────────────────
class _InfoRow extends StatelessWidget {
  final String label, value;
  const _InfoRow({required this.label, required this.value});
  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 14),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: GoogleFonts.outfit(
              color: r.text3,
              fontSize: 10,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.5,
            ),
          ),
          Flexible(
            child: Text(
              value,
              style: GoogleFonts.outfit(color: r.text1, fontSize: 14),
              textAlign: TextAlign.end,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Health Tag ───────────────────────────────────────────
class _Tag extends StatelessWidget {
  final String text;
  final Color color;
  const _Tag({required this.text, required this.color});
  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    final bg = r.dark ? color.withOpacity(0.12) : color.withOpacity(0.08);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Text(
        text,
        style: GoogleFonts.outfit(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

// ─── Toggle Row ───────────────────────────────────────────
class _ToggleRow extends StatelessWidget {
  final String label;
  final bool value;
  final ValueChanged<bool> onChanged;
  const _ToggleRow({required this.label, required this.value, required this.onChanged});
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: GoogleFonts.outfit(
                color: context.rx.text1,
                fontSize: 12,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.8,
              ),
            ),
            Switch(value: value, onChanged: onChanged),
          ],
        ),
      );
}

// ─── Action Row ───────────────────────────────────────────
class _ActionRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color? color;
  final VoidCallback? onTap;
  const _ActionRow({required this.icon, required this.label, this.color, this.onTap});
  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    final col = color ?? r.text1;
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 14),
        child: Row(children: [
          Icon(icon, color: col, size: 18),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              label,
              style: GoogleFonts.outfit(
                color: col,
                fontSize: 12,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.8,
              ),
            ),
          ),
          if (onTap != null) Icon(Icons.chevron_right_rounded, color: r.text3, size: 18),
        ]),
      ),
    );
  }
}
