import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_service.dart';
import '../data/memory_repository.dart';
import 'memory_model.dart';

// ── State ──────────────────────────────────────────────────────────────────

class MemoryState {
  final List<MemoryModel> memories;
  final bool isLoading;
  final String? error;
  final String contextPreview;

  const MemoryState({
    this.memories = const [],
    this.isLoading = false,
    this.error,
    this.contextPreview = '',
  });

  MemoryState copyWith({
    List<MemoryModel>? memories,
    bool? isLoading,
    String? error,
    String? contextPreview,
  }) =>
      MemoryState(
        memories: memories ?? this.memories,
        isLoading: isLoading ?? this.isLoading,
        error: error,
        contextPreview: contextPreview ?? this.contextPreview,
      );

  /// Memories grouped by category, in display order.
  Map<String, List<MemoryModel>> get grouped {
    const order = [
      'dietary', 'preference', 'aversion', 'goal', 'constraint', 'context',
    ];
    final map = <String, List<MemoryModel>>{};
    for (final cat in order) {
      final items = memories.where((m) => m.category == cat).toList();
      if (items.isNotEmpty) map[cat] = items;
    }
    return map;
  }
}

// ── Notifier ───────────────────────────────────────────────────────────────

class MemoryNotifier extends StateNotifier<MemoryState> {
  final MemoryRepository _repo;

  MemoryNotifier(this._repo) : super(const MemoryState());

  Future<void> load() async {
    state = state.copyWith(isLoading: true);
    try {
      final memories = await _repo.fetchAll();
      final preview = await _repo.fetchContextPreview();
      state = state.copyWith(
        memories: memories,
        contextPreview: preview,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  Future<bool> addMemory({
    required String category,
    required String key,
    required String value,
  }) async {
    try {
      final mem = await _repo.addMemory(
        category: category,
        key: key,
        value: value,
      );
      state = state.copyWith(memories: [...state.memories, mem]);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<void> deleteMemory(int memoryId) async {
    // Optimistic update
    final prev = state.memories;
    state = state.copyWith(
      memories: prev.where((m) => m.id != memoryId).toList(),
    );
    try {
      await _repo.deleteMemory(memoryId);
    } catch (_) {
      // Rollback on failure
      state = state.copyWith(memories: prev);
    }
  }

  Future<int> clearAll() async {
    final count = await _repo.clearAllMemories();
    state = state.copyWith(memories: [], contextPreview: '');
    return count;
  }
}

// ── Provider ───────────────────────────────────────────────────────────────

final memoryProvider =
    StateNotifierProvider<MemoryNotifier, MemoryState>((ref) {
  final api = ref.read(apiServiceProvider);
  return MemoryNotifier(MemoryRepository(api));
});
