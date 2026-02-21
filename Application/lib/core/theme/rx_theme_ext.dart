import 'package:flutter/material.dart';
import 'app_colors.dart';

class Rx {
  final bool dark;
  const Rx._(this.dark);
  factory Rx.of(BuildContext c) => Rx._(Theme.of(c).brightness == Brightness.dark);

  Color get bg => dark ? C.d1 : C.l0;
  Color get card => dark ? C.d2 : C.l1;
  Color get surface => dark ? C.d3 : C.l2;
  Color get border => dark ? C.d4 : C.l3;
  Color get borderStrong => dark ? C.d5 : C.l4;
  Color get text1 => dark ? C.tw : C.tb;
  Color get text2 => dark ? C.t1 : C.t3;
  Color get text3 => dark ? C.t2 : C.t4;
  Color get inputBg => dark ? C.d3 : C.l1;
  Color get inputBorder => dark ? C.d4 : C.l3;
  Color get okBg => C.okBg(dark);
  Color get warnBg => C.warnBg(dark);
  Color get errBg => C.errBg(dark);
  Color get infoBg => C.infoBg(dark);
  Color get rxBg => C.rxBg(dark);
}

extension RxCtx on BuildContext { Rx get rx => Rx.of(this); }
