import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/rx_theme_ext.dart';
import '../../../core/widgets/shared_widgets.dart';
import '../../../config/routes.dart';
import '../bloc/home_bloc.dart';

class HomeTab extends StatelessWidget {
  const HomeTab({super.key});

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return BlocBuilder<HomeBloc, HomeState>(
      builder: (context, state) {
        final p = state.user;
        final al = state.alerts.isNotEmpty ? state.alerts.first : null;
        return Scaffold(
          backgroundColor: r.bg,
          body: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(24, 20, 24, 32),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text('GOOD ${_gr().toUpperCase()}', style: GoogleFonts.outfit(color: r.text3, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 2)),
                      const SizedBox(height: 4),
                      Text(p?.firstName ?? 'User', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 36, height: 1.05)),
                    ]),
                  ),
                  GestureDetector(
                    onTap: () => Navigator.pushNamed(context, AppRoutes.notifications),
                    child: Container(
                      width: 46,
                      height: 46,
                      decoration: BoxDecoration(color: r.card, borderRadius: BorderRadius.circular(12), border: Border.all(color: r.border.withOpacity(0.4))),
                      child: Stack(children: [
                        Center(child: Icon(Icons.notifications_none_rounded, color: r.text1, size: 20)),
                        Positioned(top: 11, right: 13, child: Container(width: 7, height: 7, decoration: const BoxDecoration(color: C.rx, shape: BoxShape.circle))),
                      ]),
                    ),
                  ),
                ]),
                const SizedBox(height: 32),

                _Tile(
                  ic: Icons.medication_rounded,
                  cl: C.compute,
                  t: "TODAY'S MEDICATIONS",
                  s: state.activeMeds.isEmpty ? 'No medications yet. Tap to add.' : '${state.activeMeds.length} medications scheduled',
                  trail: Icon(Icons.chevron_right_rounded, color: r.text3, size: 20),
                  onTap: () => _showAddMedicationSheet(context),
                ),
                const SizedBox(height: 10),
                _Tile(
                  ic: Icons.schedule_rounded,
                  cl: al != null && al.daysLeft <= 5 ? C.warn : C.ok,
                  t: 'REFILL ALERT',
                  s: al != null ? '${al.medicine} — ${al.daysLeft} days left' : 'All stocked',
                  sColor: al != null && al.daysLeft <= 5 ? C.warn : C.ok,
                  trail: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
                    decoration: BoxDecoration(color: C.rx.withOpacity(r.dark ? 0.08 : 0.05), borderRadius: BorderRadius.circular(8)),
                    child: Text('REORDER', style: GoogleFonts.outfit(color: C.rx, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1)),
                  ),
                  onTap: () => _showAddMedicationSheet(context),
                ),
                const SizedBox(height: 10),
                _Tile(ic: Icons.auto_graph_rounded, cl: C.ok, t: 'MONTHLY INSIGHT', s: state.monthlyInsight),
                const SizedBox(height: 36),

                const SecLabel('QUICK ACTIONS'),
                Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                  _QA(ic: Icons.document_scanner_rounded, lb: 'UPLOAD RX', fn: () {}),
                  _QA(ic: Icons.local_shipping_outlined, lb: 'TRACK', fn: () => Navigator.pushNamed(context, AppRoutes.orderTracking)),
                  _QA(ic: Icons.receipt_long_rounded, lb: 'HISTORY', fn: () => Navigator.pushNamed(context, AppRoutes.orderHistory)),
                  _QA(ic: Icons.phone_in_talk_rounded, lb: 'SOS', fn: () {}),
                ]),
                const SizedBox(height: 36),

                if (state.orders.any((o) => o.status.isActive)) ...[
                  const SecLabel('ACTIVE ORDER'),
                  Builder(builder: (_) {
                    final o = state.orders.firstWhere((o) => o.status.isActive);
                    return RxCard(
                      onTap: () => Navigator.pushNamed(context, AppRoutes.orderTracking),
                      child: Row(children: [
                        IcoBlock(icon: Icons.local_shipping_rounded, color: C.compute),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Mono(o.orderUid),
                            const SizedBox(height: 4),
                            Text('${o.items.length} items · ${o.formattedTotal}', style: GoogleFonts.outfit(color: r.text1, fontSize: 14, fontWeight: FontWeight.w500)),
                          ]),
                        ),
                        RxBadge(text: o.status.label, color: C.compute),
                      ]),
                    );
                  }),
                ],
              ]),
            ),
          ),
        );
      },
    );
  }

  String _gr() {
    final h = DateTime.now().hour;
    return h < 12 ? 'morning' : h < 17 ? 'afternoon' : 'evening';
  }

  Future<void> _showAddMedicationSheet(BuildContext context) async {
    final nameCtrl = TextEditingController();
    final dosageCtrl = TextEditingController();
    final freqCtrl = TextEditingController(text: '1');
    final qtyCtrl = TextEditingController(text: '30');

    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) {
        final r = context.rx;
        return Padding(
          padding: EdgeInsets.fromLTRB(16, 16, 16, MediaQuery.of(ctx).viewInsets.bottom + 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Add Medication', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 24)),
              const SizedBox(height: 12),
              TextField(controller: nameCtrl, decoration: const InputDecoration(labelText: 'Medicine Name')),
              TextField(controller: dosageCtrl, decoration: const InputDecoration(labelText: 'Dosage (example: 1 tablet)')),
              TextField(controller: freqCtrl, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Times per day')),
              TextField(controller: qtyCtrl, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Available units')),
              const SizedBox(height: 16),
              RxBtn(
                label: 'Save Medication',
                onPressed: () {
                  final freq = int.tryParse(freqCtrl.text.trim()) ?? 1;
                  final qty = int.tryParse(qtyCtrl.text.trim()) ?? 30;
                  if (nameCtrl.text.trim().isEmpty || dosageCtrl.text.trim().isEmpty) return;
                  context.read<HomeBloc>().add(
                        AddMedicationEvent(
                          medicineName: nameCtrl.text.trim(),
                          dosageInstruction: dosageCtrl.text.trim(),
                          frequencyPerDay: freq < 1 ? 1 : freq,
                          quantityUnits: qty < 1 ? 1 : qty,
                        ),
                      );
                  Navigator.pop(ctx);
                },
              ),
            ],
          ),
        );
      },
    );
  }
}

