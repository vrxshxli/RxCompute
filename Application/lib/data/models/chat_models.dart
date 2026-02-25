import 'medicine_model.dart';
import 'order_model.dart';

/// Active medication tracker (used on home & medicine tabs)
class ActiveMed {
  final String name, dosage;
  final int remaining, total;

  const ActiveMed({
    required this.name,
    required this.dosage,
    required this.remaining,
    required this.total,
  });

  double get percent => (remaining / total).clamp(0.0, 1.0);
}

/// Refill risk
enum RefillRisk { low, medium, high, overdue }

class Refill {
  final String patientId, medicine;
  final int daysLeft;
  final RefillRisk risk;

  const Refill({
    required this.patientId,
    required this.medicine,
    required this.daysLeft,
    required this.risk,
  });
}

/// Chat message types
enum ChatMessageType { text, meds, options, safety, confirmed, typing }

class ChatMessage {
  final String id, text;
  final bool isUser;
  final ChatMessageType type;
  final DateTime timestamp;
  final List<MedicineModel>? medicines;
  final List<SafetyWarning>? warnings;
  final OrderModel? order;

  const ChatMessage({
    required this.id,
    required this.isUser,
    required this.text,
    this.type = ChatMessageType.text,
    required this.timestamp,
    this.medicines,
    this.warnings,
    this.order,
  });
}

class SafetyWarning {
  final String type, medicine, message;

  const SafetyWarning({
    required this.type,
    required this.medicine,
    required this.message,
  });
}
