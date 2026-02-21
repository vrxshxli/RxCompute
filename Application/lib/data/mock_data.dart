import 'models/medicine_model.dart';
import 'models/order_model.dart';
import 'models/notification_model.dart';
import 'models/chat_models.dart';
import 'models/user_model.dart';

/// Mock data used for offline / demo mode.
class MockData {
  MockData._();

  static const user = UserModel(
    id: 1,
    phone: '+91 98765 43210',
    name: 'Deepak Sharma',
    age: 34,
    gender: 'M',
    email: 'deepak@gmail.com',
    allergies: 'Penicillin',
    conditions: 'Hypertension',
    isVerified: true,
    isRegistered: true,
  );

  static const activeMeds = [
    ActiveMed(name: 'NORSAN Omega-3 Total', dosage: 'Once daily', remaining: 18, total: 30),
    ActiveMed(name: 'Panthenol Spray', dosage: 'Twice daily', remaining: 5, total: 30),
    ActiveMed(name: 'Paracetamol 500mg', dosage: 'As needed', remaining: 22, total: 30),
  ];

  static const lowMeds = [
    ActiveMed(name: 'Panthenol Spray', dosage: 'Twice daily', remaining: 5, total: 30),
    ActiveMed(name: 'Vitamin D3 1000 IU', dosage: 'Once daily', remaining: 3, total: 60),
  ];

  static final hist = [
    {'n': 'Amoxicillin 500mg', 'd': '12 JAN 2026', 'q': '2', 'f': '3× daily'},
    {'n': 'Ibuprofen 400mg', 'd': '28 DEC 2025', 'q': '1', 'f': 'As needed'},
    {'n': 'Cetirizine 10mg', 'd': '15 DEC 2025', 'q': '1', 'f': 'Once daily'},
    {'n': 'Panthenol Spray', 'd': '05 DEC 2025', 'q': '3', 'f': 'Twice daily'},
    {'n': 'NORSAN Omega-3', 'd': '20 NOV 2025', 'q': '1', 'f': 'Once daily'},
  ];

  static const alerts = [
    Refill(patientId: 'PAT001', medicine: 'Panthenol Spray', daysLeft: 5, risk: RefillRisk.high),
    Refill(patientId: 'PAT001', medicine: 'Vitamin D3 1000 IU', daysLeft: 3, risk: RefillRisk.high),
  ];

  static final medicines = [
    MedicineModel(id: 1, name: 'NORSAN Omega-3 Total', pzn: '13476520', price: 27.00, package: '200 ml', stock: 47),
    MedicineModel(id: 2, name: 'Paracetamol 500mg', pzn: '03295091', price: 4.50, package: '20 st', stock: 156),
    MedicineModel(id: 3, name: 'Panthenol Spray, 46,3 mg/g', pzn: '04020784', price: 8.90, package: '130 g', stock: 23),
    MedicineModel(id: 4, name: 'Mucosolvan Capsules 75mg', pzn: '11162860', price: 12.50, package: '50 st', stock: 34, rxRequired: true),
    MedicineModel(id: 5, name: 'Ibuprofen 400mg', pzn: '02188645', price: 5.20, package: '50 st', stock: 89),
    MedicineModel(id: 6, name: 'Vitamin D3 1000 IU', pzn: '08451902', price: 9.50, package: '60 st', stock: 135),
  ];

  static final orders = [
    OrderModel(
      id: 1,
      orderUid: 'ORD-20260218-A3F2C1',
      userId: 1,
      status: OrderStatus.picking,
      total: 35.90,
      pharmacy: 'PH-002',
      items: const [
        OrderItemModel(id: 1, medicineId: 1, name: 'NORSAN Omega-3 Total', quantity: 1, price: 27.00),
        OrderItemModel(id: 2, medicineId: 3, name: 'Panthenol Spray', quantity: 1, price: 8.90),
      ],
      createdAt: DateTime.now().subtract(const Duration(hours: 3)),
    ),
    OrderModel(
      id: 2,
      orderUid: 'ORD-20260215-B7D4E2',
      userId: 1,
      status: OrderStatus.delivered,
      total: 18.30,
      items: const [
        OrderItemModel(id: 3, medicineId: 2, name: 'Paracetamol 500mg', quantity: 2, price: 4.50),
        OrderItemModel(id: 4, medicineId: 6, name: 'Vitamin D3 1000 IU', quantity: 1, price: 9.50),
      ],
      createdAt: DateTime.now().subtract(const Duration(days: 3)),
    ),
    OrderModel(
      id: 3,
      orderUid: 'ORD-20260210-C9A1B3',
      userId: 1,
      status: OrderStatus.delivered,
      total: 27.00,
      items: const [
        OrderItemModel(id: 5, medicineId: 1, name: 'NORSAN Omega-3 Total', quantity: 1, price: 27.00),
      ],
      createdAt: DateTime.now().subtract(const Duration(days: 8)),
    ),
  ];

  static final notifications = [
    NotificationModel(id: 1, userId: 1, type: NotificationType.refill, title: 'Refill Reminder', body: 'Panthenol Spray runs out in 5 days.', hasAction: true, createdAt: DateTime.now().subtract(const Duration(hours: 2))),
    NotificationModel(id: 2, userId: 1, type: NotificationType.order, title: 'Order In Progress', body: 'ORD-20260218-A3F2C1 is being picked.', createdAt: DateTime.now().subtract(const Duration(hours: 3))),
    NotificationModel(id: 3, userId: 1, type: NotificationType.safety, title: 'Safety Update', body: 'Penicillin flagged in your records.', isRead: true, createdAt: DateTime.now().subtract(const Duration(days: 1))),
    NotificationModel(id: 4, userId: 1, type: NotificationType.order, title: 'Delivered', body: 'ORD-20260215-B7D4E2 delivered.', isRead: true, createdAt: DateTime.now().subtract(const Duration(days: 2))),
  ];

  static final chatInitial = [
    ChatMessage(
      id: '0',
      isUser: false,
      text: 'Hello, Deepak. I\'m your AI pharmacist.\nOrder medicines by typing or speaking — try "I need omega 3 and paracetamol".',
      timestamp: DateTime.now().subtract(const Duration(minutes: 5)),
    ),
  ];

  // Order tracking steps for active order
  static List<Map<String, dynamic>> get orderSteps => [
    {'label': 'Order Confirmed', 'ts': DateTime.now().subtract(const Duration(hours: 3)), 'done': true},
    {'label': 'Pharmacy Verified', 'detail': 'East Pharmacy (PH-002)', 'ts': DateTime.now().subtract(const Duration(hours: 2, minutes: 30)), 'done': true},
    {'label': 'Picking', 'detail': 'Warehouse WH-001', 'ts': DateTime.now().subtract(const Duration(hours: 1)), 'done': false, 'current': true},
    {'label': 'Packed', 'done': false},
    {'label': 'Dispatched', 'done': false},
    {'label': 'Delivered', 'done': false},
  ];
}
