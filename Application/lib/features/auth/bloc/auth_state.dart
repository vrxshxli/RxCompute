import 'package:equatable/equatable.dart';

abstract class AuthState extends Equatable {
  @override
  List<Object?> get props => [];
}

class AuthInitial extends AuthState {}

class AuthLoading extends AuthState {}

class OtpSentState extends AuthState {
  final String mockOtp;
  final String phone;
  OtpSentState({required this.mockOtp, required this.phone});

  @override
  List<Object?> get props => [mockOtp, phone];
}

class OtpVerifiedState extends AuthState {
  final int userId;
  final bool isRegistered;
  OtpVerifiedState({required this.userId, required this.isRegistered});

  @override
  List<Object?> get props => [userId, isRegistered];
}

class RegisteredState extends AuthState {}

class LoggedOutState extends AuthState {}

class AuthError extends AuthState {
  final String message;
  AuthError(this.message);

  @override
  List<Object?> get props => [message];
}
