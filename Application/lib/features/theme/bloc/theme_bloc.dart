import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';

// ─── Events ──────────────────────────────────────────────
abstract class ThemeEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class ToggleThemeEvent extends ThemeEvent {}

// ─── State ───────────────────────────────────────────────
class ThemeState extends Equatable {
  final ThemeMode mode;

  const ThemeState({this.mode = ThemeMode.dark});

  bool get isDark => mode == ThemeMode.dark;

  ThemeState copyWith({ThemeMode? mode}) =>
      ThemeState(mode: mode ?? this.mode);

  @override
  List<Object?> get props => [mode];
}

// ─── Bloc ────────────────────────────────────────────────
class ThemeBloc extends Bloc<ThemeEvent, ThemeState> {
  ThemeBloc() : super(const ThemeState()) {
    on<ToggleThemeEvent>((event, emit) {
      emit(state.copyWith(
        mode: state.isDark ? ThemeMode.light : ThemeMode.dark,
      ));
    });
  }
}
