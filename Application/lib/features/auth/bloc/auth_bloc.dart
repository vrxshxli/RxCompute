import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../data/repositories/auth_repository.dart';
import 'auth_event.dart';
import 'auth_state.dart';

class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final AuthRepository _repo;

  AuthBloc({AuthRepository? repository})
      : _repo = repository ?? AuthRepository(),
        super(AuthInitial()) {
    on<SendOtpEvent>(_onSendOtp);
    on<VerifyOtpEvent>(_onVerifyOtp);
    on<RegisterEvent>(_onRegister);
    on<LogoutEvent>(_onLogout);
    on<CheckAuthEvent>(_onCheckAuth);
  }

  Future<void> _onSendOtp(SendOtpEvent event, Emitter<AuthState> emit) async {
    emit(AuthLoading());
    try {
      final otp = await _repo.sendOtp(event.phone);
      emit(OtpSentState(mockOtp: otp, phone: event.phone));
    } catch (e) {
      emit(AuthError('Failed to send OTP: ${e.toString()}'));
    }
  }

  Future<void> _onVerifyOtp(VerifyOtpEvent event, Emitter<AuthState> emit) async {
    emit(AuthLoading());
    try {
      final data = await _repo.verifyOtp(event.phone, event.otp);
      emit(OtpVerifiedState(
        userId: data['user_id'],
        isRegistered: data['is_registered'] ?? false,
      ));
    } catch (e) {
      emit(AuthError('Invalid OTP'));
    }
  }

  Future<void> _onRegister(RegisterEvent event, Emitter<AuthState> emit) async {
    emit(AuthLoading());
    try {
      await _repo.registerUser(
        name: event.name,
        age: event.age,
        gender: event.gender,
        email: event.email,
        allergies: event.allergies,
        conditions: event.conditions,
      );
      emit(RegisteredState());
    } catch (e) {
      emit(AuthError('Registration failed: ${e.toString()}'));
    }
  }

  Future<void> _onLogout(LogoutEvent event, Emitter<AuthState> emit) async {
    await _repo.logout();
    emit(LoggedOutState());
  }

  Future<void> _onCheckAuth(CheckAuthEvent event, Emitter<AuthState> emit) async {
    final isLoggedIn = await _repo.isLoggedIn();
    if (!isLoggedIn) {
      emit(LoggedOutState());
    }
  }
}
