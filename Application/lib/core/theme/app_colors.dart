import 'package:flutter/material.dart';

/// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/// RxCompute — Clinical Brutalist Color System
/// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class C {
  C._();

  // ─── Brand ───────────────────────────────────────────────
  static const Color rx = Color(0xFFD64C2F);
  static const Color compute = Color(0xFF7EA8BE);

  // ─── Dark Mode — Deep Steel ──────────────────────────────
  static const Color d0 = Color(0xFF0A0E13);
  static const Color d1 = Color(0xFF0F141A);
  static const Color d2 = Color(0xFF161C24);
  static const Color d3 = Color(0xFF1E2630);
  static const Color d4 = Color(0xFF2A3441);
  static const Color d5 = Color(0xFF374151);

  // ─── Light Mode — Icy Slate ──────────────────────────────
  static const Color l0 = Color(0xFFF0F4F8);
  static const Color l1 = Color(0xFFFFFFFF);
  static const Color l2 = Color(0xFFE8EDF2);
  static const Color l3 = Color(0xFFD1D9E0);
  static const Color l4 = Color(0xFFB0BEC5);

  // ─── Text Dark Mode ──────────────────────────────────────
  static const Color tw = Color(0xFFF1F5F9);
  static const Color t1 = Color(0xFF94A3B8);
  static const Color t2 = Color(0xFF64748B);

  // ─── Text Light Mode ─────────────────────────────────────
  static const Color tb = Color(0xFF0F172A);
  static const Color t3 = Color(0xFF475569);
  static const Color t4 = Color(0xFF94A3B8);

  // ─── Semantic ────────────────────────────────────────────
  static const Color ok = Color(0xFF10B981);
  static const Color warn = Color(0xFFF59E0B);
  static const Color err = Color(0xFFEF4444);
  static const Color info = Color(0xFF7EA8BE);

  // ─── Soft Semantic BGs ───────────────────────────────────
  static Color okBg(bool dark) => dark ? ok.withOpacity(0.10) : const Color(0xFFD1FAE5);
  static Color warnBg(bool dark) => dark ? warn.withOpacity(0.10) : const Color(0xFFFEF3C7);
  static Color errBg(bool dark) => dark ? err.withOpacity(0.10) : const Color(0xFFFEE2E2);
  static Color infoBg(bool dark) => dark ? info.withOpacity(0.10) : const Color(0xFFE0F2FE);
  static Color rxBg(bool dark) => dark ? rx.withOpacity(0.08) : const Color(0xFFFEECE8);
}
