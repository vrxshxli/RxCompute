import 'package:equatable/equatable.dart';

abstract class AuthEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class GoogleSignInEvent extends AuthEvent {}

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
