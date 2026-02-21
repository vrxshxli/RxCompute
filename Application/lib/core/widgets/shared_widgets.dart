import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../theme/app_colors.dart';
import '../theme/rx_theme_ext.dart';

// ═══ LOGO — editorial split ═══
class RxLogo extends StatelessWidget {
  final double size;
  const RxLogo({super.key, this.size = 28});
  @override Widget build(BuildContext context) => Row(mainAxisSize: MainAxisSize.min, children: [
    Text('Rx', style: GoogleFonts.dmSerifDisplay(fontSize: size, color: C.rx, fontWeight: FontWeight.w400)),
    Text('Compute', style: GoogleFonts.outfit(fontSize: size * 0.72, color: C.compute, fontWeight: FontWeight.w600, letterSpacing: -0.5)),
  ]);
}

// ═══ CARD — frosted steel ═══
class RxCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final VoidCallback? onTap;
  final Color? accent;
  const RxCard({super.key, required this.child, this.padding = const EdgeInsets.all(20), this.onTap, this.accent});

  @override Widget build(BuildContext context) {
    final r = context.rx;
    return GestureDetector(onTap: onTap, child: Container(
      padding: padding,
      decoration: BoxDecoration(
        color: r.card,
        borderRadius: BorderRadius.circular(14),
        border: accent != null
          ? Border(left: BorderSide(color: accent!, width: 3))
          : Border.all(color: r.border.withOpacity(r.dark ? 0.4 : 0.6)),
      ),
      child: child));
  }
}

// ═══ BUTTON — bold, squared ═══
class RxBtn extends StatefulWidget {
  final String label; final VoidCallback? onPressed; final bool loading, outlined;
  final Color? color; final IconData? icon;
  const RxBtn({super.key, required this.label, this.onPressed, this.loading = false, this.outlined = false, this.color, this.icon});
  @override State<RxBtn> createState() => _RxBtnS();
}
class _RxBtnS extends State<RxBtn> {
  bool _p = false;
  @override Widget build(BuildContext context) {
    final r = context.rx;
    final bg = widget.color ?? C.rx;
    final off = widget.onPressed == null || widget.loading;
    if (widget.outlined) {
      return GestureDetector(
        onTapDown: (_) => setState(() => _p = true),
        onTapUp: (_) { setState(() => _p = false); if (!off) widget.onPressed?.call(); },
        onTapCancel: () => setState(() => _p = false),
        child: AnimatedContainer(duration: const Duration(milliseconds: 60), height: 52,
          decoration: BoxDecoration(color: _p ? r.surface : Colors.transparent, borderRadius: BorderRadius.circular(10), border: Border.all(color: r.border)),
          alignment: Alignment.center,
          child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            if (widget.icon != null) ...[Icon(widget.icon, color: r.text1, size: 17), const SizedBox(width: 8)],
            Text(widget.label.toUpperCase(), style: GoogleFonts.outfit(color: r.text1, fontSize: 13, fontWeight: FontWeight.w700, letterSpacing: 1.2)),
          ])));
    }
    return GestureDetector(
      onTapDown: (_) => setState(() => _p = true),
      onTapUp: (_) { setState(() => _p = false); if (!off) widget.onPressed?.call(); },
      onTapCancel: () => setState(() => _p = false),
      child: AnimatedContainer(duration: const Duration(milliseconds: 60), height: 52,
        decoration: BoxDecoration(color: off ? bg.withOpacity(0.35) : (_p ? bg.withOpacity(0.85) : bg), borderRadius: BorderRadius.circular(10)),
        alignment: Alignment.center,
        child: widget.loading
          ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white))
          : Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              if (widget.icon != null) ...[Icon(widget.icon, color: Colors.white, size: 17), const SizedBox(width: 8)],
              Text(widget.label.toUpperCase(), style: GoogleFonts.outfit(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w700, letterSpacing: 1.2)),
            ])));
  }
}

// ═══ BADGE — frosted status ═══
class RxBadge extends StatelessWidget {
  final String text; final Color color; final IconData? icon;
  const RxBadge({super.key, required this.text, required this.color, this.icon});
  @override Widget build(BuildContext context) {
    final bg = context.rx.dark ? color.withOpacity(0.12) : color.withOpacity(0.08);
    return Container(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(6)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        if (icon != null) ...[Icon(icon, size: 11, color: color), const SizedBox(width: 4)],
        Text(text.toUpperCase(), style: GoogleFonts.outfit(color: color, fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 0.8)),
      ]));
  }
}

// ═══ ICON BLOCK ═══
class IcoBlock extends StatelessWidget {
  final IconData icon; final Color color; final double size;
  const IcoBlock({super.key, required this.icon, required this.color, this.size = 44});
  @override Widget build(BuildContext context) {
    final bg = context.rx.dark ? color.withOpacity(0.10) : color.withOpacity(0.06);
    return Container(width: size, height: size,
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(12)),
      child: Icon(icon, color: color, size: size * 0.45));
  }
}

