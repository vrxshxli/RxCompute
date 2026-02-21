import '../providers/api_provider.dart';
import '../models/order_model.dart';
import '../../config/api_config.dart';

class OrderRepository {
  final ApiProvider _api = ApiProvider();

  Future<List<OrderModel>> getOrders() async {
    final res = await _api.dio.get(ApiConfig.orders);
    return (res.data as List)
        .map((e) => OrderModel.fromJson(e))
        .toList();
  }

  Future<OrderModel> getOrder(int id) async {
    final res = await _api.dio.get('${ApiConfig.orders}/$id');
    return OrderModel.fromJson(res.data);
  }

  Future<OrderModel> createOrder({
    required List<Map<String, dynamic>> items,
    String? pharmacy,
    String? paymentMethod,
  }) async {
    final res = await _api.dio.post(ApiConfig.orders, data: {
      'items': items,
      if (pharmacy != null) 'pharmacy': pharmacy,
      if (paymentMethod != null) 'payment_method': paymentMethod,
    });
    return OrderModel.fromJson(res.data);
  }

  Future<OrderModel> updateStatus(int orderId, String status) async {
    final res = await _api.dio.put(
      '${ApiConfig.orders}/$orderId/status',
      data: {'status': status},
    );
    return OrderModel.fromJson(res.data);
  }
}
