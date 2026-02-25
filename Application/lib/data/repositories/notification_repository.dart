import '../providers/api_provider.dart';
import '../models/notification_model.dart';
import '../../config/api_config.dart';

class NotificationRepository {
  final ApiProvider _api = ApiProvider();

  Future<List<NotificationModel>> getNotifications() async {
    final res = await _api.dio.get('${ApiConfig.notifications}/');
    return (res.data as List)
        .map((e) => NotificationModel.fromJson(e))
        .toList();
  }

  Future<void> markRead(int notificationId) async {
    await _api.dio.put('${ApiConfig.notifications}/$notificationId/read');
  }

  Future<void> markAllRead() async {
    await _api.dio.put('${ApiConfig.notifications}/read-all');
  }
}
