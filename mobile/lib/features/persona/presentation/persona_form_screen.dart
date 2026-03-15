import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';
import '../data/persona_form_data.dart';
import '../domain/persona_model.dart';
import '../domain/persona_state.dart';

/// Màn hình tạo mới hoặc chỉnh sửa một custom persona.
/// Truyền [existing] để vào chế độ edit, để null để tạo mới.
class PersonaFormScreen extends ConsumerStatefulWidget {
  final PersonaModel? existing;
  const PersonaFormScreen({super.key, this.existing});

  @override
  ConsumerState<PersonaFormScreen> createState() => _PersonaFormScreenState();
}

class _PersonaFormScreenState extends ConsumerState<PersonaFormScreen> {
  final _formKey = GlobalKey<FormState>();
  bool _saving = false;

  // Controllers
  late final TextEditingController _nameCtrl;
  late final TextEditingController _descCtrl;
  late final TextEditingController _iconCtrl;
  late final TextEditingController _systemPromptCtrl;
  late final TextEditingController _recipePrefixCtrl;
  late final TextEditingController _mealPlanPrefixCtrl;

  String _color = '#6B7280';
  bool _isPublic = true;
  final List<String> _quickActions = [];
  final _qaCtrl = TextEditingController();

  bool get _isEdit => widget.existing != null;

  static const _presetColors = [
    '#E8A020', '#3B82F6', '#10B981', '#22C55E',
    '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899',
    '#6B7280', '#0EA5E9',
  ];

  @override
  void initState() {
    super.initState();
    final e = widget.existing;
    _nameCtrl = TextEditingController(text: e?.name ?? '');
    _descCtrl = TextEditingController(text: e?.description ?? '');
    _iconCtrl = TextEditingController(text: e?.icon ?? '👨‍🍳');
    _systemPromptCtrl = TextEditingController(text: e?.systemPrompt ?? '');
    _recipePrefixCtrl = TextEditingController(text: e?.recipePrefix ?? '');
    _mealPlanPrefixCtrl = TextEditingController(text: e?.mealPlanPrefix ?? '');
    if (e != null) {
      _color = e.color;
      _isPublic = e.isPublic;
      _quickActions.addAll(e.quickActions);
    }
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _descCtrl.dispose();
    _iconCtrl.dispose();
    _systemPromptCtrl.dispose();
    _recipePrefixCtrl.dispose();
    _mealPlanPrefixCtrl.dispose();
    _qaCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_isEdit ? 'Chỉnh sửa nhân vật' : 'Tạo nhân vật mới'),
        actions: [
          TextButton(
            onPressed: _saving ? null : _submit,
            child: _saving
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2,),
                  )
                : const Text('Lưu'),
          ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // ── Preview card ──────────────────────────────────────────────
            _PreviewCard(
              icon: _iconCtrl.text,
              name: _nameCtrl.text.isEmpty ? 'Tên nhân vật' : _nameCtrl.text,
              description: _descCtrl.text.isEmpty
                  ? 'Mô tả ngắn...'
                  : _descCtrl.text,
              color: _color,
            ),
            const SizedBox(height: 20),

            // ── Basic info ────────────────────────────────────────────────
            _sectionLabel(context, 'Thông tin cơ bản'),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Icon input
                SizedBox(
                  width: 72,
                  child: TextFormField(
                    controller: _iconCtrl,
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontSize: 28),
                    decoration: const InputDecoration(labelText: 'Icon'),
                    maxLength: 4,
                    onChanged: (_) => setState(() {}),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextFormField(
                    controller: _nameCtrl,
                    decoration: const InputDecoration(labelText: 'Tên nhân vật *'),
                    validator: (v) =>
                        (v == null || v.trim().length < 2) ? 'Tối thiểu 2 ký tự' : null,
                    onChanged: (_) => setState(() {}),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _descCtrl,
              decoration: const InputDecoration(labelText: 'Mô tả ngắn'),
              maxLength: 200,
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 4),

            // ── Color picker ──────────────────────────────────────────────
            _sectionLabel(context, 'Màu sắc'),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _presetColors.map((hex) {
                final selected = hex == _color;
                final c = _hexToColor(hex);
                return GestureDetector(
                  onTap: () => setState(() => _color = hex),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 150),
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: c,
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: selected ? Colors.black : Colors.transparent,
                        width: 2.5,
                      ),
                      boxShadow: selected
                          ? [BoxShadow(color: c.withValues(alpha: 0.5), blurRadius: 6,)]
                          : null,
                    ),
                    child: selected
                        ? const Icon(Icons.check, color: Colors.white, size: 18,)
                        : null,
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 20),

