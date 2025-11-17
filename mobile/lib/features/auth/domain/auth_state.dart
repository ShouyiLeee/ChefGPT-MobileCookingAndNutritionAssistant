import 'package:equatable/equatable.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../shared/models/user_model.dart';
import '../data/auth_repository.dart';

/// Auth state for managing authentication status
class AuthState extends Equatable {
  final UserModel? user;
  final bool isLoading;
  final String? errorMessage;
  final bool isAuthenticated;

  const AuthState({
    this.user,
    this.isLoading = false,
    this.errorMessage,
    this.isAuthenticated = false,
  });

  AuthState copyWith({
    UserModel? user,
    bool? isLoading,
    String? errorMessage,
    bool? isAuthenticated,
  }) {
    return AuthState(
      user: user ?? this.user,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: errorMessage,
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
    );
  }

  @override
  List<Object?> get props => [user, isLoading, errorMessage, isAuthenticated];
}

/// Auth state notifier
class AuthNotifier extends StateNotifier<AuthState> {
  final AuthRepository _authRepository;

  AuthNotifier(this._authRepository) : super(const AuthState()) {
    _checkAuthStatus();
  }

  Future<void> _checkAuthStatus() async {
    final isLoggedIn = await _authRepository.isLoggedIn();
    state = state.copyWith(isAuthenticated: isLoggedIn);
  }

  Future<void> login(String email, String password) async {
    state = state.copyWith(isLoading: true, errorMessage: null);

    final result = await _authRepository.login(email, password);

    result.onSuccess((user) {
      state = state.copyWith(
        user: user,
        isLoading: false,
        isAuthenticated: true,
      );
    });

    result.onFailure((message) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: message,
        isAuthenticated: false,
      );
    });
  }

  Future<void> signup(String email, String password, String? name) async {
    state = state.copyWith(isLoading: true, errorMessage: null);

    final result = await _authRepository.signup(email, password, name);

    result.onSuccess((user) {
      state = state.copyWith(
        user: user,
        isLoading: false,
        isAuthenticated: true,
      );
    });

    result.onFailure((message) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: message,
        isAuthenticated: false,
      );
    });
  }

  Future<void> logout() async {
    state = state.copyWith(isLoading: true);

    final result = await _authRepository.logout();

    result.onSuccess((_) {
      state = const AuthState(isAuthenticated: false);
    });

    result.onFailure((message) {
      state = state.copyWith(isLoading: false, errorMessage: message);
    });
  }
}

/// Provider for auth state
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final authRepository = ref.watch(authRepositoryProvider);
  return AuthNotifier(authRepository);
});
