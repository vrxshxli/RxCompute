import 'package:equatable/equatable.dart';

abstract class AuthState extends Equatable {
  @override
  List<Object?> get props => [];
}

class AuthInitial extends AuthState {}

class AuthLoading extends AuthState {}

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

class RegisteredState extends AuthState {}

class LoggedOutState extends AuthState {}

class AuthError extends AuthState {
  final String message;
  AuthError(this.message);

  @override
  List<Object?> get props => [message];
}
