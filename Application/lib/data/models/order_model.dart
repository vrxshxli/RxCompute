enum OrderStatus {
  pending,
  confirmed,
  verified,
  picking,
  packed,
  dispatched,
  delivered,
  cancelled;

  String get label {
    switch (this) {
      case pending:
        return 'PENDING';
      case confirmed:
        return 'CONFIRMED';
      case verified:
        return 'VERIFIED';
      case picking:
        return 'PICKING';
      case packed:
        return 'PACKED';
      case dispatched:
        return 'IN TRANSIT';
      case delivered:
        return 'DELIVERED';
      case cancelled:
        return 'CANCELLED';
    }
  }

  bool get isActive => this != delivered && this != cancelled;

  static OrderStatus fromString(String s) =>
      OrderStatus.values.firstWhere(
        (e) => e.name == s,
        orElse: () => OrderStatus.pending,
      );
}

class OrderItemModel {
  final int id;
  final int medicineId;
  final String name;
  final int quantity;
  final double price;
  final String? dosageInstruction;
  final int stripsCount;
  final bool rxRequired;
  final String? prescriptionFile;

  const OrderItemModel({
    required this.id,
    required this.medicineId,
    required this.name,
    required this.quantity,
    required this.price,
    this.dosageInstruction,
    this.stripsCount = 1,
    this.rxRequired = false,
    this.prescriptionFile,
  });

  factory OrderItemModel.fromJson(Map<String, dynamic> json) => OrderItemModel(
        id: json['id'],
        medicineId: json['medicine_id'],
        name: json['name'],
        quantity: json['quantity'] ?? 1,
        price: (json['price'] as num).toDouble(),
        dosageInstruction: json['dosage_instruction'],
        stripsCount: json['strips_count'] ?? 1,
        rxRequired: json['rx_required'] ?? false,
        prescriptionFile: json['prescription_file'],
      );

  Map<String, dynamic> toJson() => {
        'medicine_id': medicineId,
        'name': name,
        'quantity': quantity,
        'price': price,
        if (dosageInstruction != null) 'dosage_instruction': dosageInstruction,
        'strips_count': stripsCount,
        if (prescriptionFile != null) 'prescription_file': prescriptionFile,
      };

  String get formattedPrice => '₹${(price * quantity).toStringAsFixed(2)}';
}

class OrderModel {
  final int id;
  final String orderUid;
  final int userId;
  final OrderStatus status;
  final double total;
  final String? pharmacy;
  final String? paymentMethod;
  final List<OrderItemModel> items;
  final DateTime createdAt;

  const OrderModel({
    required this.id,
    required this.orderUid,
    required this.userId,
    required this.status,
    required this.total,
    this.pharmacy,
    this.paymentMethod,
    this.items = const [],
    required this.createdAt,
  });

  factory OrderModel.fromJson(Map<String, dynamic> json) => OrderModel(
        id: json['id'],
        orderUid: json['order_uid'],
        userId: json['user_id'],
        status: OrderStatus.fromString(json['status']),
        total: (json['total'] as num).toDouble(),
        pharmacy: json['pharmacy'],
        paymentMethod: json['payment_method'],
        items: (json['items'] as List?)
                ?.map((e) => OrderItemModel.fromJson(e))
                .toList() ??
            [],
        createdAt: DateTime.tryParse((json['created_at'] ?? '').toString()) ?? DateTime.now(),
      );

  String get formattedTotal => '₹${total.toStringAsFixed(2)}';

  String get formattedDate {
    const m = [
      'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
      'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'
    ];
    return '${createdAt.day} ${m[createdAt.month - 1]} ${createdAt.year}';
  }
}
