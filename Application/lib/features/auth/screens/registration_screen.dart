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

class RegistrationScreen extends StatefulWidget {
  const RegistrationScreen({super.key});
  @override
  State<RegistrationScreen> createState() => _RegS();
}

class _RegS extends State<RegistrationScreen> {
  final _n = TextEditingController();
  final _a = TextEditingController();
  final _e = TextEditingController();
  final _al = TextEditingController();
  String? _g;
  final Set<String> _cond = {};
  bool _prefilled = false;

  bool get _ok => _n.text.length >= 2 && _a.text.isNotEmpty && _g != null;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_prefilled) {
      final args = ModalRoute.of(context)?.settings.arguments;
      if (args is Map<String, dynamic>) {
        if (args['name'] != null && _n.text.isEmpty) _n.text = args['name'];
        if (args['email'] != null && _e.text.isEmpty) _e.text = args['email'];
      }
      _prefilled = true;
    }
  }

  @override
  void dispose() {
    _n.dispose();
    _a.dispose();
    _e.dispose();
    _al.dispose();
    super.dispose();
  }

  void _submit() {
    context.read<AuthBloc>().add(RegisterEvent(
          name: _n.text,
          age: int.tryParse(_a.text) ?? 0,
          gender: _g!,
          email: _e.text.isEmpty ? null : _e.text,
          allergies: _al.text.isEmpty ? null : _al.text,
          conditions: _cond.isEmpty ? null : _cond.join(','),
        ));
  }

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return BlocListener<AuthBloc, AuthState>(
      listener: (context, state) {
        if (state is RegisteredState) {
          Navigator.pushNamed(context, AppRoutes.consent);
        } else if (state is AuthError) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(state.message)));
        }
      },
      child: Scaffold(
        backgroundColor: r.bg,
        body: SafeArea(
          child: Column(children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(28, 12, 28, 0),
              child: Row(children: [
                GestureDetector(onTap: () => Navigator.pop(context), child: Icon(Icons.arrow_back_rounded, color: r.text1, size: 24)),
                const Spacer(),
                _dots(0, r),
                const Spacer(),
                const SizedBox(width: 24),
              ]),
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 28),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const SizedBox(height: 32),
                  Text('Complete Your', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 32)),
                  Text('Profile', style: GoogleFonts.dmSerifDisplay(color: C.compute, fontSize: 32)),
                  const SizedBox(height: 8),
                  Text(
                    'WE NEED A FEW DETAILS TO KEEP YOU SAFE',
                    style: GoogleFonts.outfit(color: r.text3, fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 1.5),
                  ),
                  const SizedBox(height: 32),
                  RxInput(label: 'Full Name', hint: 'Enter your full name', ctrl: _n, onChange: (_) => setState(() {})),
                  const SizedBox(height: 20),
                  Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    SizedBox(width: 100, child: RxInput(label: 'Age', hint: 'Age', ctrl: _a, keyboard: TextInputType.number, onChange: (_) => setState(() {}))),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text('GENDER', style: GoogleFonts.outfit(color: r.text3, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1.5)),
                        const SizedBox(height: 8),
                        Row(
                          children: ['Male', 'Female', 'Other'].map((g) {
                            final s = _g == g;
                            return Expanded(
                              child: GestureDetector(
                                onTap: () => setState(() => _g = g),
                                child: Container(
                                  height: 52,
                                  margin: EdgeInsets.only(right: g != 'Other' ? 8 : 0),
                                  decoration: BoxDecoration(
                                    color: s ? C.compute : r.inputBg,
                                    borderRadius: BorderRadius.circular(10),
                                    border: s ? null : Border.all(color: r.inputBorder),
                                  ),
                                  alignment: Alignment.center,
                                  child: Text(g, style: GoogleFonts.outfit(color: s ? Colors.white : r.text1, fontSize: 13, fontWeight: s ? FontWeight.w600 : FontWeight.w400)),
                                ),
                              ),
                            );
                          }).toList(),
                        ),
                      ]),
                    ),
                  ]),
                  const SizedBox(height: 20),
                  RxInput(label: 'Email (Optional)', hint: 'your@email.com', ctrl: _e, keyboard: TextInputType.emailAddress),
                  const SizedBox(height: 20),
                  RxInput(label: 'Known Allergies (Optional)', hint: 'e.g. Penicillin, Sulfa', ctrl: _al, helper: 'Helps us flag unsafe medicines'),
                  const SizedBox(height: 20),
                  Text('CONDITIONS (OPTIONAL)', style: GoogleFonts.outfit(color: r.text3, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1.5)),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: ['Diabetes', 'Hypertension', 'Asthma', 'Thyroid', 'Heart', 'None'].map((c) {
                      final s = _cond.contains(c);
                      return GestureDetector(
                        onTap: () => setState(() {
                          if (c == 'None') {
                            _cond.clear();
                            _cond.add('None');
                          } else {
                            _cond.remove('None');
                            s ? _cond.remove(c) : _cond.add(c);
                          }
                        }),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                          decoration: BoxDecoration(
                            color: s ? C.compute : r.inputBg,
                            borderRadius: BorderRadius.circular(8),
                            border: s ? null : Border.all(color: r.inputBorder),
                          ),
                          child: Text(c, style: GoogleFonts.outfit(color: s ? Colors.white : r.text1, fontSize: 12, fontWeight: s ? FontWeight.w600 : FontWeight.w400)),
                        ),
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 100),
                ]),
              ),
            ),
            Container(
              padding: const EdgeInsets.fromLTRB(28, 12, 28, 16),
              color: r.bg,
              child: BlocBuilder<AuthBloc, AuthState>(
                builder: (context, state) => RxBtn(
                  label: 'Continue',
                  loading: state is AuthLoading,
                  onPressed: _ok ? _submit : null,
                ),
              ),
            ),
          ]),
        ),
      ),
    );
  }

  Widget _dots(int a, Rx r) => Row(
        children: List.generate(
          2,
          (i) => Container(
            width: i == a ? 20 : 8,
            height: 4,
            margin: const EdgeInsets.symmetric(horizontal: 3),
            decoration: BoxDecoration(color: i == a ? C.rx : r.border, borderRadius: BorderRadius.circular(2)),
          ),
        ),
      );
}
