import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../../data/models/user_model.dart';
import '../../../data/mock_data.dart';

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

  UpdateProfileEvent({this.name, this.age, this.gender, this.email});

  @override
  List<Object?> get props => [name, age, gender, email];
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
  ProfileBloc() : super(const ProfileState()) {
    on<LoadProfileEvent>(_onLoad);
    on<UpdateProfileEvent>(_onUpdate);
  }

  Future<void> _onLoad(LoadProfileEvent event, Emitter<ProfileState> emit) async {
    emit(state.copyWith(isLoading: true));
    try {
      // TODO: Replace with UserRepository call
      emit(state.copyWith(user: MockData.user, isLoading: false));
    } catch (e) {
      emit(state.copyWith(isLoading: false, error: e.toString()));
    }
  }

  Future<void> _onUpdate(UpdateProfileEvent event, Emitter<ProfileState> emit) async {
    emit(state.copyWith(isLoading: true));
    try {
      // TODO: Call UserRepository.updateProfile
      emit(state.copyWith(isLoading: false));
    } catch (e) {
      emit(state.copyWith(isLoading: false, error: e.toString()));
    }
  }
}
