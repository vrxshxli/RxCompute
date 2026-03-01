import '../providers/api_provider.dart';
import '../models/order_model.dart';
import '../../config/api_config.dart';

class OrderRepository {
  final ApiProvider _api = ApiProvider();

  Future<List<OrderModel>> getOrders() async {
    final res = await _api.dio.get('${ApiConfig.orders}/');
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
    String? deliveryAddress,
    double? deliveryLat,
    double? deliveryLng,
  }) async {
    final res = await _api.dio.post('${ApiConfig.orders}/', data: {
      'items': items,
      if (pharmacy != null) 'pharmacy': pharmacy,
      if (paymentMethod != null) 'payment_method': paymentMethod,
      if (deliveryAddress != null) 'delivery_address': deliveryAddress,
      if (deliveryLat != null) 'delivery_lat': deliveryLat,
      if (deliveryLng != null) 'delivery_lng': deliveryLng,
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

  Future<OrderModel> cancelMyOrder(int orderId) async {
    final res = await _api.dio.put('${ApiConfig.orders}/$orderId/cancel');
    return OrderModel.fromJson(res.data);
  }

  Future<OrderModel> createOrderViaAgent({
    required List<Map<String, dynamic>> items,
    String? paymentMethod,
    String? deliveryAddress,
    double? deliveryLat,
    double? deliveryLng,
    String source = 'api',
  }) async {
    final res = await _api.dio.post('${ApiConfig.orderAgent}/execute', data: {
      'items': items,
      'payment_method': paymentMethod ?? 'online',
      if (deliveryAddress != null) 'delivery_address': deliveryAddress,
      if (deliveryLat != null) 'delivery_lat': deliveryLat,
      if (deliveryLng != null) 'delivery_lng': deliveryLng,
      'source': source,
    });
    final data = Map<String, dynamic>.from(res.data as Map);
    final ok = data['success'] == true;
    final orderId = data['order_id'];
    if (!ok || orderId is! int) {
      final err = (data['error'] ?? data['safety_summary'] ?? 'Order placement failed').toString();
      throw Exception(err);
    }
    return getOrder(orderId);
  }
}
