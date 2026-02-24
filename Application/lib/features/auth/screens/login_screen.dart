import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/rx_theme_ext.dart';
import '../../../core/widgets/shared_widgets.dart';
import '../../../config/routes.dart';
import '../../../data/repositories/auth_repository.dart';
import '../bloc/auth_bloc.dart';
import '../bloc/auth_event.dart';
import '../bloc/auth_state.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _fadeCtrl;
  final _phoneCtrl = TextEditingController();
  final AuthRepository _authRepo = AuthRepository();

  bool get _phoneValid => _phoneCtrl.text.replaceAll(RegExp(r'\D'), '').length >= 10;

  @override
  void initState() {
    super.initState();
    _fadeCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 700),
    )..forward();
    _authRepo.warmupIfNeeded();
  }

  @override
  void dispose() {
    _fadeCtrl.dispose();
    _phoneCtrl.dispose();
    super.dispose();
  }

  void _sendOtp() {
    final phone = _phoneCtrl.text.trim();
    context.read<AuthBloc>().add(SendOtpEvent(phone: phone));
  }

  void _googleSignIn() {
    context.read<AuthBloc>().add(GoogleSignInEvent());
  }

  void _handleAuthSuccess(BuildContext context, {
    required bool isRegistered,
    String? name,
    String? email,
    String? profilePicture,
  }) {
    if (isRegistered) {
      Navigator.pushNamedAndRemoveUntil(context, AppRoutes.home, (_) => false);
    } else {
      Navigator.pushNamed(context, AppRoutes.register, arguments: {
        'name': name,
        'email': email,
        'profilePicture': profilePicture,
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return BlocListener<AuthBloc, AuthState>(
      listener: (context, state) {
        if (state is OtpSentState) {
          Navigator.pushNamed(context, AppRoutes.otp, arguments: {
            'phone': state.phone,
            'mockOtp': state.mockOtp,
          });
        } else if (state is GoogleSignInSuccess) {
          _handleAuthSuccess(
            context,
            isRegistered: state.isRegistered,
            name: state.name,
            email: state.email,
            profilePicture: state.profilePicture,
          );
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
            opacity: CurvedAnimation(parent: _fadeCtrl, curve: Curves.easeOut),
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 28),
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  minHeight: MediaQuery.of(context).size.height -
                      MediaQuery.of(context).padding.vertical,
                ),
                child: Column(
                  children: [
                    const SizedBox(height: 72),

                    // ─── Logo ─────────────────────────────
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

                    // ─── Welcome ──────────────────────────
                    Text(
                      'Welcome',
                      style: GoogleFonts.dmSerifDisplay(
                        color: r.text1,
                        fontSize: 32,
                      ),
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

                    const SizedBox(height: 40),

                    // ─── Phone Number Input ───────────────
                    RxInput(
                      label: 'Phone Number',
                      hint: 'Enter your 10-digit number',
                      ctrl: _phoneCtrl,
                      keyboard: TextInputType.phone,
                      onChange: (_) => setState(() {}),
                    ),

                    const SizedBox(height: 20),

                    // ─── Send OTP Button ──────────────────
                    BlocBuilder<AuthBloc, AuthState>(
                      builder: (context, state) {
                        final loading = state is AuthLoading;
                        return RxBtn(
                          label: 'Send OTP',
                          loading: loading,
                          onPressed: _phoneValid ? _sendOtp : null,
                        );
                      },
                    ),

                    const SizedBox(height: 28),

                    // ─── OR Divider ───────────────────────
                    Row(
                      children: [
                        Expanded(
                          child: Container(
                            height: 1,
                            color: r.border,
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          child: Text(
                            'OR',
                            style: GoogleFonts.outfit(
                              color: r.text3,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              letterSpacing: 1.5,
                            ),
                          ),
                        ),
                        Expanded(
                          child: Container(
                            height: 1,
                            color: r.border,
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 28),

                    // ─── Google Sign-In Button ────────────
                    BlocBuilder<AuthBloc, AuthState>(
                      builder: (context, state) {
                        final loading = state is AuthLoading;
                        return GestureDetector(
                          onTap: loading ? null : _googleSignIn,
                          child: Container(
                            height: 56,
                            decoration: BoxDecoration(
                              color: r.card,
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(color: r.border),
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.black
                                      .withOpacity(r.dark ? 0.3 : 0.06),
                                  blurRadius: 12,
                                  offset: const Offset(0, 4),
                                ),
                              ],
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
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

                    const SizedBox(height: 48),

                    // ─── Terms ────────────────────────────
                    Padding(
                      padding: const EdgeInsets.only(bottom: 24),
                      child: Text(
                        'By continuing, you agree to our Terms & Privacy Policy',
                        style: TextStyle(color: r.text3, fontSize: 11),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
