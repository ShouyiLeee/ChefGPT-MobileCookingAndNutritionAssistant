import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../network/dio_client.dart';
import '../network/api_service.dart';

/// Provides the DioClient instance
final dioClientProvider = Provider<DioClient>((ref) {
  return DioClient();
});

/// Provides the ApiService instance
final apiServiceProvider = Provider<ApiService>((ref) {
  final dioClient = ref.watch(dioClientProvider);
  return ApiService(dioClient.dio);
});
