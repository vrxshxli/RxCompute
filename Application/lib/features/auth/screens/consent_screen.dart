import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/rx_theme_ext.dart';
import '../../../core/widgets/shared_widgets.dart';
import '../../../config/routes.dart';

class ConsentScreen extends StatefulWidget {
  const ConsentScreen({super.key});
  @override
  State<ConsentScreen> createState() => _ConS();
}

class _ConS extends State<ConsentScreen> {
  bool _c1 = false, _c2 = false, _c3 = false, _c4 = false;
  bool get _ok => _c1 && _c2;

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return Scaffold(
      backgroundColor: r.bg,
      body: SafeArea(
        child: Column(children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(28, 12, 28, 0),
            child: Row(children: [
              GestureDetector(onTap: () => Navigator.pop(context), child: Icon(Icons.arrow_back_rounded, color: r.text1, size: 24)),
              const Spacer(),
              Row(
                children: List.generate(
                  2,
                  (i) => Container(
                    width: i == 1 ? 20 : 8,
                    height: 4,
                    margin: const EdgeInsets.symmetric(horizontal: 3),
                    decoration: BoxDecoration(color: i == 1 ? C.rx : r.border, borderRadius: BorderRadius.circular(2)),
                  ),
                ),
              ),
              const Spacer(),
              const SizedBox(width: 24),
            ]),
          ),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 28),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const SizedBox(height: 32),
                Text('Data &', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 32)),
                Text('Privacy', style: GoogleFonts.dmSerifDisplay(color: C.compute, fontSize: 32)),
                const SizedBox(height: 8),
                Text('WE NEED YOUR PERMISSION TO KEEP YOU SAFE', style: GoogleFonts.outfit(color: r.text3, fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 1.5)),
                const SizedBox(height: 28),
                _ConsentTile(title: 'Medication Safety Analysis', desc: 'Analyze history for refills, interactions, dosage safety.', req: true, value: _c1, onChanged: (v) => setState(() => _c1 = v)),
                const SizedBox(height: 10),
                _ConsentTile(title: 'Prescription & Order Processing', desc: 'Process prescriptions, verify with pharmacists.', req: true, value: _c2, onChanged: (v) => setState(() => _c2 = v)),
                const SizedBox(height: 10),
                _ConsentTile(title: 'Proactive Notifications', desc: 'Alerts when medication runs low or orders update.', value: _c3, onChanged: (v) => setState(() => _c3 = v)),
                const SizedBox(height: 10),
                _ConsentTile(title: 'Anonymous Improvement', desc: 'Anonymized usage data. No personal info shared.', value: _c4, onChanged: (v) => setState(() => _c4 = v)),
                const SizedBox(height: 24),
                Text('CONSENT V1.0 · FEBRUARY 2026', style: GoogleFonts.outfit(color: r.text3, fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 1.5)),
                const SizedBox(height: 100),
              ]),
            ),
          ),
          Container(
            padding: const EdgeInsets.fromLTRB(28, 12, 28, 16),
            color: r.bg,
            child: RxBtn(
              label: _ok ? 'I Agree & Continue' : 'Accept Required Consents',
              onPressed: _ok ? () => Navigator.pushNamedAndRemoveUntil(context, AppRoutes.home, (_) => false) : null,
            ),
          ),
        ]),
      ),
    );
  }
}

class _ConsentTile extends StatelessWidget {
  final String title, desc;
  final bool req, value;
  final ValueChanged<bool> onChanged;

  const _ConsentTile({required this.title, required this.desc, this.req = false, required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: r.card, borderRadius: BorderRadius.circular(12), border: Border.all(color: r.border.withOpacity(r.dark ? 0.4 : 0.6))),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: GoogleFonts.outfit(color: r.text1, fontSize: 14, fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            Text(desc, style: GoogleFonts.outfit(color: r.text3, fontSize: 13, height: 1.5)),
            if (req)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: RxBadge(text: 'Required', color: C.rx),
              ),
          ]),
        ),
        const SizedBox(width: 10),
        Switch(value: value, onChanged: onChanged),
      ]),
    );
  }
}
