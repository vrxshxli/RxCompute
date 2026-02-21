import 'package:equatable/equatable.dart';

abstract class AuthEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

// ─── Phone OTP Events ─────────────────────────────────────
class SendOtpEvent extends AuthEvent {
  final String phone;
  SendOtpEvent({required this.phone});

  @override
  List<Object?> get props => [phone];
}

class VerifyOtpEvent extends AuthEvent {
  final String phone;
  final String otp;
  VerifyOtpEvent({required this.phone, required this.otp});

  @override
  List<Object?> get props => [phone, otp];
}

// ─── Google Sign-In Event ─────────────────────────────────
class GoogleSignInEvent extends AuthEvent {}

// ─── Registration Event ───────────────────────────────────
class RegisterEvent extends AuthEvent {
  final String name;
  final int age;
  final String gender;
  final String? email;
  final String? allergies;
  final String? conditions;

  RegisterEvent({
    required this.name,
    required this.age,
    required this.gender,
    this.email,
    this.allergies,
    this.conditions,
  });

  @override
  List<Object?> get props => [name, age, gender, email, allergies, conditions];
}

class LogoutEvent extends AuthEvent {}

class CheckAuthEvent extends AuthEvent {}
