import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class LocalNotificationService {
  static final FlutterLocalNotificationsPlugin _plugin = FlutterLocalNotificationsPlugin();
  static bool _initialized = false;

  static Future<void> init() async {
    if (_initialized) return;
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings();
    const settings = InitializationSettings(android: androidSettings, iOS: iosSettings);
    await _plugin.initialize(settings);
    _initialized = true;
  }

  static Future<void> show({
    required String title,
    required String body,
    int id = 0,
  }) async {
    if (!_initialized) {
      await init();
    }
    const android = AndroidNotificationDetails(
      'rxcompute_alerts',
      'RxCompute Alerts',
      channelDescription: 'Order and refill notifications',
      importance: Importance.max,
      priority: Priority.high,
      playSound: true,
    );
    const ios = DarwinNotificationDetails(presentAlert: true, presentBadge: true, presentSound: true);
    await _plugin.show(id, title, body, const NotificationDetails(android: android, iOS: ios));
  }

  static Future<void> showFromRemoteMessage(RemoteMessage message) async {
    final title = message.notification?.title ?? message.data['title']?.toString() ?? 'RxCompute';
    final body = message.notification?.body ?? message.data['body']?.toString() ?? 'New update available';
    final id = DateTime.now().millisecondsSinceEpoch.remainder(1000000);
    await show(title: title, body: body, id: id);
  }
}
