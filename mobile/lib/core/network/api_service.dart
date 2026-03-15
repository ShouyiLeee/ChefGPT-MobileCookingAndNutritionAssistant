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
    List<String> ingredients,
    List<String> filters, {
    String? personaId,
  }) async {
    final res = await _dio.post('/recipes/suggest', data: {
      'ingredients': ingredients,
      'filters': filters,
      if (personaId != null) 'persona_id': personaId,
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
    String message,
    List<Map<String, dynamic>> history, {
    String? personaId,
  }) async {
    final res = await _dio.post('/chat/query', data: {
      'message': message,
      'history': history,
      if (personaId != null) 'persona_id': personaId,
    });
    return res.data as Map<String, dynamic>;
  }

  // ── AI: Meal Plan ─────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> generateMealPlan(
    String goal,
    int days,
    int caloriesTarget, {
    List<String>? personaIds,
    String? userNote,
  }) async {
    final res = await _dio.post('/mealplan/generate', data: {
      'goal': goal,
      'days': days,
      'calories_target': caloriesTarget,
      if (personaIds != null && personaIds.isNotEmpty) 'persona_ids': personaIds,
      if (userNote != null && userNote.isNotEmpty) 'user_note': userNote,
    });
    return res.data as Map<String, dynamic>;
  }

  // ── Memory ────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getMemories() async {
    final res = await _dio.get('/memory/me');
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> addMemory({
    required String category,
    required String key,
    required String value,
  }) async {
    final res = await _dio.post('/memory/me', data: {
      'category': category,
      'key': key,
      'value': value,
    },);
    return res.data as Map<String, dynamic>;
  }

  Future<void> deleteMemory(int memoryId) async {
    await _dio.delete('/memory/me/$memoryId');
  }

  Future<Map<String, dynamic>> clearAllMemories() async {
    final res = await _dio.delete('/memory/me');
    return res.data as Map<String, dynamic>;
  }

  // ── Personas ──────────────────────────────────────────────────────────────

  Future<List<Map<String, dynamic>>> getPersonas() async {
    final res = await _dio.get('/personas');
    return (res.data as List<dynamic>)
        .map((e) => e as Map<String, dynamic>)
        .toList();
  }

  Future<Map<String, dynamic>> getActivePersona() async {
    final res = await _dio.get('/personas/me');
    return res.data as Map<String, dynamic>;
  }

  Future<void> setActivePersona(String personaId) async {
    await _dio.put('/personas/me', data: {'persona_id': personaId});
  }

  Future<Map<String, dynamic>> createPersona(Map<String, dynamic> data) async {
    final res = await _dio.post('/personas', data: data);
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updatePersona(
    String personaId,
    Map<String, dynamic> data,
  ) async {
    final res = await _dio.put('/personas/$personaId', data: data);
    return res.data as Map<String, dynamic>;
  }

  Future<void> deletePersona(String personaId) async {
    await _dio.delete('/personas/$personaId');
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

  // ── AP2: Orders & Payment Mandate ────────────────────────────────────────

  Future<Map<String, dynamic>> confirmPurchase({
    required Map<String, dynamic> cartMandate,
    int? paymentMandateId,
  }) async {
    final res = await _dio.post('/chat/confirm-purchase', data: {
      'cart_mandate': cartMandate,
      if (paymentMandateId != null) 'payment_mandate_id': paymentMandateId,
    },);
    return res.data as Map<String, dynamic>;
  }

  Future<List<dynamic>> getOrders({int page = 1}) async {
    final res = await _dio.get('/orders', queryParameters: {'page': page});
    return res.data as List<dynamic>;
  }

  Future<Map<String, dynamic>> cancelOrder(int orderId) async {
    final res = await _dio.post('/orders/$orderId/cancel');
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getPaymentMandate() async {
    final res = await _dio.get('/payment-mandate');
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> savePaymentMandate(
      Map<String, dynamic> data,) async {
    final res = await _dio.post('/payment-mandate', data: data);
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> placeAgentOrder({
    required Map<String, dynamic> cartMandate,
    int? paymentMandateId,
  }) async {
    final res = await _dio.post('/orders/agent', data: {
      'cart_mandate': cartMandate,
      if (paymentMandateId != null) 'payment_mandate_id': paymentMandateId,
    },);
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
