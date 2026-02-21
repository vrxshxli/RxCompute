import 'package:equatable/equatable.dart';

abstract class AuthState extends Equatable {
  @override
  List<Object?> get props => [];
}

class AuthInitial extends AuthState {}

class AuthLoading extends AuthState {}

// ─── OTP States ───────────────────────────────────────────
class OtpSentState extends AuthState {
  final String phone;
  final String? mockOtp; // for dev testing
  OtpSentState({required this.phone, this.mockOtp});

  @override
  List<Object?> get props => [phone, mockOtp];
}

class OtpVerifiedState extends AuthState {
  final int userId;
  final bool isRegistered;
  final String? name;
  final String? email;
  final String? profilePicture;

  OtpVerifiedState({
    required this.userId,
    required this.isRegistered,
    this.name,
    this.email,
    this.profilePicture,
  });

  @override
  List<Object?> get props => [userId, isRegistered, name, email, profilePicture];
}

// ─── Google Sign-In State ─────────────────────────────────
class GoogleSignInSuccess extends AuthState {
  final int userId;
  final bool isRegistered;
  final String? name;
  final String? email;
  final String? profilePicture;

  GoogleSignInSuccess({
    required this.userId,
    required this.isRegistered,
    this.name,
    this.email,
    this.profilePicture,
  });

  @override
  List<Object?> get props => [userId, isRegistered, name, email, profilePicture];
}

// ─── Common States ────────────────────────────────────────
class RegisteredState extends AuthState {}

class LoggedOutState extends AuthState {}

class AuthError extends AuthState {
  final String message;
  AuthError(this.message);

  @override
  List<Object?> get props => [message];
}
