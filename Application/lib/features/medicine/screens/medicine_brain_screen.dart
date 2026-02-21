import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/rx_theme_ext.dart';
import '../../../core/widgets/shared_widgets.dart';
import '../bloc/medicine_bloc.dart';

class MedicineBrainScreen extends StatefulWidget {
  const MedicineBrainScreen({super.key});
  @override
  State<MedicineBrainScreen> createState() => _MBS();
}

class _MBS extends State<MedicineBrainScreen> with SingleTickerProviderStateMixin {
  late TabController _t;

  @override
  void initState() {
    super.initState();
    _t = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _t.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return BlocBuilder<MedicineBloc, MedicineState>(
      builder: (context, state) {
        return Scaffold(
          backgroundColor: r.bg,
          body: SafeArea(
            child: Column(children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 20, 24, 0),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('MY', style: GoogleFonts.outfit(color: r.text3, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 2)),
                  Text('Medicines', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 32)),
                ]),
              ),
              const SizedBox(height: 20),
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 24),
                decoration: BoxDecoration(color: r.card, borderRadius: BorderRadius.circular(10), border: Border.all(color: r.border.withOpacity(0.4))),
                child: TabBar(
                  controller: _t,
                  labelColor: C.rx,
                  unselectedLabelColor: r.text3,
                  labelStyle: GoogleFonts.outfit(fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1),
                  unselectedLabelStyle: GoogleFonts.outfit(fontSize: 11, fontWeight: FontWeight.w500, letterSpacing: 1),
                  indicatorColor: C.rx,
                  indicatorWeight: 2,
                  dividerColor: Colors.transparent,
                  tabs: const [Tab(text: 'ACTIVE'), Tab(text: 'LOW'), Tab(text: 'HISTORY')],
                ),
              ),
              const SizedBox(height: 16),
              Expanded(child: TabBarView(controller: _t, children: [_actTab(r, state), _lowTab(r, state), _histTab(r, state)])),
            ]),
          ),
        );
      },
    );
  }

  Widget _actTab(Rx r, MedicineState state) => ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        itemCount: state.activeMeds.length,
        itemBuilder: (_, i) {
          final m = state.activeMeds[i];
          return Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(color: r.card, borderRadius: BorderRadius.circular(14), border: Border.all(color: r.border.withOpacity(0.4))),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Container(width: 7, height: 7, decoration: const BoxDecoration(color: C.ok, shape: BoxShape.circle)),
                const SizedBox(width: 10),
                Expanded(child: Text(m.name, style: GoogleFonts.outfit(color: r.text1, fontSize: 14, fontWeight: FontWeight.w600))),
                if (m.percent < 0.3) Text('REORDER', style: GoogleFonts.outfit(color: C.rx, fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 1)),
              ]),
              const SizedBox(height: 6),
              Padding(padding: const EdgeInsets.only(left: 17), child: Text(m.dosage.toUpperCase(), style: GoogleFonts.outfit(color: r.text3, fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 1))),
              const SizedBox(height: 12),
              SupplyBar(pct: m.percent),
              const SizedBox(height: 6),
              Padding(padding: const EdgeInsets.only(left: 17), child: Text('${m.remaining} OF ${m.total} DAYS', style: GoogleFonts.outfit(color: r.text3, fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 1))),
            ]),
          );
        },
      );

  Widget _lowTab(Rx r, MedicineState state) => ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        itemCount: state.lowMeds.length,
        itemBuilder: (_, i) {
          final m = state.lowMeds[i];
          final c = m.remaining <= 3 ? C.err : C.warn;
          return Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(color: r.card, borderRadius: BorderRadius.circular(14), border: Border.all(color: r.border.withOpacity(0.4))),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Container(width: 7, height: 7, decoration: BoxDecoration(color: c, shape: BoxShape.circle)),
                const SizedBox(width: 10),
                Expanded(child: Text(m.name, style: GoogleFonts.outfit(color: r.text1, fontSize: 14, fontWeight: FontWeight.w600))),
                RxBadge(text: '${m.remaining}D LEFT', color: c),
              ]),
              const SizedBox(height: 12),
              SupplyBar(pct: m.percent),
              const SizedBox(height: 14),
              SizedBox(width: double.infinity, child: RxBtn(label: 'Reorder Now', outlined: true, onPressed: () {})),
            ]),
          );
        },
      );

  Widget _histTab(Rx r, MedicineState state) => ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        itemCount: state.history.length,
        itemBuilder: (_, i) {
          final h = state.history[i];
          return Container(
            margin: const EdgeInsets.only(bottom: 8),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(color: r.card, borderRadius: BorderRadius.circular(12), border: Border.all(color: r.border.withOpacity(0.4))),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(h['n'] ?? '', style: GoogleFonts.outfit(color: r.text2, fontSize: 14)),
              const SizedBox(height: 4),
              Text('${h['d']}  ·  QTY: ${h['q']}  ·  ${h['f']}'.toUpperCase(), style: GoogleFonts.outfit(color: r.text3, fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 0.8)),
            ]),
          );
        },
      );
}
