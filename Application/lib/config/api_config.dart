class ApiConfig {
  ApiConfig._();

  /// Base URL for the FastAPI backend.
  /// ─────────────────────────────────────────────────
  /// LOCAL  : http://10.0.2.2:8000  (Android emulator)
  ///          http://127.0.0.1:8000 (iOS simulator)
  ///          http://localhost:8000  (Web / Desktop)
  /// RENDER : https://rxcompute-api.onrender.com
  /// ─────────────────────────────────────────────────
  static const String baseUrl = 'https://rxcompute-api.onrender.com';

  // Auth
  static const String googleAuth = '/auth/google';
  static const String sendOtp = '/auth/send-otp';
  static const String verifyOtp = '/auth/verify-otp';

  // Users
  static const String register = '/users/register';
  static const String profile = '/users/me';

  // Medicines
  static const String medicines = '/medicines';

  // Orders
  static const String orders = '/orders';
  static const String orderAgent = '/order-agent';

  // Notifications
  static const String notifications = '/notifications';

  // Prediction agent
  static const String predictions = '/predictions';

  // Dynamic home + meds tracker
  static const String homeSummary = '/home/summary';
  static const String userMedications = '/user-medications';

  // Chat
  static const String chatUploadPrescription = '/chat/upload-prescription';
  static const String chatAssistant = '/chat/assistant';
}