            // ── Prompts ───────────────────────────────────────────────────
            _sectionLabel(context, 'Phong cách AI'),
            TextFormField(
              controller: _systemPromptCtrl,
              decoration: const InputDecoration(
                labelText: 'Hướng dẫn hệ thống',
                hintText: 'VD: Bạn là đầu bếp chuyên về ẩm thực miền Trung Việt Nam...',
                helperText: 'Inject vào mỗi lượt chat. Để trống = dùng mặc định.',
                helperMaxLines: 2,
              ),
              maxLines: 4,
              maxLength: 2000,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _recipePrefixCtrl,
              decoration: const InputDecoration(
                labelText: 'Phong cách gợi ý món ăn',
                hintText: 'VD: Ưu tiên các món truyền thống miền Trung...',
              ),
              maxLines: 2,
              maxLength: 1000,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _mealPlanPrefixCtrl,
              decoration: const InputDecoration(
                labelText: 'Phong cách lập thực đơn',
                hintText: 'VD: Cân bằng dinh dưỡng theo phong cách ẩm thực Huế...',
              ),
              maxLines: 2,
              maxLength: 1000,
            ),
            const SizedBox(height: 20),

            // ── Quick actions ─────────────────────────────────────────────
            _sectionLabel(context, 'Gợi ý nhanh (tối đa 6)'),
            ..._quickActions.asMap().entries.map((e) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.drag_handle, color: AppColors.textSecondary,),
                  title: Text(e.value, style: const TextStyle(fontSize: 14),),
                  trailing: IconButton(
                    icon: const Icon(Icons.close, size: 18,),
                    onPressed: () => setState(() => _quickActions.removeAt(e.key)),
                  ),
                ),),
            if (_quickActions.length < 6)
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _qaCtrl,
                      decoration: const InputDecoration(
                        hintText: 'Thêm gợi ý nhanh...',
                        isDense: true,
                      ),
                      textInputAction: TextInputAction.done,
                      onSubmitted: _addQuickAction,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.add_circle_outline,),
                    onPressed: () => _addQuickAction(_qaCtrl.text),
                  ),
                ],
              ),
            const SizedBox(height: 20),

            // ── Visibility ────────────────────────────────────────────────
            _sectionLabel(context, 'Chia sẻ'),
            SwitchListTile(
              value: _isPublic,
              contentPadding: EdgeInsets.zero,
              title: const Text('Công khai với mọi người'),
              subtitle: const Text(
                'Cho phép người dùng khác thấy và dùng nhân vật này.',
              ),
              onChanged: (v) => setState(() => _isPublic = v),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  void _addQuickAction(String text) {
    final trimmed = text.trim();
    if (trimmed.isEmpty || _quickActions.contains(trimmed)) return;
    setState(() {
      _quickActions.add(trimmed);
      _qaCtrl.clear();
    });
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);

    final data = PersonaFormData(
      name: _nameCtrl.text.trim(),
      description: _descCtrl.text.trim(),
      icon: _iconCtrl.text.trim().isEmpty ? '👨‍🍳' : _iconCtrl.text.trim(),
      color: _color,
      systemPrompt: _systemPromptCtrl.text.trim(),
      recipePrefix: _recipePrefixCtrl.text.trim(),
      mealPlanPrefix: _mealPlanPrefixCtrl.text.trim(),
      quickActions: List.of(_quickActions),
      isPublic: _isPublic,
    );

    bool ok;
    if (_isEdit) {
      ok = await ref
          .read(personaProvider.notifier)
          .updatePersona(widget.existing!.id, data);
    } else {
      final created =
          await ref.read(personaProvider.notifier).createPersona(data);
      ok = created != null;
    }

    if (mounted) {
      setState(() => _saving = false);
      if (ok) {
        Navigator.of(context).pop(true);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Có lỗi xảy ra, vui lòng thử lại.')),
        );
      }
    }
  }

  Color _hexToColor(String hex) {
    final h = hex.replaceAll('#', '');
    return Color(int.parse('FF$h', radix: 16));
  }
}

// ── Preview card ──────────────────────────────────────────────────────────────

class _PreviewCard extends StatelessWidget {
  final String icon;
  final String name;
  final String description;
  final String color;

  const _PreviewCard({
    required this.icon,
    required this.name,
    required this.description,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final c = Color(int.parse('FF${color.replaceAll('#', '')}', radix: 16));
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: Border.all(color: c, width: 2),
        borderRadius: BorderRadius.circular(16),
        color: c.withValues(alpha: 0.06),
      ),
      child: Row(
        children: [
          Text(icon, style: const TextStyle(fontSize: 40),),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: c,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  description,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

Widget _sectionLabel(BuildContext context, String text) => Padding(
      padding: const EdgeInsets.only(bottom: 8, top: 4),
      child: Text(
        text,
        style: Theme.of(context).textTheme.labelLarge?.copyWith(
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w600,
            ),
      ),
    );