class _Tile extends StatelessWidget {
  final IconData ic;
  final Color cl;
  final String t, s;
  final Color? sColor;
  final Widget? trail;
  final VoidCallback? onTap;
  const _Tile({required this.ic, required this.cl, required this.t, required this.s, this.sColor, this.trail, this.onTap});
  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return GestureDetector(
      onTap: onTap,
      child: RxCard(
        child: Row(children: [
          IcoBlock(icon: ic, color: cl),
          const SizedBox(width: 14),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(t, style: GoogleFonts.outfit(color: r.text3, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1.2)),
              const SizedBox(height: 4),
              Text(s, style: GoogleFonts.outfit(color: sColor ?? r.text2, fontSize: 13)),
            ]),
          ),
          if (trail != null) trail!,
        ]),
      ),
    );
  }
}

class _QA extends StatelessWidget {
  final IconData ic;
  final String lb;
  final VoidCallback fn;
  const _QA({required this.ic, required this.lb, required this.fn});
  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return GestureDetector(
      onTap: fn,
      child: Column(children: [
        Container(
          width: 56,
          height: 56,
          decoration: BoxDecoration(color: r.card, borderRadius: BorderRadius.circular(14), border: Border.all(color: r.border.withOpacity(0.4))),
          child: Icon(ic, color: r.text1, size: 20),
        ),
        const SizedBox(height: 6),
        Text(lb, style: GoogleFonts.outfit(color: r.text3, fontSize: 9, fontWeight: FontWeight.w700, letterSpacing: 1)),
      ]),
    );
  }
}
