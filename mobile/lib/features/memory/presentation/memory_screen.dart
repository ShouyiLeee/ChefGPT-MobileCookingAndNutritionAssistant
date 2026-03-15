import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';
import '../domain/memory_model.dart';
import '../domain/memory_state.dart';

class MemoryScreen extends ConsumerStatefulWidget {
  const MemoryScreen({super.key});

  @override
  ConsumerState<MemoryScreen> createState() => _MemoryScreenState();
}

class _MemoryScreenState extends ConsumerState<MemoryScreen> {
  bool _showContextPreview = false;

  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(memoryProvider.notifier).load());
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(memoryProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Bộ nhớ AI'),
        actions: [
          if (state.memories.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_sweep_outlined),
              tooltip: 'Xóa tất cả',
              onPressed: () => _confirmClearAll(context),
            ),
        ],
      ),
      body: state.isLoading
          ? const Center(child: CircularProgressIndicator())
          : state.memories.isEmpty
              ? _EmptyMemory(onAdd: () => _showAddSheet(context))
              : _buildMemoryList(context, state),
      floatingActionButton: state.memories.isNotEmpty
          ? FloatingActionButton(
              mini: true,
              tooltip: 'Thêm thông tin',
              onPressed: () => _showAddSheet(context),
              child: const Icon(Icons.add),
            )
          : null,
    );
  }

  Widget _buildMemoryList(BuildContext context, MemoryState state) {
    final grouped = state.grouped;
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 100),
      children: [
        // Info banner
        _InfoBanner(
          memoryCount: state.memories.length,
          onAddTap: () => _showAddSheet(context),
        ),
        const SizedBox(height: 12),

        // Grouped entries by category
        for (final entry in grouped.entries) ...[
          _CategorySection(
            category: entry.key,
            memories: entry.value,
          ),
          const SizedBox(height: 8),
        ],

        // Context preview collapsible card
        if (state.contextPreview.isNotEmpty) ...[
          const SizedBox(height: 8),
          _ContextPreviewCard(
            preview: state.contextPreview,
            isExpanded: _showContextPreview,
            onToggle: () => setState(() => _showContextPreview = !_showContextPreview),
          ),
        ],
        const SizedBox(height: 24),
      ],
    );
  }

  void _confirmClearAll(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Xóa toàn bộ bộ nhớ?'),
        content: const Text(
          'ChefGPT sẽ quên tất cả thông tin đã biết về bạn.\nHành động này không thể hoàn tác.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Huỷ'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(ctx);
              final count = await ref.read(memoryProvider.notifier).clearAll();
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Đã xóa $count thông tin')),
                );
              }
            },
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
            child: const Text('Xóa tất cả'),
          ),
        ],
      ),
    );
  }

  void _showAddSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const _AddMemorySheet(),
    );
  }
}

// ── Info banner ────────────────────────────────────────────────────────────

class _InfoBanner extends StatelessWidget {
  final int memoryCount;
  final VoidCallback onAddTap;
  const _InfoBanner({required this.memoryCount, required this.onAddTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppColors.primary.withValues(alpha: 0.08),
            AppColors.primary.withValues(alpha: 0.04),
          ],
        ),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.primary.withValues(alpha: 0.15)),
      ),
      child: Row(
        children: [
          const Text('🧠', style: TextStyle(fontSize: 28)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'AI đã biết $memoryCount điều về bạn',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w700,
                        color: AppColors.primary,
                      ),
                ),
                const SizedBox(height: 2),
                Text(
                  'Thông tin này được inject vào mỗi lượt gợi ý để cá nhân hoá kết quả.',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.textSecondary,
                        height: 1.4,
                      ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Empty state ────────────────────────────────────────────────────────────

class _EmptyMemory extends StatelessWidget {
  final VoidCallback onAdd;
  const _EmptyMemory({required this.onAdd});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text('🧠', style: TextStyle(fontSize: 72)),
          const SizedBox(height: 20),
          Text(
            'ChefGPT chưa biết gì về bạn',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 10),
          Text(
            'Hãy chat tự nhiên — ChefGPT sẽ tự học dị ứng, sở thích, và mục tiêu của bạn qua mỗi cuộc trò chuyện.\n\nBạn cũng có thể thêm thủ công bên dưới.',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppColors.textSecondary,
                  height: 1.5,
                ),
          ),
          const SizedBox(height: 28),
          FilledButton.icon(
            onPressed: onAdd,
            icon: const Icon(Icons.add),
            label: const Text('Thêm thông tin thủ công'),
          ),
        ],
      ),
    );
  }
}

