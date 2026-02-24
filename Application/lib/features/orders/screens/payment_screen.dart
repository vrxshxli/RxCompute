import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/rx_theme_ext.dart';
import '../../../core/widgets/shared_widgets.dart';
import '../../../config/routes.dart';
import '../../../data/mock_data.dart';
import '../../../data/models/order_model.dart';

class PaymentScreen extends StatefulWidget {
  const PaymentScreen({super.key});
  @override
  State<PaymentScreen> createState() => _PayS();
}

class _PayS extends State<PaymentScreen> {
  String _method = '';
  bool _processing = false;
  bool _saveCard = true;

  final _cardNum = TextEditingController();
  final _cardExp = TextEditingController();
  final _cardCvv = TextEditingController();
  final _cardName = TextEditingController();
  final _upiId = TextEditingController();

  OrderModel get _order => MockData.orders.first;
  double get _subtotal => _order.total;
  double get _delivery => 2.50;
  double get _discount => 3.20;
  double get _total => _subtotal + _delivery - _discount;

  @override
  void dispose() {
    _cardNum.dispose();
    _cardExp.dispose();
    _cardCvv.dispose();
    _cardName.dispose();
    _upiId.dispose();
    super.dispose();
  }

  Future<void> _pay() async {
    if (_method.isEmpty) return;
    setState(() => _processing = true);
    await Future.delayed(const Duration(seconds: 2));
    if (!mounted) return;
    setState(() => _processing = false);
    _showSuccess();
  }

