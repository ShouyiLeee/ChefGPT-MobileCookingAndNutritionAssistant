import 'package:equatable/equatable.dart';

class MealPlanDay extends Equatable {
  final int day;
  final String breakfast;
  final String lunch;
  final String dinner;

  const MealPlanDay({
    required this.day,
    required this.breakfast,
    required this.lunch,
    required this.dinner,
  });

  factory MealPlanDay.fromJson(Map<String, dynamic> json) {
    final meals = json['meals'] as Map<String, dynamic>? ?? {};
    return MealPlanDay(
      day: json['day'] as int? ?? 0,
      breakfast: meals['breakfast'] as String? ?? '',
      lunch: meals['lunch'] as String? ?? '',
      dinner: meals['dinner'] as String? ?? '',
    );
  }

  @override
  List<Object?> get props => [day, breakfast, lunch, dinner];
}

class NutritionSummary extends Equatable {
  final int avgCalories;
  final int avgProtein;
  final int avgCarbs;
  final int avgFat;
  final String notes;

  const NutritionSummary({
    required this.avgCalories,
    required this.avgProtein,
    required this.avgCarbs,
    required this.avgFat,
    required this.notes,
  });

  factory NutritionSummary.fromJson(Map<String, dynamic> json) =>
      NutritionSummary(
        avgCalories: (json['avg_calories'] as num?)?.toInt() ?? 0,
        avgProtein: (json['avg_protein'] as num?)?.toInt() ?? 0,
        avgCarbs: (json['avg_carbs'] as num?)?.toInt() ?? 0,
        avgFat: (json['avg_fat'] as num?)?.toInt() ?? 0,
        notes: json['notes'] as String? ?? '',
      );

  @override
  List<Object?> get props =>
      [avgCalories, avgProtein, avgCarbs, avgFat, notes];
}
