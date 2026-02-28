import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/rx_theme_ext.dart';
import '../../../core/widgets/shared_widgets.dart';
import '../../../config/routes.dart';
import '../../../data/repositories/prediction_repository.dart';
import '../bloc/home_bloc.dart';

class HomeTab extends StatelessWidget {
  const HomeTab({super.key});
  static final PredictionRepository _predictionRepository = PredictionRepository();

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return BlocConsumer<HomeBloc, HomeState>(
      listener: (context, state) {
        if (state.error != null && state.error!.isNotEmpty) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(state.error!), backgroundColor: C.err),
          );
        }
      },
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
                  onTrailTap: () => _showMedicationListSheet(context, state.activeMeds),
                ),
                const SizedBox(height: 14),
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
                  onTap: () => _showRefillListSheet(context, state),
                  onTrailTap: () {
                    final target = al?.medicine ?? (state.activeMeds.isNotEmpty ? state.activeMeds.first.name : null);
                    if (target == null) return;
                    _showRefillConfirmDialog(context, medicineName: target, medicineId: al?.medicineId);
                  },
                ),
                const SizedBox(height: 14),
                _Tile(
                  ic: Icons.auto_graph_rounded,
                  cl: C.ok,
                  t: 'MONTHLY INSIGHT',
                  s: state.monthlyInsight,
                  onTap: () => _showMonthlyInsightsSheet(context, state),
                ),
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
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Add Medication', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 24)),
                const SizedBox(height: 4),
                Text(
                  'Refill alerts ke liye dosage aur daily frequency zaroor bharein.',
                  style: GoogleFonts.outfit(color: r.text3, fontSize: 12),
                ),
                const SizedBox(height: 14),
                TextField(controller: nameCtrl, decoration: const InputDecoration(labelText: 'Medicine Name')),
                const SizedBox(height: 12),
                TextField(controller: dosageCtrl, decoration: const InputDecoration(labelText: 'Dosage (example: 1 tablet)')),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: freqCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'Times per day'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: TextField(
                        controller: qtyCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'Available units'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
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
          ),
        );
      },
    );
  }

  Future<void> _showMedicationListSheet(BuildContext context, List<dynamic> meds) async {
    final r = context.rx;
    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => Container(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.75),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('My Medications', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 24)),
            const SizedBox(height: 12),
            Expanded(
              child: meds.isEmpty
                  ? const Center(child: Text('No medications added yet'))
                  : ListView.separated(
                      itemCount: meds.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 10),
                      itemBuilder: (_, i) {
                        final m = meds[i];
                        return RxCard(
                          padding: const EdgeInsets.all(14),
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text(m.name, style: GoogleFonts.outfit(color: r.text1, fontSize: 14, fontWeight: FontWeight.w600)),
                            const SizedBox(height: 4),
                            Text(m.dosage, style: GoogleFonts.outfit(color: r.text3, fontSize: 12)),
                          ]),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showRefillListSheet(BuildContext context, HomeState state) async {
    final r = context.rx;
    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => Container(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.78),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Refill Alerts', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 24)),
            const SizedBox(height: 12),
            Expanded(
              child: ListView(
                children: [
                  ...state.alerts.map(
                    (a) => Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: RxCard(
                        padding: const EdgeInsets.all(14),
                        child: Row(
                          children: [
                            IcoBlock(icon: Icons.schedule_rounded, color: a.daysLeft <= 5 ? C.warn : C.ok),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                Text(a.medicine, style: GoogleFonts.outfit(color: r.text1, fontSize: 14, fontWeight: FontWeight.w600)),
                                Text('${a.daysLeft} days left', style: GoogleFonts.outfit(color: r.text3, fontSize: 12)),
                              ]),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                  if (state.alerts.isEmpty)
                    const Padding(
                      padding: EdgeInsets.only(bottom: 12),
                      child: Text('No refill alerts right now.'),
                    ),
                  const SecLabel('EXISTING MEDICATIONS'),
                  ...state.activeMeds.map(
                    (m) => Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: RxCard(
                        padding: const EdgeInsets.all(14),
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text(m.name, style: GoogleFonts.outfit(color: r.text1, fontSize: 14, fontWeight: FontWeight.w600)),
                          const SizedBox(height: 3),
                          Text(m.dosage, style: GoogleFonts.outfit(color: r.text3, fontSize: 12)),
                        ]),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showRefillConfirmDialog(
    BuildContext context, {
    required String medicineName,
    int? medicineId,
  }) async {
    final qtyCtrl = TextEditingController(text: '1');
    bool confirmed = false;
    await showDialog(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setStateDialog) {
            return AlertDialog(
              title: const Text('Confirm Refill'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Medicine: $medicineName'),
                  const SizedBox(height: 10),
                  TextField(
                    controller: qtyCtrl,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(labelText: 'Quantity (units/strips)'),
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Checkbox(
                        value: confirmed,
                        onChanged: (v) => setStateDialog(() => confirmed = v == true),
                      ),
                      const Expanded(
                        child: Text('I confirm refill order creation.'),
                      ),
                    ],
                  ),
                ],
              ),
              actions: [
                TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
                ElevatedButton(
                  onPressed: !confirmed
                      ? null
                      : () async {
                          final qty = int.tryParse(qtyCtrl.text.trim()) ?? 1;
                          try {
                            final res = await _predictionRepository.confirmRefill(
                              medicineId: medicineId,
                              medicineName: medicineId == null ? medicineName : null,
                              quantityUnits: qty < 1 ? 1 : qty,
                              confirmationSource: 'popup',
                            );
                            if (context.mounted) {
                              Navigator.pop(ctx);
                              context.read<HomeBloc>().add(LoadHomeDataEvent());
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text('Refill order created: ${res['order_uid'] ?? ''}'),
                                  backgroundColor: C.ok,
                                ),
                              );
                            }
                          } catch (e) {
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(
                                    'Refill confirmation failed: ${e.toString().replaceAll('Exception: ', '')}',
                                  ),
                                  backgroundColor: C.err,
                                ),
                              );
                            }
                          }
                        },
                  child: const Text('Confirm'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Future<void> _showMonthlyInsightsSheet(BuildContext context, HomeState state) async {
    final r = context.rx;
    final delivered = state.orders.where((o) => o.status.name == 'delivered').toList();
    final buckets = <double>[0, 0, 0, 0];
    for (var i = 0; i < state.orders.length; i++) {
      buckets[i % 4] += state.orders[i].total;
    }
    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => Container(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Monthly Insights', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 24)),
            const SizedBox(height: 10),
            RxCard(
              padding: const EdgeInsets.all(14),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: List.generate(4, (i) {
                  final max = buckets.fold<double>(0, (p, c) => p > c ? p : c);
                  final h = max == 0 ? 8.0 : (70 * (buckets[i] / max)).clamp(8.0, 70.0);
                  return Expanded(
                    child: Column(
                      children: [
                        Container(width: 22, height: h, decoration: BoxDecoration(color: C.compute, borderRadius: BorderRadius.circular(6))),
                        const SizedBox(height: 6),
                        Text('W${i + 1}', style: GoogleFonts.outfit(color: r.text3, fontSize: 10)),
                      ],
                    ),
                  );
                }),
              ),
            ),
            const SizedBox(height: 14),
            Expanded(
              child: delivered.isEmpty
                  ? const Center(child: Text('No monthly order list yet'))
                  : ListView.separated(
                      itemCount: delivered.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 10),
                      itemBuilder: (_, i) {
                        final o = delivered[i];
                        return RxCard(
                          padding: const EdgeInsets.all(14),
                          child: Row(
                            children: [
                              Expanded(child: Mono(o.orderUid, size: 12, color: r.text1)),
                              Text(o.formattedTotal, style: GoogleFonts.outfit(color: r.text1, fontWeight: FontWeight.w700)),
                            ],
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
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
  final VoidCallback? onTrailTap;
  const _Tile({required this.ic, required this.cl, required this.t, required this.s, this.sColor, this.trail, this.onTap, this.onTrailTap});
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
          if (trail != null)
            GestureDetector(
              onTap: onTrailTap,
              child: trail!,
            ),
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
