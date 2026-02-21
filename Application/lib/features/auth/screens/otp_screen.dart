import 'dart:async';
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

class OtpScreen extends StatefulWidget {
  const OtpScreen({super.key});
  @override
  State<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends State<OtpScreen> {
  // Single controller for the hidden field — much more reliable than 6 separate ones
  final _otpCtrl = TextEditingController();
  final _otpFocus = FocusNode();

  String _phone = '';
  String? _mockOtp;
  int _resendTimer = 30;
  Timer? _timer;

  String get _otp => _otpCtrl.text;
  bool get _otpValid => _otp.length == 6;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_phone.isEmpty) {
      final args = ModalRoute.of(context)?.settings.arguments;
      if (args is Map<String, dynamic>) {
        _phone = args['phone'] ?? '';
        _mockOtp = args['mockOtp'];
      }
      _startTimer();
      // Auto-focus OTP input
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _otpFocus.requestFocus();
      });
    }
  }

  void _startTimer() {
    _resendTimer = 30;
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (t) {
      if (_resendTimer <= 0) {
        t.cancel();
      } else {
        setState(() => _resendTimer--);
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _otpCtrl.dispose();
    _otpFocus.dispose();
    super.dispose();
  }

  void _verifyOtp() {
    if (_otpValid) {
      context.read<AuthBloc>().add(
            VerifyOtpEvent(phone: _phone, otp: _otp),
          );
    }
  }

  void _resendOtp() {
    // Clear old OTP
    _otpCtrl.clear();
    setState(() {});
    context.read<AuthBloc>().add(SendOtpEvent(phone: _phone));
    _startTimer();
  }

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return BlocListener<AuthBloc, AuthState>(
      listener: (context, state) {
        if (state is OtpSentState) {
          _mockOtp = state.mockOtp;
          setState(() {});
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: const Text('OTP resent successfully'),
              backgroundColor: C.ok,
              behavior: SnackBarBehavior.floating,
            ),
          );
        } else if (state is OtpVerifiedState) {
          if (state.isRegistered) {
            Navigator.pushNamedAndRemoveUntil(
                context, AppRoutes.home, (_) => false);
          } else {
            Navigator.pushNamed(context, AppRoutes.register, arguments: {
              'name': state.name,
              'email': state.email,
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
          child: Column(
            children: [
              // ─── Top bar ──────────────────────────────
              Padding(
                padding: const EdgeInsets.fromLTRB(28, 12, 28, 0),
                child: Row(
                  children: [
                    GestureDetector(
                      onTap: () => Navigator.pop(context),
                      child: Icon(Icons.arrow_back_rounded,
                          color: r.text1, size: 24),
                    ),
                    const Spacer(),
                  ],
                ),
              ),

              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(horizontal: 28),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 32),

                      // ─── Title ────────────────────────
                      Text(
                        'Verify Your',
                        style: GoogleFonts.dmSerifDisplay(
                          color: r.text1,
                          fontSize: 32,
                        ),
                      ),
                      Text(
                        'Number',
                        style: GoogleFonts.dmSerifDisplay(
                          color: C.compute,
                          fontSize: 32,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'Enter the 6-digit code sent to $_phone',
                        style: GoogleFonts.outfit(
                          color: r.text2,
                          fontSize: 14,
                          height: 1.5,
                        ),
                      ),

                      // ─── Mock OTP (dev only) ──────────
                      if (_mockOtp != null) ...[
                        const SizedBox(height: 12),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 14, vertical: 8),
                          decoration: BoxDecoration(
                            color: r.warnBg,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            'Dev OTP: $_mockOtp',
                            style: GoogleFonts.jetBrainsMono(
                              color: C.warn,
                              fontSize: 14,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      ],

                      const SizedBox(height: 40),

                      // ─── OTP Display Boxes ────────────
                      // Hidden text field that captures all input
                      SizedBox(
                        height: 0,
                        child: TextField(
                          controller: _otpCtrl,
                          focusNode: _otpFocus,
                          keyboardType: TextInputType.number,
                          maxLength: 6,
                          inputFormatters: [
                            FilteringTextInputFormatter.digitsOnly,
                          ],
                          decoration: const InputDecoration(
                            counterText: '',
                            border: InputBorder.none,
                            enabledBorder: InputBorder.none,
                            focusedBorder: InputBorder.none,
                          ),
                          onChanged: (val) {
                            setState(() {});
                            if (val.length == 6) {
                              _verifyOtp(); // Auto-verify when 6 digits entered
                            }
                          },
                        ),
                      ),

                      // Visual OTP boxes (tap to focus hidden field)
                      GestureDetector(
                        onTap: () => _otpFocus.requestFocus(),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: List.generate(6, (i) {
                            final filled = i < _otp.length;
                            final active = i == _otp.length && _otpFocus.hasFocus;
                            return AnimatedContainer(
                              duration: const Duration(milliseconds: 150),
                              width: 50,
                              height: 60,
                              decoration: BoxDecoration(
                                color: filled
                                    ? (r.dark ? C.d3 : C.l2)
                                    : r.inputBg,
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(
                                  color: active
                                      ? C.rx
                                      : filled
                                          ? C.compute.withOpacity(0.5)
                                          : r.inputBorder,
                                  width: active ? 2 : 1,
                                ),
                              ),
                              alignment: Alignment.center,
                              child: filled
                                  ? Text(
                                      _otp[i],
                                      style: GoogleFonts.jetBrainsMono(
                                        color: r.text1,
                                        fontSize: 24,
                                        fontWeight: FontWeight.w700,
                                      ),
                                    )
                                  : active
                                      ? Container(
                                          width: 2,
                                          height: 24,
                                          color: C.rx,
                                        )
                                      : const SizedBox.shrink(),
                            );
                          }),
                        ),
                      ),

                      const SizedBox(height: 32),

                      // ─── Verify Button ────────────────
                      BlocBuilder<AuthBloc, AuthState>(
                        builder: (context, state) {
                          return RxBtn(
                            label: 'Verify OTP',
                            loading: state is AuthLoading,
                            onPressed: _otpValid ? _verifyOtp : null,
                          );
                        },
                      ),

                      const SizedBox(height: 24),

                      // ─── Resend ───────────────────────
                      Center(
                        child: _resendTimer > 0
                            ? Text(
                                'Resend OTP in ${_resendTimer}s',
                                style: GoogleFonts.outfit(
                                  color: r.text3,
                                  fontSize: 13,
                                ),
                              )
                            : GestureDetector(
                                onTap: _resendOtp,
                                child: Text(
                                  'Resend OTP',
                                  style: GoogleFonts.outfit(
                                    color: C.rx,
                                    fontSize: 13,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