// ── Category section ───────────────────────────────────────────────────────

class _CategorySection extends ConsumerWidget {
  final String category;
  final List<MemoryModel> memories;
  const _CategorySection({required this.category, required this.memories});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Category header
        Padding(
          padding: const EdgeInsets.only(bottom: 6),
          child: Row(
            children: [
              Text(
                MemoryCategory.icon(category),
                style: const TextStyle(fontSize: 15),
              ),
              const SizedBox(width: 6),
              Text(
                MemoryCategory.label(category),
                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      color: AppColors.textSecondary,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.3,
                    ),
              ),
              const SizedBox(width: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                decoration: BoxDecoration(
                  color: AppColors.primaryLight.withValues(alpha: 0.4),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '${memories.length}',
                  style: const TextStyle(
                    fontSize: 11,
                    color: AppColors.primary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
        ),
        // Memory cards
        Container(
          decoration: BoxDecoration(
            color: Theme.of(context).cardColor,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: Column(
            children: [
              for (int i = 0; i < memories.length; i++) ...[
                _MemoryTile(memory: memories[i]),
                if (i < memories.length - 1)
                  Divider(height: 1, indent: 16, endIndent: 16, color: Colors.grey.shade100),
              ],
            ],
          ),
        ),
      ],
    );
  }
}

// ── Memory tile ────────────────────────────────────────────────────────────

class _MemoryTile extends ConsumerWidget {
  final MemoryModel memory;
  const _MemoryTile({required this.memory});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Source is the original chat message text when auto-extracted,
    // or 'manual' / empty when added manually.
    final isAutoLearned = memory.source.length > 10 &&
        memory.source != 'manual' &&
        memory.source != 'explicit';

    return Dismissible(
      key: ValueKey(memory.id),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        decoration: BoxDecoration(
          color: AppColors.error,
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Icon(Icons.delete_outline, color: Colors.white),
      ),
      onDismissed: (_) => ref.read(memoryProvider.notifier).deleteMemory(memory.id),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Key label chip
                  Container(
                    margin: const EdgeInsets.only(bottom: 4),
                    padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade100,
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      _keyLabel(memory.category, memory.key),
                      style: Theme.of(context).textTheme.labelSmall?.copyWith(
                            color: AppColors.textSecondary,
                            fontWeight: FontWeight.w600,
                          ),
                    ),
                  ),
                  // Value
                  Text(
                    memory.value,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.w500,
                        ),
                  ),
                  const SizedBox(height: 4),
                  // Source badge
                  if (isAutoLearned)
                    Row(
                      children: [
                        const Icon(Icons.auto_awesome, size: 11, color: AppColors.primary),
                        const SizedBox(width: 3),
                        Text(
                          'Học từ chat',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: AppColors.primary,
                                fontSize: 11,
                              ),
                        ),
                        if (memory.confidence < 0.9) ...[
                          const SizedBox(width: 6),
                          _ConfidenceDots(confidence: memory.confidence),
                        ],
                      ],
                    )
                  else
                    Row(
                      children: [
                        Icon(Icons.edit_outlined, size: 11, color: Colors.grey.shade500),
                        const SizedBox(width: 3),
                        Text(
                          'Thêm thủ công',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: Colors.grey.shade500,
                                fontSize: 11,
                              ),
                        ),
                      ],
                    ),
                ],
              ),
            ),
            // Delete button
            IconButton(
              icon: const Icon(Icons.close, size: 18, color: AppColors.textSecondary),
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
              onPressed: () => ref.read(memoryProvider.notifier).deleteMemory(memory.id),
            ),
          ],
        ),
      ),
    );
  }

  static const _keyLabels = {
    'allergy': 'Dị ứng',
    'diet_type': 'Chế độ ăn',
    'favorite_cuisine': 'Ẩm thực yêu thích',
    'disliked_ingredient': 'Nguyên liệu ghét',
    'disliked_flavor': 'Hương vị ghét',
    'nutrition_goal': 'Mục tiêu dinh dưỡng',
    'weight_target': 'Mục tiêu cân nặng',
    'cooking_time': 'Thời gian nấu',
    'budget': 'Ngân sách',
    'equipment': 'Thiết bị',
    'cooking_skill': 'Kỹ năng nấu',
    'household_size': 'Số người gia đình',
    'meal_frequency': 'Tần suất ăn',
    'health_condition': 'Tình trạng sức khoẻ',
    'lifestyle': 'Lối sống',
    'other': 'Khác',
    'flavor': 'Hương vị',
    'spice_level': 'Độ cay',
  };

  String _keyLabel(String category, String key) =>
      _keyLabels[key] ?? key.replaceAll('_', ' ');
}

