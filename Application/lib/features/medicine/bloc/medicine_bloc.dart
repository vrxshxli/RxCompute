import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../../data/models/medicine_model.dart';
import '../../../data/models/chat_models.dart';
import '../../../data/mock_data.dart';

// ─── Events ──────────────────────────────────────────────
abstract class MedicineEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class LoadMedicinesEvent extends MedicineEvent {}

class SearchMedicinesEvent extends MedicineEvent {
  final String query;
  SearchMedicinesEvent(this.query);

  @override
  List<Object?> get props => [query];
}

// ─── State ───────────────────────────────────────────────
class MedicineState extends Equatable {
  final List<MedicineModel> medicines;
  final List<ActiveMed> activeMeds;
  final List<ActiveMed> lowMeds;
  final List<Map<String, String>> history;
  final bool isLoading;
  final String? error;

  const MedicineState({
    this.medicines = const [],
    this.activeMeds = const [],
    this.lowMeds = const [],
    this.history = const [],
    this.isLoading = false,
    this.error,
  });

  MedicineState copyWith({
    List<MedicineModel>? medicines,
    List<ActiveMed>? activeMeds,
    List<ActiveMed>? lowMeds,
    List<Map<String, String>>? history,
    bool? isLoading,
    String? error,
  }) =>
      MedicineState(
        medicines: medicines ?? this.medicines,
        activeMeds: activeMeds ?? this.activeMeds,
        lowMeds: lowMeds ?? this.lowMeds,
        history: history ?? this.history,
        isLoading: isLoading ?? this.isLoading,
        error: error,
      );

  @override
  List<Object?> get props => [medicines, activeMeds, lowMeds, history, isLoading, error];
}

// ─── Bloc ────────────────────────────────────────────────
class MedicineBloc extends Bloc<MedicineEvent, MedicineState> {
  MedicineBloc() : super(const MedicineState()) {
    on<LoadMedicinesEvent>(_onLoad);
    on<SearchMedicinesEvent>(_onSearch);
  }

  Future<void> _onLoad(LoadMedicinesEvent event, Emitter<MedicineState> emit) async {
    emit(state.copyWith(isLoading: true));
    try {
      // TODO: Replace with repository calls
      emit(state.copyWith(
        medicines: MockData.medicines,
        activeMeds: MockData.activeMeds,
        lowMeds: MockData.lowMeds,
        history: MockData.hist.map((e) => e.map((k, v) => MapEntry(k, v.toString()))).toList(),
        isLoading: false,
      ));
    } catch (e) {
      emit(state.copyWith(isLoading: false, error: e.toString()));
    }
  }

  Future<void> _onSearch(SearchMedicinesEvent event, Emitter<MedicineState> emit) async {
    // TODO: Call repository search
    final q = event.query.toLowerCase();
    final filtered = MockData.medicines.where((m) => m.name.toLowerCase().contains(q)).toList();
    emit(state.copyWith(medicines: filtered));
  }
}
