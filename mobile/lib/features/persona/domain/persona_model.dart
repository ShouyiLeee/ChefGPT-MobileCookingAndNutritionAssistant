class PersonaModel {
  final String id;
  final String name;
  final String description;
  final String icon;
  final String color;
  final bool isDefault;
  final bool isSystem;          // true = built-in JSON, false = user-created
  final String? createdBy;      // user_id of creator (null for system)
  final bool isPublic;
  final List<String> cuisineFilters;
  final List<String> quickActions;
  // Prompt fields — populated from API when editing a custom persona
  final String systemPrompt;
  final String recipePrefix;
  final String mealPlanPrefix;

  const PersonaModel({
    required this.id,
    required this.name,
    required this.description,
    required this.icon,
    required this.color,
    this.isDefault = false,
    this.isSystem = true,
    this.createdBy,
    this.isPublic = true,
    this.cuisineFilters = const [],
    this.quickActions = const [],
    this.systemPrompt = '',
    this.recipePrefix = '',
    this.mealPlanPrefix = '',
  });

  factory PersonaModel.fromJson(Map<String, dynamic> json) {
    return PersonaModel(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String,
      icon: json['icon'] as String,
      color: json['color'] as String,
      isDefault: json['is_default'] as bool? ?? false,
      isSystem: json['is_system'] as bool? ?? true,
      createdBy: json['created_by'] as String?,
      isPublic: json['is_public'] as bool? ?? true,
      cuisineFilters: (json['cuisine_filters'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      quickActions: (json['quick_actions'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      systemPrompt: json['system_prompt'] as String? ?? '',
      recipePrefix: json['recipe_prefix'] as String? ?? '',
      mealPlanPrefix: json['meal_plan_prefix'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'description': description,
        'icon': icon,
        'color': color,
        'is_default': isDefault,
        'is_system': isSystem,
        'created_by': createdBy,
        'is_public': isPublic,
        'cuisine_filters': cuisineFilters,
        'quick_actions': quickActions,
        'system_prompt': systemPrompt,
        'recipe_prefix': recipePrefix,
        'meal_plan_prefix': mealPlanPrefix,
      };

  /// Parse hex color string "#RRGGBB" to Flutter Color int
  int get colorValue {
    final hex = color.replaceAll('#', '');
    return int.parse('FF$hex', radix: 16);
  }

  /// Whether the current user can edit/delete this persona
  bool canEdit(String currentUserId) =>
      !isSystem && createdBy == currentUserId;

  @override
  bool operator ==(Object other) =>
      identical(this, other) || (other is PersonaModel && other.id == id);

  @override
  int get hashCode => id.hashCode;

  /// Default fallback persona shown when none is selected
  static const PersonaModel defaultPersona = PersonaModel(
    id: 'asian_chef',
    name: 'Đầu bếp Á',
    description: 'Chuyên gia ẩm thực châu Á',
    icon: '🍜',
    color: '#E8A020',
    isDefault: true,
    isSystem: true,
    quickActions: [
      'Gợi ý món Việt từ trứng và cà chua',
      'Cách nấu phở bò chuẩn vị',
      'Món Nhật đơn giản cho bữa tối',
      'Bún bò Huế cần những gì?',
    ],
  );
}
