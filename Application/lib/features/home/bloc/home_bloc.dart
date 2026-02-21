import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../../data/models/chat_models.dart';
import '../../../data/models/order_model.dart';
import '../../../data/models/notification_model.dart';
import '../../../data/models/user_model.dart';
import '../../../data/mock_data.dart';

// ─── Events ──────────────────────────────────────────────
abstract class HomeEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class LoadHomeDataEvent extends HomeEvent {}

// ─── State ───────────────────────────────────────────────
class HomeState extends Equatable {
  final UserModel? user;
  final List<ActiveMed> activeMeds;
  final List<Refill> alerts;
  final List<OrderModel> orders;
  final List<NotificationModel> notifications;
  final bool isLoading;
  final String? error;

  const HomeState({
    this.user,
    this.activeMeds = const [],
    this.alerts = const [],
    this.orders = const [],
    this.notifications = const [],
    this.isLoading = false,
    this.error,
  });

  HomeState copyWith({
    UserModel? user,
    List<ActiveMed>? activeMeds,
    List<Refill>? alerts,
    List<OrderModel>? orders,
    List<NotificationModel>? notifications,
    bool? isLoading,
    String? error,
  }) =>
      HomeState(
        user: user ?? this.user,
        activeMeds: activeMeds ?? this.activeMeds,
        alerts: alerts ?? this.alerts,
        orders: orders ?? this.orders,
        notifications: notifications ?? this.notifications,
        isLoading: isLoading ?? this.isLoading,
        error: error,
      );

  @override
  List<Object?> get props => [user, activeMeds, alerts, orders, notifications, isLoading, error];
}

// ─── Bloc ────────────────────────────────────────────────
class HomeBloc extends Bloc<HomeEvent, HomeState> {
  HomeBloc() : super(const HomeState()) {
    on<LoadHomeDataEvent>(_onLoad);
  }

  Future<void> _onLoad(LoadHomeDataEvent event, Emitter<HomeState> emit) async {
    emit(state.copyWith(isLoading: true));
    try {
      // TODO: Replace mock data with repository calls
      emit(state.copyWith(
        user: MockData.user,
        activeMeds: MockData.activeMeds,
        alerts: MockData.alerts,
        orders: MockData.orders,
        notifications: MockData.notifications,
        isLoading: false,
      ));
    } catch (e) {
      emit(state.copyWith(isLoading: false, error: e.toString()));
    }
  }
}
