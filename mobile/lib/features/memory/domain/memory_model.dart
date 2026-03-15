class MemoryModel {
  final int id;
  final String category;
  final String key;
  final String value;
  final double confidence;
  final String source;
  final DateTime createdAt;

  const MemoryModel({
    required this.id,
    required this.category,
    required this.key,
    required this.value,
    required this.confidence,
    required this.source,
    required this.createdAt,
  });

  factory MemoryModel.fromJson(Map<String, dynamic> json) => MemoryModel(
        id: json['id'] as int,
        category: json['category'] as String,
        key: json['key'] as String,
        value: json['value'] as String,
        confidence: (json['confidence'] as num).toDouble(),
        source: json['source'] as String,
        createdAt: DateTime.parse(json['created_at'] as String),
      );

  String get categoryIcon => MemoryCategory.icon(category);
  String get categoryLabel => MemoryCategory.label(category);
}

/// Memory category metadata — mirrors backend CATEGORY_CONFIG
class MemoryCategory {
  static const _config = {
    'dietary':    {'icon': '🚫', 'label': 'Chế độ ăn / Dị ứng'},
    'preference': {'icon': '✅', 'label': 'Sở thích'},
    'aversion':   {'icon': '❌', 'label': 'Không thích'},
    'goal':       {'icon': '🎯', 'label': 'Mục tiêu'},
    'constraint': {'icon': '⏰', 'label': 'Hạn chế'},
    'context':    {'icon': '📝', 'label': 'Thông tin khác'},
  };

  static String icon(String category) =>
      _config[category]?['icon'] ?? '💬';

  static String label(String category) =>
      _config[category]?['label'] ?? category;

  static List<String> get all => _config.keys.toList();
}
