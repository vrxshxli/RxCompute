import 'package:dio/dio.dart';
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
    on<GoogleSignInEvent>(_onGoogleSignIn);
    on<RegisterEvent>(_onRegister);
    on<LogoutEvent>(_onLogout);
    on<CheckAuthEvent>(_onCheckAuth);
  }

  // ─── Friendly error message ──────────────────────────────
  String _friendlyError(dynamic e, String fallback) {
    if (e is DioException) {
      if (e.type == DioExceptionType.connectionTimeout ||
          e.type == DioExceptionType.receiveTimeout ||
          e.type == DioExceptionType.sendTimeout) {
        return 'Server is starting up. Please wait a moment and try again.';
      }
      if (e.type == DioExceptionType.connectionError) {
        return 'No internet connection. Please check your network.';
      }
      if (e.response?.statusCode == 401) {
        return 'Invalid credentials. Please try again.';
      }
      if (e.response?.statusCode == 500) {
        return 'Server error. Please try again later.';
      }
    }
    return fallback;
  }

  // ─── Phone OTP ──────────────────────────────────────────
  Future<void> _onSendOtp(SendOtpEvent event, Emitter<AuthState> emit) async {
    emit(AuthLoading());
    try {
      final data = await _repo.sendOtp(event.phone);
      emit(OtpSentState(
        phone: event.phone,
        mockOtp: data['mock_otp'],
      ));
    } catch (e) {
      emit(AuthError(_friendlyError(e, 'Failed to send OTP. Please try again.')));
    }
  }

  Future<void> _onVerifyOtp(VerifyOtpEvent event, Emitter<AuthState> emit) async {
    emit(AuthLoading());
    try {
      final data = await _repo.verifyOtp(event.phone, event.otp);
      emit(OtpVerifiedState(
        userId: data['user_id'],
        isRegistered: data['is_registered'] ?? false,
        name: data['name'],
        email: data['email'],
        profilePicture: data['profile_picture'],
      ));
    } catch (e) {
      emit(AuthError(_friendlyError(e, 'Invalid OTP. Please try again.')));
    }
  }

  // ─── Google Sign-In ─────────────────────────────────────
  Future<void> _onGoogleSignIn(GoogleSignInEvent event, Emitter<AuthState> emit) async {
    emit(AuthLoading());
    try {
      final data = await _repo.signInWithGoogle();
      if (data == null) {
        emit(AuthInitial()); // User cancelled
        return;
      }
      emit(GoogleSignInSuccess(
        userId: data['user_id'],
        isRegistered: data['is_registered'] ?? false,
        name: data['name'],
        email: data['email'],
        profilePicture: data['profile_picture'],
      ));
    } catch (e) {
      emit(AuthError(_friendlyError(e, 'Google Sign-In failed. Please try again.')));
    }
  }

  // ─── Registration ───────────────────────────────────────
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
      emit(AuthError(_friendlyError(e, 'Registration failed. Please try again.')));
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
