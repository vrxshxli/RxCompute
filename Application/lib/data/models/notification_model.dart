enum NotificationType { refill, order, safety, system }

class NotificationModel {
  final int id;
  final int userId;
  final NotificationType type;
  final String title;
  final String body;
  final bool isRead;
  final bool hasAction;
  final DateTime createdAt;

  const NotificationModel({
    required this.id,
    required this.userId,
    required this.type,
    required this.title,
    required this.body,
    this.isRead = false,
    this.hasAction = false,
    required this.createdAt,
  });

  factory NotificationModel.fromJson(Map<String, dynamic> json) =>
      NotificationModel(
        id: json['id'],
        userId: json['user_id'],
        type: _parseType(json['type']),
        title: json['title'],
        body: json['body'],
        isRead: json['is_read'] ?? false,
        hasAction: json['has_action'] ?? false,
        createdAt: DateTime.parse(json['created_at']),
      );

  static NotificationType _parseType(String? t) {
    switch (t) {
      case 'refill':
        return NotificationType.refill;
      case 'order':
        return NotificationType.order;
      case 'safety':
        return NotificationType.safety;
      default:
        return NotificationType.system;
    }
  }
}
