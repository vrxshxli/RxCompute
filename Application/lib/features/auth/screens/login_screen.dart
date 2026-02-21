import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/rx_theme_ext.dart';
import '../../../core/widgets/shared_widgets.dart';
import '../../../config/routes.dart';
import '../bloc/auth_bloc.dart';
import '../bloc/auth_event.dart';
import '../bloc/auth_state.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _S();
}

class _S extends State<LoginScreen> with SingleTickerProviderStateMixin {
  late AnimationController _fc;

  @override
  void initState() {
    super.initState();
    _fc = AnimationController(vsync: this, duration: const Duration(milliseconds: 700))..forward();
  }

  @override
  void dispose() {
    _fc.dispose();
    super.dispose();
  }

  void _googleSignIn() {
    context.read<AuthBloc>().add(GoogleSignInEvent());
  }

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return BlocListener<AuthBloc, AuthState>(
      listener: (context, state) {
        if (state is GoogleSignInSuccess) {
          if (state.isRegistered) {
            // Existing user — go straight home
            Navigator.pushNamedAndRemoveUntil(context, AppRoutes.home, (_) => false);
          } else {
            // New user — collect details
            Navigator.pushNamed(context, AppRoutes.register, arguments: {
              'name': state.name,
              'email': state.email,
              'profilePicture': state.profilePicture,
            });
          }
        } else if (state is AuthError) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(state.message),
              backgroundColor: C.err,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      },
      child: Scaffold(
        backgroundColor: r.bg,
        body: SafeArea(
          child: FadeTransition(
            opacity: CurvedAnimation(parent: _fc, curve: Curves.easeOut),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 28),
              child: Column(children: [
                const Spacer(flex: 2),

                // ─── Logo ─────────────────────────────────
                const RxLogo(size: 36),
                const SizedBox(height: 8),
                Text(
                  'YOUR AI PHARMACIST',
                  style: GoogleFonts.outfit(
                    color: r.text3,
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 3,
                  ),
                ),

                const SizedBox(height: 48),

                // ─── Welcome text ─────────────────────────
                Text(
                  'Welcome',
                  style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 32),
                ),
                const SizedBox(height: 8),
                Text(
                  'Sign in to manage your medicines,\ntrack orders & chat with AI',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.outfit(
                    color: r.text2,
                    fontSize: 14,
                    height: 1.5,
                  ),
                ),

                const Spacer(flex: 2),

                // ─── Google Sign-In Button ────────────────
                BlocBuilder<AuthBloc, AuthState>(
                  builder: (context, state) {
                    final loading = state is AuthLoading;
                    return GestureDetector(
                      onTap: loading ? null : _googleSignIn,
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        height: 56,
                        decoration: BoxDecoration(
                          color: r.card,
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: r.border),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(r.dark ? 0.3 : 0.06),
                              blurRadius: 12,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: loading
                            ? const Center(child: SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.5)))
                            : Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  // Google "G" icon
                                  Container(
                                    width: 28,
                                    height: 28,
                                    decoration: BoxDecoration(
                                      color: Colors.white,
                                      borderRadius: BorderRadius.circular(6),
                                    ),
                                    child: Center(
                                      child: Text(
                                        'G',
                                        style: GoogleFonts.outfit(
                                          fontSize: 18,
                                          fontWeight: FontWeight.w700,
                                          color: const Color(0xFF4285F4),
                                        ),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 14),
                                  Text(
                                    'Continue with Google',
                                    style: GoogleFonts.outfit(
                                      color: r.text1,
                                      fontSize: 15,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                      ),
                    );
                  },
                ),

                const SizedBox(height: 32),

                // ─── Terms ────────────────────────────────
                Padding(
                  padding: const EdgeInsets.only(bottom: 24),
                  child: Text(
                    'By continuing, you agree to our Terms & Privacy Policy',
                    style: TextStyle(color: r.text3, fontSize: 11),
                    textAlign: TextAlign.center,
                  ),
                ),
              ]),
            ),
          ),
        ),
      ),
    );
  }
}
