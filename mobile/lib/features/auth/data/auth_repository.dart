import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../../core/network/api_service.dart';
import '../../../core/network/api_result.dart';
import '../../../core/providers/dio_provider.dart';
import '../../../core/constants/app_constants.dart';
import '../../../shared/models/user_model.dart';

class AuthRepository {
  final ApiService _apiService;
  final FlutterSecureStorage _secureStorage;

  AuthRepository(this._apiService, this._secureStorage);

  Future<ApiResult<UserModel>> login(String email, String password) async {
    try {
      final response = await _apiService.login({
        'email': email,
        'password': password,
      });

      final accessToken = response['access_token'];
      final refreshToken = response['refresh_token'];
      final user = UserModel.fromJson(response['user']);

      await _secureStorage.write(key: AppConstants.accessTokenKey, value: accessToken);
      await _secureStorage.write(key: AppConstants.refreshTokenKey, value: refreshToken);
      await _secureStorage.write(key: AppConstants.userIdKey, value: user.id);

      return Success(user);
    } catch (e) {
      return Failure(message: 'Login failed: ${e.toString()}');
    }
  }

  Future<ApiResult<UserModel>> signup(String email, String password, String? name) async {
    try {
      final response = await _apiService.signup({
        'email': email,
        'password': password,
        if (name != null) 'name': name,
      });

      final accessToken = response['access_token'];
      final refreshToken = response['refresh_token'];
      final user = UserModel.fromJson(response['user']);

      await _secureStorage.write(key: AppConstants.accessTokenKey, value: accessToken);
      await _secureStorage.write(key: AppConstants.refreshTokenKey, value: refreshToken);
      await _secureStorage.write(key: AppConstants.userIdKey, value: user.id);

      return Success(user);
    } catch (e) {
      return Failure(message: 'Signup failed: ${e.toString()}');
    }
  }

  Future<ApiResult<void>> logout() async {
    try {
      await _apiService.logout();
      await _secureStorage.deleteAll();
      return const Success(null);
    } catch (e) {
      return Failure(message: 'Logout failed: ${e.toString()}');
    }
  }

  Future<bool> isLoggedIn() async {
    final token = await _secureStorage.read(key: AppConstants.accessTokenKey);
    return token != null;
  }
}

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final apiService = ref.watch(apiServiceProvider);
  const secureStorage = FlutterSecureStorage();
  return AuthRepository(apiService, secureStorage);
});
