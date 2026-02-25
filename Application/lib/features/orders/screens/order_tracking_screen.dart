import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/rx_theme_ext.dart';
import '../../../core/widgets/shared_widgets.dart';
import '../../../data/models/order_model.dart';
import '../bloc/order_bloc.dart';

class OrderTrackingScreen extends StatefulWidget {
  const OrderTrackingScreen({super.key});

  @override
  State<OrderTrackingScreen> createState() => _OrderTrackingScreenState();
}

class _OrderTrackingScreenState extends State<OrderTrackingScreen> {
  int? _selectedOrderId;
  bool _argsRead = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_argsRead) return;
    _argsRead = true;
    final args = ModalRoute.of(context)?.settings.arguments;
    if (args is OrderModel) {
      _selectedOrderId = args.id;
    } else if (args is int) {
      _selectedOrderId = args;
    }
  }

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return BlocBuilder<OrderBloc, OrderState>(
      builder: (context, state) {
        final orders = state.orders;
        if (orders.isEmpty) {
          return Scaffold(
            backgroundColor: r.bg,
            appBar: AppBar(
              backgroundColor: r.bg,
              leading: IconButton(icon: Icon(Icons.arrow_back_rounded, color: r.text1), onPressed: () => Navigator.pop(context)),
              title: Text('TRACK ORDER', style: GoogleFonts.outfit(color: r.text1, fontSize: 13, fontWeight: FontWeight.w700, letterSpacing: 2)),
            ),
            body: const EmptyState(icon: Icons.local_shipping_outlined, title: 'No active order'),
          );
        }
        OrderModel? selected;
        if (_selectedOrderId != null) {
          for (final order in orders) {
            if (order.id == _selectedOrderId) {
              selected = order;
              break;
            }
          }
        }
        if (selected == null) {
          return _buildOrderList(context, r, orders);
        }
        final o = selected;
        final steps = _stepsForStatus(o.status.name);
        return Scaffold(
          backgroundColor: r.bg,
          appBar: AppBar(
            backgroundColor: r.bg,
            leading: IconButton(
              icon: Icon(Icons.arrow_back_rounded, color: r.text1),
              onPressed: () => setState(() => _selectedOrderId = null),
            ),
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

  Widget _buildOrderList(BuildContext context, Rx r, List<OrderModel> orders) {
    return Scaffold(
      backgroundColor: r.bg,
      appBar: AppBar(
        backgroundColor: r.bg,
        leading: IconButton(icon: Icon(Icons.arrow_back_rounded, color: r.text1), onPressed: () => Navigator.pop(context)),
        title: Text('TRACK ORDER', style: GoogleFonts.outfit(color: r.text1, fontSize: 13, fontWeight: FontWeight.w700, letterSpacing: 2)),
      ),
      body: ListView.builder(
        padding: const EdgeInsets.fromLTRB(24, 10, 24, 24),
        itemCount: orders.length,
        itemBuilder: (_, i) {
          final o = orders[i];
          final statusColor = o.status == OrderStatus.delivered ? C.ok : o.status == OrderStatus.cancelled ? C.err : C.warn;
          return GestureDetector(
            onTap: () => setState(() => _selectedOrderId = o.id),
            child: Container(
              margin: const EdgeInsets.only(bottom: 10),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: r.card, borderRadius: BorderRadius.circular(12), border: Border.all(color: r.border.withOpacity(0.4))),
              child: Row(
                children: [
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Mono(o.orderUid, color: r.text1),
                      const SizedBox(height: 4),
                      Text('${o.items.length} items · ${o.formattedTotal}', style: GoogleFonts.outfit(color: r.text2, fontSize: 13)),
                    ]),
                  ),
                  RxBadge(text: o.status.label, color: statusColor),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  List<Map<String, dynamic>> _stepsForStatus(String status) {
    const labels = ['Order Confirmed', 'Pharmacy Verified', 'Picking', 'Packed', 'Dispatched', 'Delivered'];
    final statusMap = {
      'pending': 0,
      'confirmed': 0,
      'verified': 1,
      'picking': 2,
      'packed': 3,
      'dispatched': 4,
      'delivered': 5,
    };
    final current = statusMap[status] ?? 0;
    return List.generate(labels.length, (i) {
      return {
        'label': labels[i],
        'done': i <= current,
        'current': i == current,
      };
    });
  }
}
