import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../../data/models/chat_models.dart';
import '../../../data/models/order_model.dart';
import '../../../data/models/notification_model.dart';
import '../../../data/models/user_model.dart';
import '../../../data/repositories/home_repository.dart';
import '../../../data/repositories/medicine_repository.dart';
import '../../../data/repositories/notification_repository.dart';
import '../../../data/repositories/order_repository.dart';
import '../../../data/repositories/user_medication_repository.dart';
import '../../../data/repositories/user_repository.dart';

// ─── Events ──────────────────────────────────────────────
abstract class HomeEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class LoadHomeDataEvent extends HomeEvent {}

class AddMedicationEvent extends HomeEvent {
  final String medicineName;
  final String dosageInstruction;
  final int frequencyPerDay;
  final int quantityUnits;

  AddMedicationEvent({
    required this.medicineName,
    required this.dosageInstruction,
    required this.frequencyPerDay,
    required this.quantityUnits,
  });

  @override
  List<Object?> get props => [medicineName, dosageInstruction, frequencyPerDay, quantityUnits];
}

class ReorderRefillEvent extends HomeEvent {
  final String medicineName;
  final int? medicineId;
  ReorderRefillEvent(this.medicineName, {this.medicineId});

  @override
  List<Object?> get props => [medicineName, medicineId];
}

// ─── State ───────────────────────────────────────────────
class HomeState extends Equatable {
  final UserModel? user;
  final List<ActiveMed> activeMeds;
  final List<Refill> alerts;
  final List<OrderModel> orders;
  final List<NotificationModel> notifications;
  final String monthlyInsight;
  final bool isLoading;
  final String? error;

  const HomeState({
    this.user,
    this.activeMeds = const [],
    this.alerts = const [],
    this.orders = const [],
    this.notifications = const [],
    this.monthlyInsight = 'No monthly insights yet',
    this.isLoading = false,
    this.error,
  });

  HomeState copyWith({
    UserModel? user,
    List<ActiveMed>? activeMeds,
    List<Refill>? alerts,
    List<OrderModel>? orders,
    List<NotificationModel>? notifications,
    String? monthlyInsight,
    bool? isLoading,
    String? error,
  }) =>
      HomeState(
        user: user ?? this.user,
        activeMeds: activeMeds ?? this.activeMeds,
        alerts: alerts ?? this.alerts,
        orders: orders ?? this.orders,
        notifications: notifications ?? this.notifications,
        monthlyInsight: monthlyInsight ?? this.monthlyInsight,
        isLoading: isLoading ?? this.isLoading,
        error: error ?? this.error,
      );

  @override
  List<Object?> get props => [user, activeMeds, alerts, orders, notifications, monthlyInsight, isLoading, error];
}

// ─── Bloc ────────────────────────────────────────────────
class HomeBloc extends Bloc<HomeEvent, HomeState> {
  final UserRepository _userRepo = UserRepository();
  final UserMedicationRepository _medRepo = UserMedicationRepository();
  final OrderRepository _orderRepo = OrderRepository();
  final MedicineRepository _medicineRepo = MedicineRepository();
  final NotificationRepository _notificationRepo = NotificationRepository();
  final HomeRepository _homeRepo = HomeRepository();

  HomeBloc() : super(const HomeState()) {
    on<LoadHomeDataEvent>(_onLoad);
    on<AddMedicationEvent>(_onAddMedication);
    on<ReorderRefillEvent>(_onReorderRefill);
  }

  Future<void> _onLoad(LoadHomeDataEvent event, Emitter<HomeState> emit) async {
    emit(state.copyWith(isLoading: true));
    try {
      final user = await _userRepo.getProfile();
      final meds = await _medRepo.getUserMedications();
      final orders = await _orderRepo.getOrders();
      final notifications = await _notificationRepo.getNotifications();
      final summary = await _homeRepo.getSummary();

      final activeMeds = meds
          .map(
            (m) => ActiveMed(
              name: m.name,
              dosage: '${m.dosageInstruction} · ${m.frequencyPerDay}x/day',
              remaining: m.daysLeft,
              total: (m.daysLeft > 30 ? m.daysLeft : 30),
            ),
          )
          .toList();

      final alerts = summary.refillAlert == null
          ? const <Refill>[]
          : [
              Refill(
                patientId: 'self',
                medicine: summary.refillAlert!.name,
                medicineId: summary.refillAlert!.medicineId,
                daysLeft: summary.refillAlert!.daysLeft,
                risk: summary.refillAlert!.daysLeft <= 2
                    ? RefillRisk.overdue
                    : summary.refillAlert!.daysLeft <= 5
                        ? RefillRisk.high
                        : summary.refillAlert!.daysLeft <= 10
                            ? RefillRisk.medium
                            : RefillRisk.low,
              ),
            ];

      final monthlyInsight = summary.monthlyOrderCount == 0
          ? 'No order activity this month yet'
          : '${summary.monthlyOrderCount} orders · ₹${summary.monthlyTotalSpend.toStringAsFixed(2)} spent this month';

      emit(state.copyWith(
        user: user,
        activeMeds: activeMeds,
        alerts: alerts,
        orders: orders,
        notifications: notifications,
        monthlyInsight: monthlyInsight,
        isLoading: false,
        error: null,
      ));
    } catch (e) {
      emit(state.copyWith(isLoading: false, error: e.toString()));
    }
  }

  Future<void> _onAddMedication(AddMedicationEvent event, Emitter<HomeState> emit) async {
    emit(state.copyWith(isLoading: true, error: null));
    try {
      await _medRepo.addMedication(
        customName: event.medicineName,
        dosageInstruction: event.dosageInstruction,
        frequencyPerDay: event.frequencyPerDay,
        quantityUnits: event.quantityUnits,
      );
      add(LoadHomeDataEvent());
    } catch (e) {
      emit(state.copyWith(isLoading: false, error: e.toString()));
    }
  }

  Future<void> _onReorderRefill(ReorderRefillEvent event, Emitter<HomeState> emit) async {
    emit(state.copyWith(isLoading: true, error: null));
    try {
      final tracked = await _medRepo.getUserMedications();

      int? targetMedicineId = event.medicineId;
      if (targetMedicineId == null) {
        final byName = tracked.where((m) => m.name.toLowerCase() == event.medicineName.toLowerCase()).toList();
        if (byName.isNotEmpty) {
          targetMedicineId = byName.first.medicineId;
        } else {
          final contains = tracked.where((m) => m.name.toLowerCase().contains(event.medicineName.toLowerCase())).toList();
          if (contains.isNotEmpty) {
            targetMedicineId = contains.first.medicineId;
          }
        }
      }

      final meds = targetMedicineId != null
          ? [await _medicineRepo.getMedicine(targetMedicineId)]
          : await _medicineRepo.getMedicines(search: event.medicineName);
      if (meds.isEmpty) {
        throw Exception('Medicine not found for reorder');
      }
      final med = meds.first;

      await _orderRepo.createOrder(
        items: [
          {
            'medicine_id': med.id,
            'name': med.name,
            'quantity': 1,
            'price': med.price,
            'dosage_instruction': 'As needed',
            'strips_count': 1,
          },
        ],
        paymentMethod: 'cod',
      );
      add(LoadHomeDataEvent());
    } catch (e) {
      emit(state.copyWith(isLoading: false, error: e.toString()));
    }
  }
}
