import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../data/repositories/auth_repository.dart';
import 'auth_event.dart';
import 'auth_state.dart';

class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final AuthRepository _repo;

  AuthBloc({AuthRepository? repository})
      : _repo = repository ?? AuthRepository(),
        super(AuthInitial()) {
    on<GoogleSignInEvent>(_onGoogleSignIn);
    on<RegisterEvent>(_onRegister);
    on<LogoutEvent>(_onLogout);
    on<CheckAuthEvent>(_onCheckAuth);
  }

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
      emit(AuthError('Google Sign-In failed: ${e.toString()}'));
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
