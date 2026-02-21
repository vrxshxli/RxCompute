import 'package:flutter/material.dart';

import '../features/auth/screens/splash_screen.dart';
import '../features/auth/screens/login_screen.dart';
import '../features/auth/screens/registration_screen.dart';
import '../features/auth/screens/consent_screen.dart';
import '../features/onboarding/screens/onboarding_screen.dart';
import '../features/home/screens/main_shell.dart';
import '../features/home/screens/notifications_screen.dart';
import '../features/orders/screens/order_tracking_screen.dart';
import '../features/orders/screens/order_history_screen.dart';
import '../features/orders/screens/payment_screen.dart';

class AppRoutes {
  AppRoutes._();

  static const String splash = '/splash';
  static const String onboarding = '/onboarding';
  static const String login = '/login';
  static const String register = '/register';
  static const String consent = '/consent';
  static const String home = '/home';
  static const String notifications = '/notifications';
  static const String orderTracking = '/order-tracking';
  static const String orderHistory = '/order-history';
  static const String payment = '/payment';

  static Map<String, WidgetBuilder> get routes => {
        splash: (_) => const SplashScreen(),
        onboarding: (_) => const OnboardingScreen(),
        login: (_) => const LoginScreen(),
        register: (_) => const RegistrationScreen(),
        consent: (_) => const ConsentScreen(),
        home: (_) => const MainShell(),
        notifications: (_) => const NotificationsScreen(),
        orderTracking: (_) => const OrderTrackingScreen(),
        orderHistory: (_) => const OrderHistoryScreen(),
        payment: (_) => const PaymentScreen(),
      };
}
