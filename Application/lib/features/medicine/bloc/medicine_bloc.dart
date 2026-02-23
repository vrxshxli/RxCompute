import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../../data/models/medicine_model.dart';
import '../../../data/models/chat_models.dart';
import '../../../data/repositories/medicine_repository.dart';
import '../../../data/repositories/user_medication_repository.dart';

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
  final MedicineRepository _medicineRepo = MedicineRepository();
  final UserMedicationRepository _userMedicationRepo = UserMedicationRepository();

  MedicineBloc() : super(const MedicineState()) {
    on<LoadMedicinesEvent>(_onLoad);
    on<SearchMedicinesEvent>(_onSearch);
  }

  Future<void> _onLoad(LoadMedicinesEvent event, Emitter<MedicineState> emit) async {
    emit(state.copyWith(isLoading: true));
    try {
      final meds = await _medicineRepo.getMedicines();
      final userMeds = await _userMedicationRepo.getUserMedications();
      final active = userMeds
          .map((m) => ActiveMed(
                name: m.name,
                dosage: '${m.dosageInstruction} · ${m.frequencyPerDay}x/day',
                remaining: m.quantityUnits,
                total: (m.daysLeft * m.frequencyPerDay).clamp(1, 2000),
              ))
          .toList();
      final low = active.where((m) => m.remaining <= 5).toList();
      emit(state.copyWith(
        medicines: meds,
        activeMeds: active,
        lowMeds: low,
        history: const [],
        isLoading: false,
        error: null,
      ));
    } catch (e) {
      emit(state.copyWith(isLoading: false, error: e.toString()));
    }
  }

  Future<void> _onSearch(SearchMedicinesEvent event, Emitter<MedicineState> emit) async {
    try {
      final meds = await _medicineRepo.getMedicines(search: event.query);
      emit(state.copyWith(medicines: meds, error: null));
    } catch (e) {
      emit(state.copyWith(error: e.toString()));
    }
  }
}
