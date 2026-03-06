import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_service.dart';
import '../../../core/theme/app_colors.dart';

// ── Model ─────────────────────────────────────────────────────────────────────

class _GroceryItem {
  final String name;
  final String quantity;
  bool checked;

  _GroceryItem(
      {required this.name, required this.quantity, this.checked = false});

  factory _GroceryItem.fromJson(Map<String, dynamic> json) => _GroceryItem(
        name: json['name'] as String? ?? '',
        quantity: json['quantity'] as String? ?? '',
        checked: json['checked'] as bool? ?? false,
      );
}

class _GroceryCategory {
  final String name;
  final List<_GroceryItem> items;

  _GroceryCategory({required this.name, required this.items});

  factory _GroceryCategory.fromJson(Map<String, dynamic> json) =>
      _GroceryCategory(
        name: json['name'] as String? ?? '',
        items: (json['items'] as List<dynamic>? ?? [])
            .map((i) => _GroceryItem.fromJson(i as Map<String, dynamic>))
            .toList(),
      );
}

// ── State ─────────────────────────────────────────────────────────────────────

class _GroceryState {
  final List<_GroceryCategory> categories;
  final bool isLoading;
  final String? error;

  const _GroceryState(
      {this.categories = const [], this.isLoading = false, this.error});

  _GroceryState copyWith({
    List<_GroceryCategory>? categories,
    bool? isLoading,
    String? error,
  }) =>
      _GroceryState(
        categories: categories ?? this.categories,
        isLoading: isLoading ?? this.isLoading,
        error: error,
      );
}

class _GroceryNotifier extends StateNotifier<_GroceryState> {
  final ApiService _api;

  _GroceryNotifier(this._api) : super(const _GroceryState(isLoading: true)) {
    _load();
  }

  Future<void> _load() async {
    try {
      final res = await _api.getMockShoppingList();
      final cats = (res['categories'] as List<dynamic>? ?? [])
          .map((c) =>
              _GroceryCategory.fromJson(c as Map<String, dynamic>))
          .toList();
      state = state.copyWith(categories: cats, isLoading: false);
    } catch (e) {
      state = state.copyWith(
          isLoading: false, error: 'Loi tai danh sach: ${e.toString()}');
    }
  }

  void reload() {
    state = const _GroceryState(isLoading: true);
    _load();
  }

  void toggleItem(int catIndex, int itemIndex) {
    final cats = state.categories.toList();
    cats[catIndex].items[itemIndex].checked =
        !cats[catIndex].items[itemIndex].checked;
    state = state.copyWith(categories: cats);
  }
}

final _groceryProvider =
    StateNotifierProvider<_GroceryNotifier, _GroceryState>(
        (ref) => _GroceryNotifier(ref.read(apiServiceProvider)));

// ── Screen ────────────────────────────────────────────────────────────────────

class GroceryScreen extends ConsumerWidget {
  const GroceryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(_groceryProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Danh sach mua sam'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(_groceryProvider.notifier).reload(),
          ),
        ],
      ),
      body: state.isLoading
          ? const Center(child: CircularProgressIndicator())
          : state.error != null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.error_outline,
                          size: 48, color: AppColors.error),
                      const SizedBox(height: 12),
                      Text(state.error!),
                      const SizedBox(height: 12),
                      ElevatedButton(
                        onPressed: () =>
                            ref.read(_groceryProvider.notifier).reload(),
                        child: const Text('Thu lai'),
                      ),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.only(bottom: 24),
                  itemCount: state.categories.length,
                  itemBuilder: (_, catIdx) {
                    final cat = state.categories[catIdx];
                    return _CategorySection(
                      category: cat,
                      catIndex: catIdx,
                      onToggle: (itemIdx) => ref
                          .read(_groceryProvider.notifier)
                          .toggleItem(catIdx, itemIdx),
                    );
                  },
                ),
    );
  }
}

class _CategorySection extends StatelessWidget {
  final _GroceryCategory category;
  final int catIndex;
  final void Function(int) onToggle;

  const _CategorySection({
    required this.category,
    required this.catIndex,
    required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding:
              const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          color: AppColors.surface,
          child: Row(
            children: [
              const Icon(Icons.label, size: 18, color: AppColors.primary),
              const SizedBox(width: 8),
              Text(category.name,
                  style: Theme.of(context)
                      .textTheme
                      .titleSmall
                      ?.copyWith(color: AppColors.primary)),
            ],
          ),
        ),
        ...category.items.asMap().entries.map(
              (e) => CheckboxListTile(
                value: e.value.checked,
                onChanged: (_) => onToggle(e.key),
                title: Text(
                  e.value.name,
                  style: TextStyle(
                    decoration: e.value.checked
                        ? TextDecoration.lineThrough
                        : null,
                    color: e.value.checked
                        ? AppColors.textHint
                        : AppColors.textPrimary,
                  ),
                ),
                subtitle: Text(e.value.quantity,
                    style: const TextStyle(
                        fontSize: 12, color: AppColors.textSecondary)),
                activeColor: AppColors.primary,
                controlAffinity: ListTileControlAffinity.leading,
              ),
            ),
      ],
    );
  }
}
