import 'package:equatable/equatable.dart';

/// A Gemini-generated dish suggestion
class DishSuggestion extends Equatable {
  final String name;
  final String description;
  final List<String> steps;
  final int timeMinutes;
  final String difficulty;
  final NutritionInfo nutrition;

  const DishSuggestion({
    required this.name,
    required this.description,
    required this.steps,
    required this.timeMinutes,
    required this.difficulty,
    required this.nutrition,
  });

  factory DishSuggestion.fromJson(Map<String, dynamic> json) => DishSuggestion(
        name: json['name'] as String? ?? '',
        description: json['description'] as String? ?? '',
        steps: (json['steps'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            [],
        timeMinutes: json['time_minutes'] as int? ?? 0,
        difficulty: json['difficulty'] as String? ?? 'medium',
        nutrition: NutritionInfo.fromJson(
            json['nutrition'] as Map<String, dynamic>? ?? {}),
      );

  @override
  List<Object?> get props =>
      [name, description, steps, timeMinutes, difficulty, nutrition];
}

class NutritionInfo extends Equatable {
  final int calories;
  final int protein;
  final int carbs;
  final int fat;

  const NutritionInfo({
    required this.calories,
    required this.protein,
    required this.carbs,
    required this.fat,
  });

  factory NutritionInfo.fromJson(Map<String, dynamic> json) => NutritionInfo(
        calories: (json['calories'] as num?)?.toInt() ?? 0,
        protein: (json['protein'] as num?)?.toInt() ?? 0,
        carbs: (json['carbs'] as num?)?.toInt() ?? 0,
        fat: (json['fat'] as num?)?.toInt() ?? 0,
      );

  @override
  List<Object?> get props => [calories, protein, carbs, fat];
}
