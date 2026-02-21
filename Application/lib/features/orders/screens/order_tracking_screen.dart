import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/rx_theme_ext.dart';
import '../../../core/widgets/shared_widgets.dart';
import '../../../data/mock_data.dart';
import '../bloc/order_bloc.dart';

class OrderTrackingScreen extends StatelessWidget {
  const OrderTrackingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return BlocBuilder<OrderBloc, OrderState>(
      builder: (context, state) {
        final o = state.activeOrder ?? MockData.orders.first;
        final steps = MockData.orderSteps;
        return Scaffold(
          backgroundColor: r.bg,
          appBar: AppBar(
            backgroundColor: r.bg,
            leading: IconButton(icon: Icon(Icons.arrow_back_rounded, color: r.text1), onPressed: () => Navigator.pop(context)),
            title: Text('TRACK ORDER', style: GoogleFonts.outfit(color: r.text1, fontSize: 13, fontWeight: FontWeight.w700, letterSpacing: 2)),
          ),
          body: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(24, 8, 24, 32),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Center(child: Mono(o.orderUid, size: 13)),
              const SizedBox(height: 32),
              ...List.generate(steps.length, (i) {
                final s = steps[i];
                final last = i == steps.length - 1;
                final done = s['done'] == true;
                final cur = s['current'] == true;
                final nc = done ? C.ok : cur ? C.rx : r.border;
                return IntrinsicHeight(
                  child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    SizedBox(
                      width: 32,
                      child: Column(children: [
                        Container(
                          width: 18,
                          height: 18,
                          decoration: BoxDecoration(color: nc, shape: BoxShape.circle),
                          child: done ? const Icon(Icons.check, color: Colors.white, size: 10) : null,
                        ),
                        if (!last) Expanded(child: Container(width: 2, color: done ? C.ok : r.border)),
                      ]),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Padding(
                        padding: EdgeInsets.only(bottom: last ? 0 : 28),
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text((s['label'] as String).toUpperCase(), style: GoogleFonts.outfit(color: cur ? C.rx : r.text1, fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 0.8)),
                          if (s['detail'] != null)
                            Padding(padding: const EdgeInsets.only(top: 3), child: Text(s['detail'] as String, style: TextStyle(color: r.text2, fontSize: 12))),
                          if (s['ts'] != null)
                            Padding(
                              padding: const EdgeInsets.only(top: 3),
                              child: Text(
                                '${(s['ts'] as DateTime).hour.toString().padLeft(2, '0')}:${(s['ts'] as DateTime).minute.toString().padLeft(2, '0')}  ·  ${(s['ts'] as DateTime).day}/${(s['ts'] as DateTime).month}/${(s['ts'] as DateTime).year}',
                                style: TextStyle(color: r.text3, fontSize: 10),
                              ),
                            ),
                        ]),
                      ),
                    ),
                  ]),
                );
              }),
              const SizedBox(height: 36),
              Text('ORDER DETAILS', style: GoogleFonts.outfit(color: r.text3, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 2)),
              const SizedBox(height: 12),
              RxCard(
                child: Column(children: [
                  ...o.items.map((it) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                          Expanded(
                            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                              Text(it.name, style: GoogleFonts.outfit(color: r.text1, fontSize: 14, fontWeight: FontWeight.w500)),
                              Text('QTY: ${it.quantity}', style: GoogleFonts.outfit(color: r.text3, fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 1)),
                            ]),
                          ),
                          Text(it.formattedPrice, style: GoogleFonts.outfit(color: r.text1, fontSize: 14)),
                        ]),
                      )),
                  Container(height: 1, color: r.border, margin: const EdgeInsets.symmetric(vertical: 8)),
                  Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                    Text('Total', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 20)),
                    Text(o.formattedTotal, style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 20)),
                  ]),
                ]),
              ),
              const SizedBox(height: 24),
              RxBtn(label: 'Need Help?', outlined: true, icon: Icons.chat_bubble_outline_rounded, onPressed: () {}),
            ]),
          ),
        );
      },
    );
  }
}
