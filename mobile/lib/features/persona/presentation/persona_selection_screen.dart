import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';
import '../../auth/domain/auth_state.dart';
import '../domain/persona_model.dart';
import '../domain/persona_state.dart';
import 'persona_form_screen.dart';

/// Full-screen persona selection page (accessible from Profile screen)
class PersonaSelectionScreen extends ConsumerWidget {
  const PersonaSelectionScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Chọn nhân vật AI'),
        centerTitle: true,
      ),
      body: PersonaGridContent(
        scrollController: ScrollController(),
        onSelected: () => Navigator.of(context).pop(),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _openForm(context),
        icon: const Icon(Icons.add),
        label: const Text('Tạo mới'),
      ),
    );
  }

  void _openForm(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => const PersonaFormScreen(),
      ),
    );
  }
}

/// Reusable grid widget — used both in full screen and bottom sheet
class PersonaGridContent extends ConsumerStatefulWidget {
  const PersonaGridContent({
    super.key,
    required this.scrollController,
    required this.onSelected,
  });

  final ScrollController scrollController;
  final VoidCallback onSelected;

  @override
  ConsumerState<PersonaGridContent> createState() => _PersonaGridContentState();
}

class _PersonaGridContentState extends ConsumerState<PersonaGridContent> {
  PersonaModel? _pending;

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(personaProvider);
    final currentUserId = ref.watch(authProvider).user?.id ?? '';
    final active = state.activePersona ?? PersonaModel.defaultPersona;

    return Column(
      children: [
        // Handle bar
        Center(
          child: Container(
            margin: const EdgeInsets.only(top: 12, bottom: 4),
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: Colors.grey[300],
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 8, 8),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  'Chọn hoặc tạo nhân vật AI cho riêng bạn',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                ),
              ),
              TextButton.icon(
                onPressed: () => _createPersona(context),
                icon: const Icon(Icons.add, size: 18),
                label: const Text('Tạo mới'),
              ),
            ],
          ),
        ),
        Expanded(
          child: state.isLoading && state.personas.isEmpty
              ? const Center(child: CircularProgressIndicator())
              : GridView.builder(
                  controller: widget.scrollController,
                  padding: const EdgeInsets.fromLTRB(12, 4, 12, 100),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    childAspectRatio: 0.82,
                    mainAxisSpacing: 12,
                    crossAxisSpacing: 12,
                  ),
                  itemCount: state.personas.isEmpty ? 1 : state.personas.length,
                  itemBuilder: (context, i) {
                    final persona = state.personas.isEmpty
                        ? PersonaModel.defaultPersona
                        : state.personas[i];
                    final isActive = (_pending ?? active).id == persona.id;
                    final canEdit = persona.canEdit(currentUserId);
                    return _PersonaCard(
                      persona: persona,
                      isActive: isActive,
                      canEdit: canEdit,
                      onTap: () => setState(() => _pending = persona),
                      onEdit: canEdit ? () => _editPersona(context, persona) : null,
                      onDelete: canEdit
                          ? () => _confirmDelete(context, persona)
                          : null,
                    );
                  },
                ),
        ),
        // Apply button
        SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
            child: SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _pending == null || _pending!.id == active.id
                    ? null
                    : () async {
                        await ref
                            .read(personaProvider.notifier)
                            .setPersona(_pending!);
                        widget.onSelected();
                      },
                child: const Text('Áp dụng'),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Future<void> _createPersona(BuildContext context) async {
    final result = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => const PersonaFormScreen()),
    );
    if (result == true && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Đã tạo nhân vật mới!')),
      );
    }
  }

  Future<void> _editPersona(BuildContext context, PersonaModel persona) async {
    final result = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => PersonaFormScreen(existing: persona),
      ),
    );
    if (result == true && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Đã cập nhật nhân vật!')),
      );
    }
  }

  void _confirmDelete(BuildContext context, PersonaModel persona) {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Xóa ${persona.name}?'),
        content: const Text('Thao tác này không thể hoàn tác.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Huỷ'),
          ),
          TextButton(
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
            onPressed: () async {
              Navigator.pop(ctx);
              await ref
                  .read(personaProvider.notifier)
                  .deletePersona(persona.id);
            },
            child: const Text('Xóa'),
          ),
        ],
      ),
    );
  }
}

// ── Persona card ──────────────────────────────────────────────────────────────

class _PersonaCard extends StatelessWidget {
  const _PersonaCard({
    required this.persona,
    required this.isActive,
    required this.canEdit,
    required this.onTap,
    this.onEdit,
    this.onDelete,
  });

  final PersonaModel persona;
  final bool isActive;
  final bool canEdit;
  final VoidCallback onTap;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;

  @override
  Widget build(BuildContext context) {
    final borderColor = Color(persona.colorValue);
    final theme = Theme.of(context);

    return GestureDetector(
      onTap: onTap,
      onLongPress: canEdit
          ? () => _showEditMenu(context)
          : null,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isActive ? borderColor : Colors.grey.shade200,
            width: isActive ? 2.5 : 1,
          ),
          color: isActive
              ? Color(persona.colorValue).withValues(alpha: 0.06)
              : theme.cardColor,
          boxShadow: isActive
              ? [
                  BoxShadow(
                    color: borderColor.withValues(alpha: 0.2),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ]
              : null,
        ),
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Icon + edit badge
            Stack(
              alignment: Alignment.topRight,
              children: [
                Padding(
                  padding: const EdgeInsets.all(4),
                  child: Text(persona.icon,
                      style: const TextStyle(fontSize: 38),),
                ),
                if (canEdit)
                  Container(
                    padding: const EdgeInsets.all(2),
                    decoration: const BoxDecoration(
                      color: AppColors.primary,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.edit, size: 10, color: Colors.white,),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              persona.name,
              textAlign: TextAlign.center,
              style: theme.textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.w700,
                color: isActive ? borderColor : null,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              persona.description,
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: theme.textTheme.bodySmall?.copyWith(
                color: Colors.grey[600],
                height: 1.3,
              ),
            ),
            if (!persona.isSystem) ...[
              const SizedBox(height: 4),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: AppColors.primaryLight.withValues(alpha: 0.4),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Text(
                  'Tùy chỉnh',
                  style: TextStyle(fontSize: 10, color: AppColors.primary),
                ),
              ),
            ],
            if (isActive) ...[
              const SizedBox(height: 6),
              Icon(Icons.check_circle, color: borderColor, size: 18,),
            ],
          ],
        ),
      ),
    );
  }

  void _showEditMenu(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.edit_outlined),
              title: const Text('Chỉnh sửa'),
              onTap: () {
                Navigator.pop(context);
                onEdit?.call();
              },
            ),
            ListTile(
              leading: const Icon(Icons.delete_outline, color: AppColors.error,),
              title: const Text('Xóa', style: TextStyle(color: AppColors.error),),
              onTap: () {
                Navigator.pop(context);
                onDelete?.call();
              },
            ),
          ],
        ),
      ),
    );
  }
}
