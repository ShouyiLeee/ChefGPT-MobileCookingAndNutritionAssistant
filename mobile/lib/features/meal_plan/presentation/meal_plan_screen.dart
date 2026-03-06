import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_service.dart';
import '../../../core/theme/app_colors.dart';
import '../../../shared/models/meal_plan_model.dart';

// ── State ─────────────────────────────────────────────────────────────────────

class _MealPlanState {
  final List<MealPlanDay> plan;
  final NutritionSummary? summary;
  final bool isLoading;
  final String? error;

  const _MealPlanState({
    this.plan = const [],
    this.summary,
    this.isLoading = false,
    this.error,
  });

  _MealPlanState copyWith({
    List<MealPlanDay>? plan,
    NutritionSummary? summary,
    bool? isLoading,
    String? error,
  }) =>
      _MealPlanState(
        plan: plan ?? this.plan,
        summary: summary ?? this.summary,
        isLoading: isLoading ?? this.isLoading,
        error: error,
      );
}

class _MealPlanNotifier extends StateNotifier<_MealPlanState> {
  final ApiService _api;

  _MealPlanNotifier(this._api) : super(const _MealPlanState());

  Future<void> generate(String goal, int days, int calories) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final res = await _api.generateMealPlan(goal, days, calories);
      final plan = (res['plan'] as List<dynamic>? ?? [])
          .map((d) => MealPlanDay.fromJson(d as Map<String, dynamic>))
          .toList();
      final summary = res['nutrition_summary'] != null
          ? NutritionSummary.fromJson(
              res['nutrition_summary'] as Map<String, dynamic>)
          : null;
      state = state.copyWith(plan: plan, summary: summary, isLoading: false);
    } catch (e) {
      state = state.copyWith(
          isLoading: false, error: ApiService.parseError(e));
    }
  }

  void reset() => state = const _MealPlanState();
}

final _mealPlanProvider =
    StateNotifierProvider<_MealPlanNotifier, _MealPlanState>(
        (ref) => _MealPlanNotifier(ref.read(apiServiceProvider)));

// ── Screen ────────────────────────────────────────────────────────────────────

class MealPlanScreen extends ConsumerStatefulWidget {
  const MealPlanScreen({super.key});

  @override
  ConsumerState<MealPlanScreen> createState() => _MealPlanScreenState();
}

class _MealPlanScreenState extends ConsumerState<MealPlanScreen> {
  String _goal = 'eat_clean';
  int _days = 7;
  int _calories = 1800;

  static const _goals = {
    'eat_clean': 'Ăn sạch (Eat Clean)',
    'weight_loss': 'Giảm cân',
    'muscle_gain': 'Tăng cơ',
    'keto': 'Keto',
  };

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(_mealPlanProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Kế hoạch bữa ăn'),
        actions: [
          if (state.plan.isNotEmpty)
            TextButton(
              onPressed: () => ref.read(_mealPlanProvider.notifier).reset(),
              child: const Text('Lam moi'),
            ),
        ],
      ),
      body: state.isLoading
          ? const Center(
              child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(),
                SizedBox(height: 16),
                Text('Gemini đang tạo thực đơn...'),
              ],
            ))
          : state.plan.isNotEmpty
              ? _PlanResult(plan: state.plan, summary: state.summary)
              : _ConfigPanel(
                  goal: _goal,
                  days: _days,
                  calories: _calories,
                  goals: _goals,
                  onGoalChanged: (v) => setState(() => _goal = v),
                  onDaysChanged: (v) => setState(() => _days = v),
                  onCaloriesChanged: (v) => setState(() => _calories = v),
                  onGenerate: () => ref
                      .read(_mealPlanProvider.notifier)
                      .generate(_goal, _days, _calories),
                  error: state.error,
                ),
    );
  }
}

// ── Config panel ──────────────────────────────────────────────────────────────

class _ConfigPanel extends StatelessWidget {
  final String goal;
  final int days;
  final int calories;
  final Map<String, String> goals;
  final void Function(String) onGoalChanged;
  final void Function(int) onDaysChanged;
  final void Function(int) onCaloriesChanged;
  final VoidCallback onGenerate;
  final String? error;