  void _showSuccess() {
    showModalBottomSheet(
      context: context,
      isDismissible: false,
      enableDrag: false,
      backgroundColor: context.rx.card,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) {
        final r = ctx.rx;
        return Padding(
          padding: const EdgeInsets.fromLTRB(28, 32, 28, 32),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Container(width: 72, height: 72, decoration: BoxDecoration(color: C.okBg(r.dark), borderRadius: BorderRadius.circular(22)), child: const Icon(Icons.check_rounded, color: C.ok, size: 36)),
            const SizedBox(height: 20),
            Text('Payment', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 28)),
            Text('Successful', style: GoogleFonts.dmSerifDisplay(color: C.ok, fontSize: 28)),
            const SizedBox(height: 16),
            Text('₹${_total.toStringAsFixed(2)}', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 36)),
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: C.okBg(r.dark), borderRadius: BorderRadius.circular(12), border: const Border(left: BorderSide(color: C.ok, width: 3))),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('ORDER CONFIRMED', style: GoogleFonts.outfit(color: C.ok, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1.5)),
                const SizedBox(height: 6),
                Row(children: [
                  Text('ID  ', style: GoogleFonts.outfit(color: r.text3, fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 1)),
                  Mono(_order.orderUid, size: 12, color: r.text1),
                ]),
                const SizedBox(height: 4),
                Text('${_order.items.length} items · Pharmacy ${_order.pharmacy ?? "PH-001"}', style: GoogleFonts.outfit(color: r.text2, fontSize: 12)),
              ]),
            ),
            const SizedBox(height: 24),
            RxBtn(
              label: 'Track Order',
              icon: Icons.local_shipping_rounded,
              color: C.compute,
              onPressed: () {
                Navigator.pop(ctx);
                Navigator.pushNamedAndRemoveUntil(context, AppRoutes.home, (_) => false);
                Navigator.pushNamed(context, AppRoutes.orderTracking);
              },
            ),
            const SizedBox(height: 10),
            RxBtn(
              label: 'Back to Home',
              outlined: true,
              onPressed: () {
                Navigator.pop(ctx);
                Navigator.pushNamedAndRemoveUntil(context, AppRoutes.home, (_) => false);
              },
            ),
          ]),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return Scaffold(
      backgroundColor: r.bg,
      appBar: AppBar(
        backgroundColor: r.bg,
        leading: IconButton(icon: Icon(Icons.arrow_back_rounded, color: r.text1), onPressed: () => Navigator.pop(context)),
        title: Text('PAYMENT', style: GoogleFonts.outfit(color: r.text1, fontSize: 13, fontWeight: FontWeight.w700, letterSpacing: 2)),
      ),
      body: Column(children: [
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const SecLabel('ORDER SUMMARY'),
              RxCard(
                padding: const EdgeInsets.all(18),
                child: Column(children: [
                  ...(_order.items).map((it) => Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                          Expanded(child: Text(it.name, style: GoogleFonts.outfit(color: r.text1, fontSize: 14), overflow: TextOverflow.ellipsis)),
                          Text('×${it.quantity}', style: GoogleFonts.outfit(color: r.text3, fontSize: 13)),
                          const SizedBox(width: 16),
                          Text(it.formattedPrice, style: GoogleFonts.outfit(color: r.text1, fontSize: 14)),
                        ]),
                      )),
                  Container(height: 1, color: r.border, margin: const EdgeInsets.symmetric(vertical: 10)),
                  _priceRow('Subtotal', '₹${_subtotal.toStringAsFixed(2)}', r),
                  const SizedBox(height: 4),
                  _priceRow('Delivery', '₹${_delivery.toStringAsFixed(2)}', r),
                  const SizedBox(height: 4),
                  _priceRow('Discount', '-₹${_discount.toStringAsFixed(2)}', r, color: C.ok),
                  Container(height: 1, color: r.border, margin: const EdgeInsets.symmetric(vertical: 10)),
                  Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                    Text('Total', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 22)),
                    Text('₹${_total.toStringAsFixed(2)}', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 22)),
                  ]),
                ]),
              ),
              const SizedBox(height: 28),
              const SecLabel('UPI'),
              _PayOption(key_: 'gpay', icon: Icons.account_balance_wallet_rounded, label: 'Google Pay', subtitle: 'Instant transfer', selected: _method == 'gpay', onTap: () => setState(() => _method = 'gpay')),
              const SizedBox(height: 8),
              _PayOption(key_: 'phonepe', icon: Icons.phone_android_rounded, label: 'PhonePe', subtitle: 'UPI payment', selected: _method == 'phonepe', onTap: () => setState(() => _method = 'phonepe')),
              const SizedBox(height: 8),
              _PayOption(key_: 'upi_id', icon: Icons.alternate_email_rounded, label: 'UPI ID', subtitle: 'Enter your UPI address', selected: _method == 'upi_id', onTap: () => setState(() => _method = 'upi_id')),
              if (_method == 'upi_id') ...[
                const SizedBox(height: 12),
                RxCard(
                  padding: const EdgeInsets.all(16),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    RxInput(label: 'UPI ID', hint: 'yourname@upi', ctrl: _upiId),
                    const SizedBox(height: 6),
                    Text('e.g. deepak@oksbi, deepak@ybl', style: GoogleFonts.outfit(color: r.text3, fontSize: 11)),
                  ]),
                ),
              ],
              const SizedBox(height: 24),
              const SecLabel('CARDS'),
              _PayOption(key_: 'card', icon: Icons.credit_card_rounded, label: 'Credit / Debit Card', subtitle: 'Visa, Mastercard, Rupay', selected: _method == 'card', onTap: () => setState(() => _method = 'card')),
              if (_method == 'card') ...[
                const SizedBox(height: 12),
                RxCard(
                  padding: const EdgeInsets.all(18),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    RxInput(label: 'Card Number', hint: '4242 4242 4242 4242', ctrl: _cardNum, keyboard: TextInputType.number),
                    const SizedBox(height: 16),
                    Row(children: [
                      Expanded(child: RxInput(label: 'Expiry', hint: 'MM/YY', ctrl: _cardExp, keyboard: TextInputType.datetime)),
                      const SizedBox(width: 16),
                      Expanded(child: RxInput(label: 'CVV', hint: '•••', ctrl: _cardCvv, keyboard: TextInputType.number)),
                    ]),
                    const SizedBox(height: 16),
                    RxInput(label: 'Cardholder Name', hint: 'Name on card', ctrl: _cardName),
                    const SizedBox(height: 14),
                    GestureDetector(
                      onTap: () => setState(() => _saveCard = !_saveCard),
                      child: Row(children: [
                        Container(
                          width: 20,
                          height: 20,
                          decoration: BoxDecoration(color: _saveCard ? C.compute : Colors.transparent, borderRadius: BorderRadius.circular(5), border: _saveCard ? null : Border.all(color: r.border)),
                          child: _saveCard ? const Icon(Icons.check, color: Colors.white, size: 14) : null,
                        ),
                        const SizedBox(width: 10),
                        Text('SAVE CARD FOR FUTURE', style: GoogleFonts.outfit(color: r.text2, fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 1)),
                      ]),
                    ),
                  ]),
                ),
              ],
              const SizedBox(height: 24),
              const SecLabel('WALLETS'),
              _PayOption(key_: 'paytm', icon: Icons.account_balance_wallet_outlined, label: 'Paytm Wallet', subtitle: 'Balance: ₹2,340', selected: _method == 'paytm', onTap: () => setState(() => _method = 'paytm')),
              const SizedBox(height: 8),
              _PayOption(key_: 'amazon', icon: Icons.shopping_bag_outlined, label: 'Amazon Pay', subtitle: 'Pay with Amazon balance', selected: _method == 'amazon', onTap: () => setState(() => _method = 'amazon')),
              const SizedBox(height: 24),
              const SecLabel('NET BANKING'),
              _PayOption(key_: 'sbi', icon: Icons.account_balance_rounded, label: 'State Bank of India', subtitle: 'Redirect to SBI', selected: _method == 'sbi', onTap: () => setState(() => _method = 'sbi')),
              const SizedBox(height: 8),
              _PayOption(key_: 'hdfc', icon: Icons.account_balance_rounded, label: 'HDFC Bank', subtitle: 'Redirect to HDFC', selected: _method == 'hdfc', onTap: () => setState(() => _method = 'hdfc')),
              const SizedBox(height: 24),
              const SecLabel('OTHER'),
              _PayOption(key_: 'cod', icon: Icons.local_atm_rounded, label: 'Cash on Delivery', subtitle: '₹1.00 COD fee applies', selected: _method == 'cod', onTap: () => setState(() => _method = 'cod')),
              const SizedBox(height: 24),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(color: C.infoBg(r.dark), borderRadius: BorderRadius.circular(10)),
                child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Icon(Icons.lock_rounded, color: C.compute, size: 16),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'YOUR PAYMENT IS SECURED WITH 256-BIT ENCRYPTION. WE NEVER STORE YOUR FULL CARD DETAILS.',
                      style: GoogleFonts.outfit(color: r.dark ? C.compute : C.t3, fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 0.8, height: 1.5),
                    ),
                  ),
                ]),
              ),
              const SizedBox(height: 100),
            ]),
          ),
        ),
        Container(
          padding: const EdgeInsets.fromLTRB(24, 14, 24, 14),
          decoration: BoxDecoration(color: r.card, border: Border(top: BorderSide(color: r.border, width: 0.5))),
          child: SafeArea(
            top: false,
            child: Row(children: [
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('TOTAL', style: GoogleFonts.outfit(color: r.text3, fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 1.5)),
                  const SizedBox(height: 2),
                  Text('₹${_total.toStringAsFixed(2)}', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 24)),
                ]),
              ),
              SizedBox(
                width: 180,
                child: RxBtn(label: _processing ? 'Processing...' : 'Pay Now', icon: _processing ? null : Icons.lock_rounded, loading: _processing, onPressed: _method.isNotEmpty ? _pay : null),
              ),
            ]),
          ),
        ),
      ]),
    );
  }

  Widget _priceRow(String label, String value, Rx r, {Color? color}) {
    return Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
      Text(label.toUpperCase(), style: GoogleFonts.outfit(color: r.text3, fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 0.8)),
      Text(value, style: GoogleFonts.outfit(color: color ?? r.text2, fontSize: 13, fontWeight: FontWeight.w500)),
    ]);
  }
}

