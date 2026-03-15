import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/network/api_service.dart';
import '../data/persona_repository.dart';
import '../data/persona_form_data.dart';
import 'persona_model.dart';

class PersonaState {
  final List<PersonaModel> personas;
  final PersonaModel? activePersona;
  final bool isLoading;
  final String? error;

  const PersonaState({
    this.personas = const [],
    this.activePersona,
    this.isLoading = false,
    this.error,
  });

  PersonaState copyWith({
    List<PersonaModel>? personas,
    PersonaModel? activePersona,
    bool? isLoading,
    String? error,
  }) =>
      PersonaState(
        personas: personas ?? this.personas,
        activePersona: activePersona ?? this.activePersona,
        isLoading: isLoading ?? this.isLoading,
        error: error,
      );
}

class PersonaNotifier extends StateNotifier<PersonaState> {
  PersonaNotifier(this._repo) : super(const PersonaState()) {
    _loadFromStorage();
  }

  final PersonaRepository _repo;
  final _storage = const FlutterSecureStorage();

  /// On init: read persona id from secure storage for instant UI (no network wait)
  Future<void> _loadFromStorage() async {
    final storedId = await _storage.read(key: AppConstants.activePersonaKey);
    // We don't have the full PersonaModel yet — just set a minimal placeholder
    // with the stored ID so chip shows something while network loads
    if (storedId != null) {
      state = state.copyWith(
        activePersona: PersonaModel(
          id: storedId,
          name: storedId,
          description: '',
          icon: '👨‍🍳',
          color: '#6B7280',
        ),
      );
    }
    // Background fetch full list
    await loadPersonas();
  }

  Future<void> loadPersonas() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final personas = await _repo.fetchAll();
      // Find which one is active
      final storedId = await _storage.read(key: AppConstants.activePersonaKey);
      PersonaModel? active;
      if (storedId != null) {
        try {
          active = personas.firstWhere((p) => p.id == storedId);
        } catch (_) {}
      }
      active ??= personas.where((p) => p.isDefault).firstOrNull ?? personas.firstOrNull;

      state = state.copyWith(
        personas: personas,
        activePersona: active,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: ApiService.parseError(e));
    }
  }

  Future<PersonaModel?> createPersona(PersonaFormData data) async {
    try {
      final created = await _repo.createPersona(data);
      state = state.copyWith(personas: [...state.personas, created]);
      return created;
    } catch (e) {
      state = state.copyWith(error: ApiService.parseError(e));
      return null;
    }
  }

  Future<bool> updatePersona(String personaId, PersonaFormData data) async {
    try {
      final updated = await _repo.updatePersona(personaId, data);
      state = state.copyWith(
        personas: state.personas
            .map((p) => p.id == personaId ? updated : p)
            .toList(),
        activePersona: state.activePersona?.id == personaId
            ? updated
            : state.activePersona,
      );
      return true;
    } catch (e) {
      state = state.copyWith(error: ApiService.parseError(e));
      return false;
    }
  }

  Future<bool> deletePersona(String personaId) async {
    final prev = state.personas;
    state = state.copyWith(
      personas: prev.where((p) => p.id != personaId).toList(),
    );
    try {
      await _repo.deletePersona(personaId);
      // If deleted the active persona, switch to default
      if (state.activePersona?.id == personaId) {
        final fallback = state.personas.where((p) => p.isDefault).firstOrNull
            ?? state.personas.firstOrNull;
        if (fallback != null) await setPersona(fallback);
      }
      return true;
    } catch (e) {
      state = state.copyWith(personas: prev, error: ApiService.parseError(e));
      return false;
    }
  }

  Future<void> setPersona(PersonaModel persona) async {
    final previous = state.activePersona;
    // Optimistic update
    state = state.copyWith(activePersona: persona, error: null);
    try {
      await _repo.setActive(persona.id);
      await _storage.write(
        key: AppConstants.activePersonaKey,
        value: persona.id,
      );
    } catch (e) {
      // Rollback on error
      state = state.copyWith(
        activePersona: previous,
        error: ApiService.parseError(e),
      );
    }
  }
}

final personaRepositoryProvider = Provider<PersonaRepository>((ref) {
  return PersonaRepository(ref.read(apiServiceProvider));
});

final personaProvider = StateNotifierProvider<PersonaNotifier, PersonaState>((ref) {
  return PersonaNotifier(ref.read(personaRepositoryProvider));
});
