import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../../data/models/order_model.dart';
import '../../../data/mock_data.dart';

// ─── Events ──────────────────────────────────────────────
abstract class OrderEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class LoadOrdersEvent extends OrderEvent {}

class CreateOrderEvent extends OrderEvent {
  final List<Map<String, dynamic>> items;
  final String? paymentMethod;

  CreateOrderEvent({required this.items, this.paymentMethod});

  @override
  List<Object?> get props => [items, paymentMethod];
}

// ─── State ───────────────────────────────────────────────
class OrderState extends Equatable {
  final List<OrderModel> orders;
  final OrderModel? activeOrder;
  final bool isLoading;
  final String? error;

  const OrderState({
    this.orders = const [],
    this.activeOrder,
    this.isLoading = false,
    this.error,
  });

  OrderState copyWith({
    List<OrderModel>? orders,
    OrderModel? activeOrder,
    bool? isLoading,
    String? error,
  }) =>
      OrderState(
        orders: orders ?? this.orders,
        activeOrder: activeOrder ?? this.activeOrder,
        isLoading: isLoading ?? this.isLoading,
        error: error,
      );

  @override
  List<Object?> get props => [orders, activeOrder, isLoading, error];
}

// ─── Bloc ────────────────────────────────────────────────
class OrderBloc extends Bloc<OrderEvent, OrderState> {
  OrderBloc() : super(const OrderState()) {
    on<LoadOrdersEvent>(_onLoad);
    on<CreateOrderEvent>(_onCreate);
  }

  Future<void> _onLoad(LoadOrdersEvent event, Emitter<OrderState> emit) async {
    emit(state.copyWith(isLoading: true));
    try {
      // TODO: Replace with repository calls
      final orders = MockData.orders;
      final active = orders.where((o) => o.status.isActive).toList();
      emit(state.copyWith(
        orders: orders,
        activeOrder: active.isNotEmpty ? active.first : null,
        isLoading: false,
      ));
    } catch (e) {
      emit(state.copyWith(isLoading: false, error: e.toString()));
    }
  }

  Future<void> _onCreate(CreateOrderEvent event, Emitter<OrderState> emit) async {
    emit(state.copyWith(isLoading: true));
    try {
      // TODO: Call order repository
      emit(state.copyWith(isLoading: false));
    } catch (e) {
      emit(state.copyWith(isLoading: false, error: e.toString()));
    }
  }
}
