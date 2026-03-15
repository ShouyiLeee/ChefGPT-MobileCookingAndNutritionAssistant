import '../../../core/network/api_service.dart';
import '../domain/memory_model.dart';

class MemoryRepository {
  final ApiService _api;
  const MemoryRepository(this._api);

  Future<List<MemoryModel>> fetchAll() async {
    final res = await _api.getMemories();
    final list = res['memories'] as List<dynamic>? ?? [];
    return list
        .map((e) => MemoryModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<String> fetchContextPreview() async {
    final res = await _api.getMemories();
    return res['context_preview'] as String? ?? '';
  }

  Future<MemoryModel> addMemory({
    required String category,
    required String key,
    required String value,
  }) async {
    final res = await _api.addMemory(
      category: category,
      key: key,
      value: value,
    );
    return MemoryModel.fromJson(res);
  }

  Future<void> deleteMemory(int memoryId) async {
    await _api.deleteMemory(memoryId);
  }

  Future<int> clearAllMemories() async {
    final res = await _api.clearAllMemories();
    return res['deleted'] as int? ?? 0;
  }
}
