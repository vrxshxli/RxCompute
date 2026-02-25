import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/rx_theme_ext.dart';
import '../../../core/widgets/shared_widgets.dart';
import '../../../config/routes.dart';
import '../../../data/models/order_model.dart';
import '../bloc/order_bloc.dart';

class OrderHistoryScreen extends StatelessWidget {
  const OrderHistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return BlocBuilder<OrderBloc, OrderState>(
      builder: (context, state) {
        return Scaffold(
          backgroundColor: r.bg,
          appBar: AppBar(
            backgroundColor: r.bg,
            leading: IconButton(icon: Icon(Icons.arrow_back_rounded, color: r.text1), onPressed: () => Navigator.pop(context)),
            title: Text('ORDER HISTORY', style: GoogleFonts.outfit(color: r.text1, fontSize: 13, fontWeight: FontWeight.w700, letterSpacing: 2)),
          ),
          body: state.orders.isEmpty
              ? const EmptyState(icon: Icons.shopping_bag_outlined, title: 'No orders yet')
              : ListView.builder(
                  padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
                  itemCount: state.orders.length,
                  itemBuilder: (_, i) {
                    final o = state.orders[i];
                    final sc = o.status == OrderStatus.delivered
                        ? C.ok
                        : o.status == OrderStatus.cancelled
                            ? C.err
                            : C.warn;
                    return GestureDetector(
                      onTap: () => Navigator.pushNamed(context, AppRoutes.orderTracking, arguments: o),
                      child: Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        padding: const EdgeInsets.all(18),
                        decoration: BoxDecoration(color: r.card, borderRadius: BorderRadius.circular(14), border: Border.all(color: r.border.withOpacity(0.4))),
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Row(children: [Mono(o.orderUid), const Spacer(), RxBadge(text: o.status.label, color: sc)]),
                          const SizedBox(height: 12),
                          Text(o.items.map((i) => i.name).join(', '), maxLines: 2, overflow: TextOverflow.ellipsis, style: GoogleFonts.outfit(color: r.text1, fontSize: 14)),
                          const SizedBox(height: 10),
                          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                            Text(o.formattedDate, style: GoogleFonts.outfit(color: r.text3, fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 0.5)),
                            Text(o.formattedTotal, style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 18)),
                          ]),
                        ]),
                      ),
                    );
                  },
                ),
        );
      },
    );
  }
}
