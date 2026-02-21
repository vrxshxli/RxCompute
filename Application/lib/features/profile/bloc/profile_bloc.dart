import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:dio/dio.dart';
import '../../../data/models/user_model.dart';
import '../../../data/repositories/user_repository.dart';

// ─── Events ──────────────────────────────────────────────
abstract class ProfileEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class LoadProfileEvent extends ProfileEvent {}

class UpdateProfileEvent extends ProfileEvent {
  final String? name;
  final int? age;
  final String? gender;
  final String? email;
  final String? allergies;
  final String? conditions;

  UpdateProfileEvent({
    this.name,
    this.age,
    this.gender,
    this.email,
    this.allergies,
    this.conditions,
  });

  @override
  List<Object?> get props => [name, age, gender, email, allergies, conditions];
}

// ─── State ───────────────────────────────────────────────
class ProfileState extends Equatable {
  final UserModel? user;
  final bool isLoading;
  final String? error;

  const ProfileState({this.user, this.isLoading = false, this.error});

  ProfileState copyWith({UserModel? user, bool? isLoading, String? error}) =>
      ProfileState(
        user: user ?? this.user,
        isLoading: isLoading ?? this.isLoading,
        error: error,
      );

  @override
  List<Object?> get props => [user, isLoading, error];
}

// ─── Bloc ────────────────────────────────────────────────
class ProfileBloc extends Bloc<ProfileEvent, ProfileState> {
  final UserRepository _repo;

  ProfileBloc({UserRepository? repository})
      : _repo = repository ?? UserRepository(),
        super(const ProfileState()) {
    on<LoadProfileEvent>(_onLoad);
    on<UpdateProfileEvent>(_onUpdate);
  }

  Future<void> _onLoad(LoadProfileEvent event, Emitter<ProfileState> emit) async {
    emit(state.copyWith(isLoading: true, error: null));
    try {
      final user = await _repo.getProfile();
      emit(state.copyWith(user: user, isLoading: false));
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        emit(state.copyWith(isLoading: false, error: 'Session expired. Please login again.'));
      } else if (e.type == DioExceptionType.connectionTimeout ||
          e.type == DioExceptionType.receiveTimeout) {
        emit(state.copyWith(isLoading: false, error: 'Server is starting up. Please try again.'));
      } else {
        emit(state.copyWith(isLoading: false, error: 'Failed to load profile.'));
      }
    } catch (e) {
      emit(state.copyWith(isLoading: false, error: e.toString()));
    }
  }

  Future<void> _onUpdate(UpdateProfileEvent event, Emitter<ProfileState> emit) async {
    emit(state.copyWith(isLoading: true, error: null));
    try {
      final updated = await _repo.updateProfile(
        name: event.name,
        age: event.age,
        gender: event.gender,
        email: event.email,
        allergies: event.allergies,
        conditions: event.conditions,
      );
      emit(state.copyWith(user: updated, isLoading: false));
    } on DioException catch (_) {
      emit(state.copyWith(isLoading: false, error: 'Failed to update profile.'));
    } catch (e) {
      emit(state.copyWith(isLoading: false, error: e.toString()));
    }
  }
}
