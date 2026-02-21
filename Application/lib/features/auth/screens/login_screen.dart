import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
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
  final _ph = TextEditingController();
  bool _ok = false;
  late AnimationController _fc;

  @override
  void initState() {
    super.initState();
    _fc = AnimationController(vsync: this, duration: const Duration(milliseconds: 700))..forward();
    _ph.addListener(() {
      final v = _ph.text.length == 10;
      if (v != _ok) setState(() => _ok = v);
    });
  }

  @override
  void dispose() {
    _ph.dispose();
    _fc.dispose();
    super.dispose();
  }

  void _sendOtp() {
    context.read<AuthBloc>().add(SendOtpEvent(_ph.text));
  }

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return BlocListener<AuthBloc, AuthState>(
      listener: (context, state) {
        if (state is OtpSentState) {
          Navigator.pushNamed(context, AppRoutes.otp, arguments: {'phone': state.phone, 'otp': state.mockOtp});
        } else if (state is AuthError) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(state.message)));
        }
      },
      child: Scaffold(
        backgroundColor: r.bg,
        body: SafeArea(
          child: FadeTransition(
            opacity: CurvedAnimation(parent: _fc, curve: Curves.easeOut),
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 28),
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: MediaQuery.of(context).size.height - MediaQuery.of(context).padding.vertical),
                child: Column(children: [
                  const SizedBox(height: 72),
                  const RxLogo(size: 30),
                  const SizedBox(height: 8),
                  Text('YOUR AI PHARMACIST', style: GoogleFonts.outfit(color: r.text3, fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 3)),
                  const SizedBox(height: 64),
                  Align(alignment: Alignment.centerLeft, child: Text('PHONE NUMBER', style: GoogleFonts.outfit(color: r.text3, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1.5))),
                  const SizedBox(height: 8),
                  Container(
                    height: 52,
                    decoration: BoxDecoration(color: r.inputBg, borderRadius: BorderRadius.circular(10), border: Border.all(color: r.inputBorder)),
                    child: Row(children: [
                      Padding(
                        padding: const EdgeInsets.only(left: 16, right: 12),
                        child: Row(children: [
                          Text('+91', style: GoogleFonts.outfit(color: r.text3, fontSize: 14, fontWeight: FontWeight.w500)),
                          const SizedBox(width: 12),
                          Container(width: 1, height: 22, color: r.border),
                        ]),
                      ),
                      Expanded(
                        child: TextField(
                          controller: _ph,
                          keyboardType: TextInputType.phone,
                          inputFormatters: [FilteringTextInputFormatter.digitsOnly, LengthLimitingTextInputFormatter(10)],
                          style: GoogleFonts.outfit(color: r.text1, fontSize: 15),
                          decoration: InputDecoration(
                            hintText: 'Enter phone number',
                            hintStyle: TextStyle(color: r.text3),
                            border: InputBorder.none,
                            enabledBorder: InputBorder.none,
                            focusedBorder: InputBorder.none,
                            filled: false,
                            contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 14),
                          ),
                        ),
                      ),
                    ]),
                  ),
                  const SizedBox(height: 20),
                  BlocBuilder<AuthBloc, AuthState>(
                    builder: (context, state) => RxBtn(
                      label: 'Send OTP',
                      loading: state is AuthLoading,
                      onPressed: _ok ? _sendOtp : null,
                    ),
                  ),
                  const SizedBox(height: 40),
                  Row(children: [
                    Expanded(child: Container(height: 1, color: r.border)),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: Text('OR', style: GoogleFonts.outfit(color: r.text3, fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 2)),
                    ),
                    Expanded(child: Container(height: 1, color: r.border)),
                  ]),
                  const SizedBox(height: 40),
                  RxBtn(label: 'Continue with Google', outlined: true, icon: Icons.g_mobiledata_rounded, onPressed: () => Navigator.pushNamed(context, AppRoutes.register)),
                  const Spacer(),
                  Padding(
                    padding: const EdgeInsets.only(bottom: 20),
                    child: Text('By continuing, you agree to our Terms & Privacy Policy', style: TextStyle(color: r.text3, fontSize: 11), textAlign: TextAlign.center),
                  ),
                ]),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
