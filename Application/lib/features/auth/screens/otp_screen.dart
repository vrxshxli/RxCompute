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
  State<OtpScreen> createState() => _OtpS();
}

class _OtpS extends State<OtpScreen> {
  final _c = List.generate(6, (_) => TextEditingController());
  final _f = List.generate(6, (_) => FocusNode());
  int _cd = 30;
  Timer? _t;
  String _phone = '';

  @override
  void initState() {
    super.initState();
    _startT();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final args = ModalRoute.of(context)?.settings.arguments;
      if (args is Map<String, dynamic>) {
        _phone = args['phone'] ?? '';
      }
      _f[0].requestFocus();
    });
  }

  void _startT() {
    _cd = 30;
    _t?.cancel();
    _t = Timer.periodic(const Duration(seconds: 1), (t) {
      if (_cd <= 0) {
        t.cancel();
      } else {
        setState(() => _cd--);
      }
    });
  }

  bool get _filled => _c.every((c) => c.text.length == 1);

  void _ch(int i, String v) {
    if (v.isNotEmpty && i < 5) _f[i + 1].requestFocus();
    if (_filled) _verify();
  }

  void _verify() {
    final otp = _c.map((c) => c.text).join();
    context.read<AuthBloc>().add(VerifyOtpEvent(_phone, otp));
  }

  @override
  void dispose() {
    _t?.cancel();
    for (final c in _c) c.dispose();
    for (final f in _f) f.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return BlocListener<AuthBloc, AuthState>(
      listener: (context, state) {
        if (state is OtpVerifiedState) {
          if (state.isRegistered) {
            Navigator.pushNamedAndRemoveUntil(context, AppRoutes.home, (_) => false);
          } else {
            Navigator.pushReplacementNamed(context, AppRoutes.register);
          }
        } else if (state is AuthError) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(state.message)));
        }
      },
      child: Scaffold(
        backgroundColor: r.bg,
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 28),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const SizedBox(height: 12),
              GestureDetector(onTap: () => Navigator.pop(context), child: Icon(Icons.arrow_back_rounded, color: r.text1, size: 24)),
              const SizedBox(height: 40),
              Text('Verify', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 36)),
              Text('Phone', style: GoogleFonts.dmSerifDisplay(color: C.compute, fontSize: 36)),
              const SizedBox(height: 10),
              Text('CODE SENT TO +91 ${_phone.length >= 5 ? '${_phone.substring(0, 2)}XXX XX${_phone.substring(_phone.length - 3)}' : _phone}',
                  style: GoogleFonts.outfit(color: r.text3, fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 1.5)),
              const SizedBox(height: 44),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(6, (i) {
                  final focused = _f[i].hasFocus;
                  return Container(
                    width: 48,
                    height: 56,
                    margin: EdgeInsets.only(right: i < 5 ? 10 : 0),
                    decoration: BoxDecoration(
                      color: r.inputBg,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: focused ? C.compute : r.inputBorder, width: focused ? 1.5 : 1),
                    ),
                    child: TextField(
                      controller: _c[i],
                      focusNode: _f[i],
                      keyboardType: TextInputType.number,
                      textAlign: TextAlign.center,
                      maxLength: 1,
                      onChanged: (v) => _ch(i, v),
                      inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                      style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 24),
                      decoration: const InputDecoration(counterText: '', border: InputBorder.none, filled: false, contentPadding: EdgeInsets.zero),
                    ),
                  );
                }),
              ),
              const SizedBox(height: 36),
              BlocBuilder<AuthBloc, AuthState>(
                builder: (context, state) => RxBtn(label: 'Verify', onPressed: _filled ? _verify : null, loading: state is AuthLoading),
              ),
              const SizedBox(height: 24),
              Center(
                child: _cd > 0
                    ? Text('RESEND IN ${_cd}s', style: GoogleFonts.outfit(color: r.text3, fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 1.5))
                    : GestureDetector(
                        onTap: () {
                          _startT();
                          context.read<AuthBloc>().add(SendOtpEvent(_phone));
                        },
                        child: Text('RESEND CODE', style: GoogleFonts.outfit(color: C.compute, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1.5)),
                      ),
              ),
            ]),
          ),
        ),
      ),
    );
  }
}