// ═══ SUPPLY BAR ═══
class SupplyBar extends StatelessWidget {
  final double pct;
  const SupplyBar({super.key, required this.pct});
  Color get _c => pct > 0.5 ? C.ok : pct > 0.2 ? C.warn : C.err;
  @override Widget build(BuildContext context) => Container(height: 5,
    decoration: BoxDecoration(color: context.rx.surface, borderRadius: BorderRadius.circular(3)),
    child: FractionallySizedBox(alignment: Alignment.centerLeft, widthFactor: pct.clamp(0, 1),
      child: Container(decoration: BoxDecoration(color: _c, borderRadius: BorderRadius.circular(3)))));
}

// ═══ MONO TEXT ═══
class Mono extends StatelessWidget {
  final String text; final double size; final Color? color;
  const Mono(this.text, {super.key, this.size = 11, this.color});
  @override Widget build(BuildContext context) => Text(text, style: GoogleFonts.jetBrainsMono(fontSize: size, color: color ?? context.rx.text3));
}

// ═══ SECTION LABEL ═══
class SecLabel extends StatelessWidget {
  final String text;
  const SecLabel(this.text, {super.key});
  @override Widget build(BuildContext context) => Padding(padding: const EdgeInsets.only(bottom: 14),
    child: Text(text.toUpperCase(), style: GoogleFonts.outfit(color: context.rx.text3, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 2.0)));
}

// ═══ INPUT ═══
class RxInput extends StatelessWidget {
  final String label; final String? hint, helper;
  final TextEditingController? ctrl; final TextInputType? keyboard;
  final bool readOnly; final Widget? suffix; final ValueChanged<String>? onChange;
  const RxInput({super.key, required this.label, this.hint, this.helper, this.ctrl, this.keyboard, this.readOnly = false, this.suffix, this.onChange});
  @override Widget build(BuildContext context) {
    final r = context.rx;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(label.toUpperCase(), style: GoogleFonts.outfit(color: r.text3, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1.5)),
      const SizedBox(height: 8),
      TextField(controller: ctrl, keyboardType: keyboard, readOnly: readOnly, onChanged: onChange,
        style: GoogleFonts.outfit(color: r.text1, fontSize: 15),
        decoration: InputDecoration(hintText: hint, suffixIcon: suffix)),
      if (helper != null) Padding(padding: const EdgeInsets.only(top: 6), child: Text(helper!, style: TextStyle(color: r.text3, fontSize: 11))),
    ]);
  }
}

// ═══ TYPING INDICATOR ═══
class TypingDots extends StatefulWidget {
  const TypingDots({super.key});
  @override State<TypingDots> createState() => _TD();
}
class _TD extends State<TypingDots> with TickerProviderStateMixin {
  late List<AnimationController> _c;
  late List<Animation<double>> _a;
  @override void initState() { super.initState();
    _c = List.generate(3, (i) => AnimationController(vsync: this, duration: const Duration(milliseconds: 500)));
    _a = _c.map((c) => Tween(begin: 0.0, end: -5.0).animate(CurvedAnimation(parent: c, curve: Curves.easeInOut))).toList();
    for (int i = 0; i < 3; i++) Future.delayed(Duration(milliseconds: i * 150), () { if (mounted) _c[i].repeat(reverse: true); });
  }
  @override void dispose() { for (final c in _c) c.dispose(); super.dispose(); }
  @override Widget build(BuildContext context) => Row(mainAxisSize: MainAxisSize.min, children: List.generate(3, (i) =>
    AnimatedBuilder(animation: _a[i], builder: (_, __) => Container(margin: const EdgeInsets.symmetric(horizontal: 2.5),
      child: Transform.translate(offset: Offset(0, _a[i].value), child: Container(width: 6, height: 6, decoration: BoxDecoration(color: context.rx.text3, shape: BoxShape.circle)))))));
}

// ═══ EMPTY STATE ═══
class EmptyState extends StatelessWidget {
  final IconData icon; final String title; final String? sub; final String? btn; final VoidCallback? fn;
  const EmptyState({super.key, required this.icon, required this.title, this.sub, this.btn, this.fn});
  @override Widget build(BuildContext context) {
    final r = context.rx;
    return Center(child: Padding(padding: const EdgeInsets.all(48), child: Column(mainAxisSize: MainAxisSize.min, children: [
      Container(width: 72, height: 72, decoration: BoxDecoration(color: r.surface, borderRadius: BorderRadius.circular(18)),
        child: Icon(icon, size: 30, color: r.text3)),
      const SizedBox(height: 20),
      Text(title, style: Theme.of(context).textTheme.titleMedium),
      if (sub != null) ...[const SizedBox(height: 8), Text(sub!, textAlign: TextAlign.center, style: TextStyle(color: r.text2, fontSize: 14))],
      if (btn != null && fn != null) ...[const SizedBox(height: 24), SizedBox(width: 200, child: RxBtn(label: btn!, onPressed: fn))],
    ])));
  }
}
