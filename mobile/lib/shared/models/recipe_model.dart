import 'package:json_annotation/json_annotation.dart';
import 'package:equatable/equatable.dart';

part 'recipe_model.g.dart';

@JsonSerializable()
class RecipeModel extends Equatable {
  final int id;
  final String title;
  final String description;
  final String? imageUrl;
  final int? prepTime; // in minutes
  final int? cookTime; // in minutes
  final String? difficulty; // easy, medium, hard
  final int? servings;
  final List<RecipeIngredient> ingredients;
  final List<RecipeStep> steps;
  final NutritionInfo? nutrition;
  final String? videoUrl;
  final List<String>? tags;
  final String? authorId;
  final DateTime createdAt;

  const RecipeModel({
    required this.id,
    required this.title,
    required this.description,
    this.imageUrl,
    this.prepTime,
    this.cookTime,
    this.difficulty,
    this.servings,
    required this.ingredients,
    required this.steps,
    this.nutrition,
    this.videoUrl,
    this.tags,
    this.authorId,
    required this.createdAt,
  });

  factory RecipeModel.fromJson(Map<String, dynamic> json) => _$RecipeModelFromJson(json);
  Map<String, dynamic> toJson() => _$RecipeModelToJson(this);

  @override
  List<Object?> get props => [id, title, description, imageUrl, prepTime, cookTime, difficulty, servings, ingredients, steps, nutrition, videoUrl, tags, authorId, createdAt];
}

@JsonSerializable()
class RecipeIngredient extends Equatable {
  final int ingredientId;
  final String name;
  final double quantity;
  final String unit;
  final bool isAvailable;

  const RecipeIngredient({
    required this.ingredientId,
    required this.name,
    required this.quantity,
    required this.unit,
    this.isAvailable = false,
  });

  factory RecipeIngredient.fromJson(Map<String, dynamic> json) => _$RecipeIngredientFromJson(json);
  Map<String, dynamic> toJson() => _$RecipeIngredientToJson(this);

  @override
  List<Object?> get props => [ingredientId, name, quantity, unit, isAvailable];
}

@JsonSerializable()
class RecipeStep extends Equatable {
  final int stepNumber;
  final String instruction;
  final String? imageUrl;
  final int? duration; // in seconds

  const RecipeStep({
    required this.stepNumber,
    required this.instruction,
    this.imageUrl,
    this.duration,
  });

  factory RecipeStep.fromJson(Map<String, dynamic> json) => _$RecipeStepFromJson(json);
  Map<String, dynamic> toJson() => _$RecipeStepToJson(this);

  @override
  List<Object?> get props => [stepNumber, instruction, imageUrl, duration];
}

@JsonSerializable()
class NutritionInfo extends Equatable {
  final double? calories;
  final double? protein;
  final double? carbs;
  final double? fat;
  final double? fiber;
  final double? sugar;
  final double? sodium;

  const NutritionInfo({
    this.calories,
    this.protein,
    this.carbs,
    this.fat,
    this.fiber,
    this.sugar,
    this.sodium,
  });

  factory NutritionInfo.fromJson(Map<String, dynamic> json) => _$NutritionInfoFromJson(json);
  Map<String, dynamic> toJson() => _$NutritionInfoToJson(this);

  @override
  List<Object?> get props => [calories, protein, carbs, fat, fiber, sugar, sodium];
}
