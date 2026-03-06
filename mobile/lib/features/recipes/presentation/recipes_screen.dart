import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import '../../../core/network/api_service.dart';
import '../../../core/theme/app_colors.dart';
import '../../../shared/models/recipe_model.dart';

// ── State ─────────────────────────────────────────────────────────────────────

class _RecipesState {
  final List<DishSuggestion> dishes;
  final bool isLoading;
  final String? error;

  const _RecipesState({
    this.dishes = const [],
    this.isLoading = false,
    this.error,
  });

  _RecipesState copyWith({
    List<DishSuggestion>? dishes,
    bool? isLoading,
    String? error,
  }) =>
      _RecipesState(
        dishes: dishes ?? this.dishes,
        isLoading: isLoading ?? this.isLoading,
        error: error,
      );
}

class _RecipesNotifier extends StateNotifier<_RecipesState> {
  final ApiService _api;

  _RecipesNotifier(this._api) : super(const _RecipesState());

  Future<void> suggestFromText(
      List<String> ingredients, List<String> filters) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final res = await _api.suggestRecipes(ingredients, filters);
      final dishes = (res['dishes'] as List<dynamic>? ?? [])
          .map((d) => DishSuggestion.fromJson(d as Map<String, dynamic>))
          .toList();
      state = state.copyWith(dishes: dishes, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: ApiService.parseError(e));
    }
  }

  Future<void> suggestFromImage(List<int> bytes) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final recognized = await _api.recognizeIngredients(bytes);
      final ingredients = (recognized['ingredients'] as List<dynamic>? ?? [])
          .map((e) => e as String)
          .toList();
      if (ingredients.isEmpty) {
        state = state.copyWith(
            isLoading: false,
            error: 'Không nhận diện được nguyên liệu trong ảnh.');
        return;
      }
      await suggestFromText(ingredients, []);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: ApiService.parseError(e));
    }
  }

  void reset() => state = const _RecipesState();
}

final _recipesProvider =
    StateNotifierProvider<_RecipesNotifier, _RecipesState>(
        (ref) => _RecipesNotifier(ref.read(apiServiceProvider)));

// ── Screen ────────────────────────────────────────────────────────────────────

class RecipesScreen extends ConsumerStatefulWidget {
  const RecipesScreen({super.key});

  @override
  ConsumerState<RecipesScreen> createState() => _RecipesScreenState();
}

class _RecipesScreenState extends ConsumerState<RecipesScreen> {
  final TextEditingController _ingredientCtrl = TextEditingController();
  final List<String> _ingredients = [];
  final List<String> _selectedFilters = [];

  static const _filterOptions = [
    'chay',
    'không cay',
    'ít dầu',
    'không gluten',
    'keto',
  ];

  @override
  void dispose() {
    _ingredientCtrl.dispose();
    super.dispose();
  }

  void _addIngredient() {
    final val = _ingredientCtrl.text.trim();
    if (val.isEmpty) return;
    setState(() {
      _ingredients.add(val);
      _ingredientCtrl.clear();
    });
  }

  void _suggest() {
    if (_ingredients.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Vui lòng thêm ít nhất 1 nguyên liệu')),
      );
      return;
    }
    ref
        .read(_recipesProvider.notifier)
        .suggestFromText(_ingredients, _selectedFilters);
  }

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final file = await picker.pickImage(
        source: ImageSource.camera, maxWidth: 1024, imageQuality: 85);
    if (file == null) return;
    final bytes = await file.readAsBytes();
    if (!mounted) return;
    ref.read(_recipesProvider.notifier).suggestFromImage(bytes.toList());
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(_recipesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Gợi ý món ăn'),
        actions: [
          if (state.dishes.isNotEmpty)
            TextButton(
              onPressed: () {
                ref.read(_recipesProvider.notifier).reset();
                setState(() {
                  _ingredients.clear();
                  _selectedFilters.clear();
                });
              },
              child: const Text('Làm mới'),
            )
        ],
      ),
      body: state.isLoading
          ? const Center(
              child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(),
                SizedBox(height: 16),
                Text('Gemini đang gợi ý món ăn...'),
              ],
            ))
          : state.dishes.isNotEmpty
              ? _DishList(dishes: state.dishes)
              : _InputPanel(
                  ingredientCtrl: _ingredientCtrl,
                  ingredients: _ingredients,
                  selectedFilters: _selectedFilters,
                  filterOptions: _filterOptions,
                  onAddIngredient: _addIngredient,
                  onRemoveIngredient: (i) =>
                      setState(() => _ingredients.removeAt(i)),
                  onToggleFilter: (f) => setState(() => _selectedFilters
                          .contains(f)
                      ? _selectedFilters.remove(f)
                      : _selectedFilters.add(f)),
                  onSuggest: _suggest,
                  onCamera: _pickImage,
                  error: state.error,
                ),
    );
  }
}

// ── Input panel ───────────────────────────────────────────────────────────────

class _InputPanel extends StatelessWidget {
  final TextEditingController ingredientCtrl;
  final List<String> ingredients;
  final List<String> selectedFilters;
  final List<String> filterOptions;
  final VoidCallback onAddIngredient;
  final void Function(int) onRemoveIngredient;
  final void Function(String) onToggleFilter;
  final VoidCallback onSuggest;
  final VoidCallback onCamera;
  final String? error;