// ── Confidence dots ────────────────────────────────────────────────────────

class _ConfidenceDots extends StatelessWidget {
  final double confidence;
  const _ConfidenceDots({required this.confidence});

  @override
  Widget build(BuildContext context) {
    final filled = (confidence * 3).round().clamp(1, 3);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(3, (i) => Container(
        width: 5,
        height: 5,
        margin: const EdgeInsets.only(right: 2),
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: i < filled
              ? AppColors.primary.withValues(alpha: 0.6)
              : Colors.grey.shade300,
        ),
      ),),
    );
  }
}

// ── Context preview card ───────────────────────────────────────────────────

class _ContextPreviewCard extends StatelessWidget {
  final String preview;
  final bool isExpanded;
  final VoidCallback onToggle;

  const _ContextPreviewCard({
    required this.preview,
    required this.isExpanded,
    required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header — tap to toggle
          InkWell(
            onTap: onToggle,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Row(
                children: [
                  const Icon(Icons.visibility_outlined, size: 18, color: AppColors.textSecondary),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Xem những gì AI biết về bạn',
                      style: Theme.of(context).textTheme.labelLarge?.copyWith(
                            color: AppColors.textSecondary,
                            fontWeight: FontWeight.w600,
                          ),
                    ),
                  ),
                  Icon(
                    isExpanded ? Icons.expand_less : Icons.expand_more,
                    color: AppColors.textSecondary,
                    size: 20,
                  ),
                ],
              ),
            ),
          ),
          // Preview text
          if (isExpanded) ...[
            const Divider(height: 1),
            Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Đoạn text này được inject vào system prompt của AI trước mỗi câu trả lời:',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppColors.textSecondary,
                          fontStyle: FontStyle.italic,
                        ),
                  ),
                  const SizedBox(height: 10),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.grey.shade200),
                    ),
                    child: Text(
                      preview,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            fontFamily: 'monospace',
                            height: 1.6,
                            color: AppColors.textPrimary,
                          ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

// ── Add memory sheet ───────────────────────────────────────────────────────

class _AddMemorySheet extends ConsumerStatefulWidget {
  const _AddMemorySheet();

  @override
  ConsumerState<_AddMemorySheet> createState() => _AddMemorySheetState();
}

class _AddMemorySheetState extends ConsumerState<_AddMemorySheet> {
  String _selectedCategory = 'dietary';
  String _selectedKey = 'allergy';
  final _valueCtrl = TextEditingController();
  bool _saving = false;

  static const _categoryOptions = [
    ('dietary', '🚫', 'Chế độ ăn / Dị ứng'),
    ('preference', '✅', 'Sở thích'),
    ('aversion', '❌', 'Không thích'),
    ('goal', '🎯', 'Mục tiêu'),
    ('constraint', '⏰', 'Hạn chế'),
    ('context', '📝', 'Thông tin khác'),
  ];

  static const _keyOptions = <String, List<(String, String)>>{
    'dietary': [
      ('allergy', 'Dị ứng (tôm, đậu phộng, sữa...)'),
      ('diet_type', 'Chế độ ăn (chay, keto, eat clean...)'),
      ('health_condition', 'Tình trạng sức khoẻ (tiểu đường, ...)'),
    ],
    'preference': [
      ('favorite_cuisine', 'Ẩm thực yêu thích'),
      ('flavor', 'Hương vị thích'),
      ('spice_level', 'Độ cay'),
      ('other', 'Khác'),
    ],
    'aversion': [
      ('disliked_ingredient', 'Nguyên liệu ghét'),
      ('disliked_flavor', 'Hương vị ghét'),
      ('other', 'Khác'),
    ],
    'goal': [
      ('nutrition_goal', 'Mục tiêu dinh dưỡng'),
      ('weight_target', 'Mục tiêu cân nặng'),
      ('other', 'Khác'),
    ],
    'constraint': [
      ('cooking_time', 'Thời gian nấu tối đa'),
      ('budget', 'Ngân sách'),
      ('equipment', 'Thiết bị có sẵn'),
      ('meal_frequency', 'Số bữa / ngày'),
    ],
    'context': [
      ('cooking_skill', 'Kỹ năng nấu ăn'),
      ('household_size', 'Số người trong gia đình'),
      ('lifestyle', 'Lối sống'),
      ('other', 'Khác'),
    ],
  };

  static const _hints = {
    'allergy': 'VD: tôm, đậu phộng, hải sản, sữa',
    'diet_type': 'VD: ăn chay, keto, gluten-free',
    'health_condition': 'VD: tiểu đường type 2, tăng huyết áp',
    'favorite_cuisine': 'VD: Việt Nam, Nhật, Ý',
    'flavor': 'VD: thích chua cay, không thích ngọt',
    'spice_level': 'VD: ăn được cay vừa, không ăn được cay',
    'disliked_ingredient': 'VD: rau mùi, cà tím, gan',
    'nutrition_goal': 'VD: tăng protein, giảm carb',
    'weight_target': 'VD: giảm 5kg trong 3 tháng',
    'cooking_time': 'VD: tối đa 30 phút mỗi bữa',
    'budget': 'VD: dưới 100k/ngày',
    'equipment': 'VD: không có lò nướng, có nồi chiên không dầu',
    'cooking_skill': 'VD: mới học nấu ăn, nấu ăn 5 năm',
    'household_size': 'VD: 2 người lớn + 1 trẻ em',
    'lifestyle': 'VD: tập gym 5 buổi/tuần, làm việc văn phòng',
  };

  @override
  void dispose() {
    _valueCtrl.dispose();
    super.dispose();
  }

  List<(String, String)> get _currentKeys =>
      _keyOptions[_selectedCategory] ?? [('other', 'Khác')];

  String get _hint => _hints[_selectedKey] ?? 'Nhập thông tin...';

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: Container(
        decoration: BoxDecoration(
          color: Theme.of(context).scaffoldBackgroundColor,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Handle bar
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: Colors.grey.shade300,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 14),
                Text(
                  'Thêm thông tin cho AI',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  'AI sẽ nhớ và áp dụng ngay vào các gợi ý tiếp theo.',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                ),
                const SizedBox(height: 16),
                // Category chips
                Text(
                  'Loại thông tin',
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                ),
                const SizedBox(height: 8),
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: _categoryOptions.map((cat) {
                      final selected = _selectedCategory == cat.$1;
                      return Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: FilterChip(
                          label: Text('${cat.$2} ${cat.$3}'),
                          selected: selected,
                          onSelected: (_) => setState(() {
                            _selectedCategory = cat.$1;
                            _selectedKey = _currentKeys.first.$1;
                            _valueCtrl.clear();
                          }),
                          selectedColor: AppColors.primary.withValues(alpha: 0.12),
                          checkmarkColor: AppColors.primary,
                          labelStyle: TextStyle(
                            fontSize: 12,
                            color: selected ? AppColors.primary : null,
                            fontWeight: selected ? FontWeight.w600 : null,
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ),
                const SizedBox(height: 14),
                // Key dropdown
                DropdownButtonFormField<String>(
                  initialValue: _selectedKey,
                  decoration: const InputDecoration(
                    labelText: 'Trường thông tin',
                    isDense: true,
                  ),
                  items: _currentKeys
                      .map((e) => DropdownMenuItem(
                            value: e.$1,
                            child: Text(e.$2, style: const TextStyle(fontSize: 14)),
                          ),)
                      .toList(),
                  onChanged: (v) => setState(() {
                    _selectedKey = v!;
                    _valueCtrl.clear();
                  }),
                ),
                const SizedBox(height: 12),
                // Value input
                TextField(
                  controller: _valueCtrl,
                  decoration: InputDecoration(
                    labelText: 'Giá trị',
                    hintText: _hint,
                    hintStyle: const TextStyle(fontSize: 13),
                  ),
                  autofocus: true,
                  textCapitalization: TextCapitalization.sentences,
                  textInputAction: TextInputAction.done,
                  onSubmitted: (_) => _save(),
                ),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    onPressed: _saving ? null : _save,
                    child: _saving
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('Lưu thông tin'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _save() async {
    final value = _valueCtrl.text.trim();
    if (value.isEmpty) return;
    setState(() => _saving = true);
    final ok = await ref.read(memoryProvider.notifier).addMemory(
          category: _selectedCategory,
          key: _selectedKey,
          value: value,
        );
    if (mounted) {
      Navigator.pop(context);
      if (ok) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Đã lưu! AI sẽ nhớ điều này.')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Không thể lưu — thông tin đã tồn tại.')),
        );
      }
    }
  }
}