  const _ConfigPanel({
    required this.goal,
    required this.days,
    required this.calories,
    required this.goals,
    required this.onGoalChanged,
    required this.onDaysChanged,
    required this.onCaloriesChanged,
    required this.onGenerate,
    this.error,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Goal
          Text('Mục tiêu dinh dưỡng',
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          ...goals.entries.map((e) => RadioListTile<String>(
                value: e.key,
                groupValue: goal,
                title: Text(e.value),
                onChanged: (v) => onGoalChanged(v!),
                activeColor: AppColors.primary,
              )),
          const SizedBox(height: 16),
          const Divider(),
          const SizedBox(height: 16),

          // Days
          Text('Số ngày: $days ngày',
              style: Theme.of(context).textTheme.titleMedium),
          Slider(
            value: days.toDouble(),
            min: 1,
            max: 14,
            divisions: 13,
            label: '$days',
            activeColor: AppColors.primary,
            onChanged: (v) => onDaysChanged(v.toInt()),
          ),
          const SizedBox(height: 8),

          // Calories
          Text('Mục tiêu calories: $calories kcal/ngày',
              style: Theme.of(context).textTheme.titleMedium),
          Slider(
            value: calories.toDouble(),
            min: 1200,
            max: 3000,
            divisions: 18,
            label: '$calories kcal',
            activeColor: AppColors.primary,
            onChanged: (v) => onCaloriesChanged(v.toInt()),
          ),
          const SizedBox(height: 24),

          if (error != null) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.red.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child:
                  Text(error!, style: TextStyle(color: Colors.red.shade700)),
            ),
            const SizedBox(height: 16),
          ],

          ElevatedButton.icon(
            onPressed: onGenerate,
            icon: const Icon(Icons.auto_awesome),
            label: const Text('Tạo thực đơn với Gemini AI'),
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

// ── Plan result ───────────────────────────────────────────────────────────────

class _PlanResult extends StatelessWidget {
  final List<MealPlanDay> plan;
  final NutritionSummary? summary;

  const _PlanResult({required this.plan, this.summary});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (summary != null) _SummaryCard(summary: summary!),
        const SizedBox(height: 8),
        ...plan.map((day) => _DayCard(day: day)),
      ],
    );
  }
}

class _SummaryCard extends StatelessWidget {
  final NutritionSummary summary;
  const _SummaryCard({required this.summary});

  @override
  Widget build(BuildContext context) {
    return Card(
      color: AppColors.primaryLight,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Tổng quan dinh dưỡng trung bình/ngày',
                style: Theme.of(context)
                    .textTheme
                    .titleSmall
                    ?.copyWith(color: AppColors.primary)),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _NutStat(label: 'Calories', value: '${summary.avgCalories}'),
                _NutStat(label: 'Protein', value: '${summary.avgProtein}g'),
                _NutStat(label: 'Carbs', value: '${summary.avgCarbs}g'),
                _NutStat(label: 'Fat', value: '${summary.avgFat}g'),
              ],
            ),
            if (summary.notes.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(summary.notes,
                  style: Theme.of(context)
                      .textTheme
                      .bodySmall
                      ?.copyWith(color: AppColors.textSecondary)),
            ]
          ],
        ),
      ),
    );
  }
}

class _NutStat extends StatelessWidget {
  final String label;
  final String value;
  const _NutStat({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value,
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(color: AppColors.primary)),
        Text(label,
            style: Theme.of(context)
                .textTheme
                .bodySmall
                ?.copyWith(color: AppColors.textSecondary)),
      ],
    );
  }
}

class _DayCard extends StatelessWidget {
  final MealPlanDay day;
  const _DayCard({required this.day});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Ngày ${day.day}',
                style: Theme.of(context)
                    .textTheme
                    .titleMedium
                    ?.copyWith(color: AppColors.primary)),
            const Divider(),
            _MealRow(icon: Icons.wb_sunny, label: 'Sáng', meal: day.breakfast),
            const SizedBox(height: 8),
            _MealRow(icon: Icons.lunch_dining, label: 'Trưa', meal: day.lunch),
            const SizedBox(height: 8),
            _MealRow(
                icon: Icons.dinner_dining, label: 'Tối', meal: day.dinner),
          ],
        ),
      ),
    );
  }
}

class _MealRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String meal;
  const _MealRow(
      {required this.icon, required this.label, required this.meal});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 18, color: AppColors.textSecondary),
        const SizedBox(width: 8),
        SizedBox(
          width: 45,
          child: Text('$label:',
              style: const TextStyle(fontWeight: FontWeight.w600)),
        ),
        Expanded(child: Text(meal)),
      ],
    );
  }
}