  const _InputPanel({
    required this.ingredientCtrl,
    required this.ingredients,
    required this.selectedFilters,
    required this.filterOptions,
    required this.onAddIngredient,
    required this.onRemoveIngredient,
    required this.onToggleFilter,
    required this.onSuggest,
    required this.onCamera,
    this.error,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Scan image button
          OutlinedButton.icon(
            onPressed: onCamera,
            icon: const Icon(Icons.camera_alt),
            label: const Text('Chụp ảnh nguyên liệu'),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 12),
            ),
          ),
          const SizedBox(height: 16),
          const Row(children: [
            Expanded(child: Divider()),
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 12),
              child: Text('hoặc nhập thủ công'),
            ),
            Expanded(child: Divider()),
          ]),
          const SizedBox(height: 16),

          // Ingredient input
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: ingredientCtrl,
                  decoration: const InputDecoration(
                    hintText: 'Thêm nguyên liệu (ví dụ: trứng, cà chua)',
                    prefixIcon: Icon(Icons.add),
                  ),
                  onSubmitted: (_) => onAddIngredient(),
                ),
              ),
              const SizedBox(width: 8),
              ElevatedButton(
                onPressed: onAddIngredient,
                child: const Text('Thêm'),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Ingredient chips
          if (ingredients.isNotEmpty) ...[
            Wrap(
              spacing: 8,
              runSpacing: 4,
              children: ingredients
                  .asMap()
                  .entries
                  .map((e) => Chip(
                        label: Text(e.value),
                        onDeleted: () => onRemoveIngredient(e.key),
                        backgroundColor: AppColors.primaryLight,
                      ))
                  .toList(),
            ),
            const SizedBox(height: 16),
          ],

          // Filters
          Text('Bộ lọc:',
              style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 4,
            children: filterOptions
                .map((f) => FilterChip(
                      label: Text(f),
                      selected: selectedFilters.contains(f),
                      onSelected: (_) => onToggleFilter(f),
                      selectedColor: AppColors.primaryLight,
                    ))
                .toList(),
          ),
          const SizedBox(height: 24),

          if (error != null) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.red.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(error!,
                  style: TextStyle(color: Colors.red.shade700)),
            ),
            const SizedBox(height: 16),
          ],

          ElevatedButton.icon(
            onPressed: onSuggest,
            icon: const Icon(Icons.auto_awesome),
            label: const Text('Gợi ý món ăn với Gemini AI'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 14),
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
            ),
          ),
        ],
      ),
    );
  }
}

// ── Dish list ─────────────────────────────────────────────────────────────────

class _DishList extends StatelessWidget {
  final List<DishSuggestion> dishes;
  const _DishList({required this.dishes});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: dishes.length,
      itemBuilder: (_, i) => _DishCard(dish: dishes[i]),
    );
  }
}

class _DishCard extends StatefulWidget {
  final DishSuggestion dish;
  const _DishCard({required this.dish});

  @override
  State<_DishCard> createState() => _DishCardState();
}

class _DishCardState extends State<_DishCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final d = widget.dish;
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ListTile(
            leading: const CircleAvatar(
              backgroundColor: AppColors.primaryLight,
              child: Icon(Icons.restaurant, color: AppColors.primary),
            ),
            title: Text(d.name,
                style: Theme.of(context).textTheme.titleMedium),
            subtitle: Text(d.description, maxLines: 2,
                overflow: TextOverflow.ellipsis),
            trailing: Icon(
                _expanded ? Icons.expand_less : Icons.expand_more),
            onTap: () => setState(() => _expanded = !_expanded),
          ),

          // Nutrition row
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                _NutritionChip(
                    label: '${d.nutrition.calories} kcal',
                    icon: Icons.local_fire_department,
                    color: Colors.orange),
                const SizedBox(width: 8),
                _NutritionChip(
                    label: '${d.nutrition.protein}g protein',
                    icon: Icons.fitness_center,
                    color: Colors.blue),
                const SizedBox(width: 8),
                _NutritionChip(
                    label: '${d.timeMinutes} min',
                    icon: Icons.access_time,
                    color: Colors.green),
              ],
            ),
          ),

          if (_expanded) ...[
            const Divider(),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Hướng dẫn nấu:',
                      style: Theme.of(context).textTheme.titleSmall),
                  const SizedBox(height: 8),
                  ...d.steps.asMap().entries.map(
                        (e) => Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              CircleAvatar(
                                radius: 12,
                                backgroundColor: AppColors.primary,
                                child: Text('${e.key + 1}',
                                    style: const TextStyle(
                                        color: Colors.white, fontSize: 11)),
                              ),
                              const SizedBox(width: 8),
                              Expanded(child: Text(e.value)),
                            ],
                          ),
                        ),
                      ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}

class _NutritionChip extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  const _NutritionChip(
      {required this.label, required this.icon, required this.color});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: color),
        const SizedBox(width: 4),
        Text(label,
            style: Theme.of(context)
                .textTheme
                .bodySmall
                ?.copyWith(color: AppColors.textSecondary)),
      ],
    );
  }
}
