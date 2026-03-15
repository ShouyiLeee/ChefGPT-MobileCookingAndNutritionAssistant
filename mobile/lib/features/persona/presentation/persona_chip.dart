import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/persona_model.dart';
import '../domain/persona_state.dart';
import 'persona_selection_screen.dart';

/// Small chip hiển thị persona đang active trên AppBar của chat screen.
/// Tap → mở bottom sheet chọn persona.
class PersonaChip extends ConsumerWidget {
  const PersonaChip({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final persona = ref.watch(personaProvider).activePersona ?? PersonaModel.defaultPersona;
    final colorValue = persona.colorValue;
    final borderColor = Color(colorValue);

    return GestureDetector(
      onTap: () => _showPersonaSheet(context, ref),
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          border: Border.all(color: borderColor, width: 1.5),
          borderRadius: BorderRadius.circular(20),
          color: borderColor.withValues(alpha: 0.08),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(persona.icon, style: const TextStyle(fontSize: 14)),
            const SizedBox(width: 4),
            Text(
              persona.name.split(' ').take(2).join(' '),
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: borderColor,
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showPersonaSheet(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        maxChildSize: 0.95,
        minChildSize: 0.5,
        builder: (_, scrollController) => Container(
          decoration: BoxDecoration(
            color: Theme.of(context).scaffoldBackgroundColor,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: PersonaGridContent(
            scrollController: scrollController,
            onSelected: () => Navigator.of(context).pop(),
          ),
        ),
      ),
    );
  }
}
