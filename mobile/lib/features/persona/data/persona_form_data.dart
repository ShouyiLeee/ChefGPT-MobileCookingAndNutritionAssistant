/// Data class truyền từ PersonaFormScreen → PersonaNotifier khi create/update
class PersonaFormData {
  final String name;
  final String description;
  final String icon;
  final String color;
  final String systemPrompt;
  final String recipePrefix;
  final String mealPlanPrefix;
  final List<String> quickActions;
  final bool isPublic;

  const PersonaFormData({
    required this.name,
    required this.description,
    required this.icon,
    required this.color,
    required this.systemPrompt,
    required this.recipePrefix,
    required this.mealPlanPrefix,
    required this.quickActions,
    required this.isPublic,
  });

  Map<String, dynamic> toJson() => {
        'name': name,
        'description': description,
        'icon': icon,
        'color': color,
        'system_prompt': systemPrompt,
        'recipe_prefix': recipePrefix,
        'meal_plan_prefix': mealPlanPrefix,
        'quick_actions': quickActions,
        'is_public': isPublic,
      };
}
