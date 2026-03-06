import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../constants/app_constants.dart';

/// Plain Dio-based API client — no code generation needed.
class ApiService {
  late final Dio _dio;
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();

  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConstants.baseUrl,
      connectTimeout: AppConstants.connectionTimeout,
      receiveTimeout: AppConstants.receiveTimeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token =
            await _secureStorage.read(key: AppConstants.accessTokenKey);
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (error, handler) async {
        // FormData cannot be reused after finalization — skip retry for multipart requests
        final isMultipart = error.requestOptions.data is FormData;
        if (error.response?.statusCode == 401 && !isMultipart) {
          final refreshed = await _refreshToken();
          if (refreshed) {
            return handler.resolve(await _retry(error.requestOptions));
          }
        }
        return handler.next(error);
      },
    ));
  }

  // ── Auth ──────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> signup(Map<String, dynamic> data) async {
    final res = await _dio.post('/auth/signup', data: data);
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> login(Map<String, dynamic> data) async {
    final res = await _dio.post('/auth/login', data: data);
    return res.data as Map<String, dynamic>;
  }

  Future<void> logout() async {
    try {
      await _dio.post('/auth/logout');
    } catch (_) {}
  }

  // ── AI: Recipes / Ingredients ─────────────────────────────────────────────

  Future<Map<String, dynamic>> suggestRecipes(
      List<String> ingredients, List<String> filters) async {
    final res = await _dio.post('/recipes/suggest', data: {
      'ingredients': ingredients,
      'filters': filters,
    });
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> recognizeIngredients(
      List<int> imageBytes) async {
    final formData = FormData.fromMap({
      'image': MultipartFile.fromBytes(imageBytes, filename: 'photo.jpg'),
    });
    final res = await _dio.post('/ingredients/recognize', data: formData);
    return res.data as Map<String, dynamic>;
  }

  // ── AI: Chat ──────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> sendChat(
      String message, List<Map<String, dynamic>> history) async {
    final res = await _dio.post('/chat/query', data: {
      'message': message,
      'history': history,
    });
    return res.data as Map<String, dynamic>;
  }

  // ── AI: Meal Plan ─────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> generateMealPlan(
      String goal, int days, int caloriesTarget) async {
    final res = await _dio.post('/mealplan/generate', data: {
      'goal': goal,
      'days': days,
      'calories_target': caloriesTarget,
    });
    return res.data as Map<String, dynamic>;
  }

  // ── Social: Posts ─────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getPosts({int page = 1}) async {
    final res = await _dio.get('/posts', queryParameters: {'page': page, 'limit': 20});
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> createPost(String content) async {
    final res = await _dio.post('/posts', data: {'content': content});
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> toggleLike(int postId) async {
    final res = await _dio.post('/posts/$postId/like');
    return res.data as Map<String, dynamic>;
  }

  Future<void> deletePost(int postId) async {
    await _dio.delete('/posts/$postId');
  }

  // ── Social: Comments ──────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getComments(int postId) async {
    final res = await _dio.get('/posts/$postId/comments');
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> createComment(int postId, String content) async {
    final res = await _dio.post(
      '/posts/$postId/comments',
      data: {'content': content},
    );
    return res.data as Map<String, dynamic>;
  }

  // ── Mock: Shopping List ───────────────────────────────────────────────────

  Future<Map<String, dynamic>> getMockShoppingList() async {
    final res = await _dio.get('/shopping-list/mock');
    return res.data as Map<String, dynamic>;
  }

  // ── Internal helpers ──────────────────────────────────────────────────────

  Future<bool> _refreshToken() async {
    try {
      final refreshToken =
          await _secureStorage.read(key: AppConstants.refreshTokenKey);
      if (refreshToken == null) return false;
      final res = await _dio
          .post('/auth/refresh', data: {'refresh_token': refreshToken});
      if (res.statusCode == 200) {
        await _secureStorage.write(
          key: AppConstants.accessTokenKey,
          value: res.data['access_token'] as String,
        );
        return true;
      }
    } catch (_) {}
    return false;
  }

  Future<Response<dynamic>> _retry(RequestOptions requestOptions) async {
    return _dio.request<dynamic>(
      requestOptions.path,
      data: requestOptions.data,
      queryParameters: requestOptions.queryParameters,
      options: Options(
        method: requestOptions.method,
        headers: requestOptions.headers,
      ),
    );
  }

  // ── Error helper ──────────────────────────────────────────────────────────
  /// Trả về thông báo lỗi dễ đọc từ DioException hoặc các exception khác.
  static String parseError(Object e) {
    if (e is DioException) {
      switch (e.type) {
        case DioExceptionType.connectionTimeout:
          return 'Không thể kết nối server. Kiểm tra backend đang chạy tại localhost:8000.';
        case DioExceptionType.receiveTimeout:
          return 'AI đang xử lý lâu (timeout). Gemini có thể mất 1-2 phút, vui lòng chờ.';
        case DioExceptionType.sendTimeout:
          return 'Gửi dữ liệu thất bại. Thử lại.';
        case DioExceptionType.badResponse:
          final code = e.response?.statusCode;
          final body = e.response?.data;
          if (code == 401 || code == 403) {
            return 'Phần đăng nhập hết hạn. Vui lòng đăng nhập lại.';
          }
          if (code == 422) {
            final detail = body is Map ? body['detail'] : body.toString();
            return 'Dữ liệu không hợp lệ: $detail';
          }
          if (code == 503) return 'AI service đang bận, thử lại sau.';
          return 'Lỗi server $code: ${body is Map ? (body["detail"] ?? body) : body}';
        case DioExceptionType.connectionError:
          return 'Không kết nối được backend. Kiểm tra backend và CORS.';
        case DioExceptionType.cancel:
          return 'Yêu cầu bị huỷ.';
        default:
          return 'Lỗi kết nối: ${e.message}';
      }
    }
    return e.toString();
  }
}

final apiServiceProvider = Provider<ApiService>((ref) => ApiService());