class _PayOption extends StatelessWidget {
  final String key_;
  final IconData icon;
  final String label;
  final String subtitle;
  final bool selected;
  final VoidCallback onTap;

  const _PayOption({required this.key_, required this.icon, required this.label, required this.subtitle, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: selected ? (r.dark ? C.compute.withOpacity(0.08) : C.compute.withOpacity(0.04)) : r.card,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: selected ? C.compute : r.border.withOpacity(r.dark ? 0.4 : 0.6), width: selected ? 1.5 : 1),
        ),
        child: Row(children: [
          Container(width: 40, height: 40, decoration: BoxDecoration(color: selected ? C.compute.withOpacity(r.dark ? 0.15 : 0.08) : r.surface, borderRadius: BorderRadius.circular(10)), child: Icon(icon, color: selected ? C.compute : r.text2, size: 20)),
          const SizedBox(width: 14),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(label, style: GoogleFonts.outfit(color: r.text1, fontSize: 14, fontWeight: FontWeight.w600)),
              const SizedBox(height: 2),
              Text(subtitle.toUpperCase(), style: GoogleFonts.outfit(color: r.text3, fontSize: 10, fontWeight: FontWeight.w500, letterSpacing: 0.5)),
            ]),
          ),
          Container(
            width: 22,
            height: 22,
            decoration: BoxDecoration(shape: BoxShape.circle, border: Border.all(color: selected ? C.compute : r.border, width: selected ? 2 : 1.5)),
            child: selected ? Center(child: Container(width: 10, height: 10, decoration: const BoxDecoration(color: C.compute, shape: BoxShape.circle))) : null,
          ),
        ]),
      ),
    );
  }
}
