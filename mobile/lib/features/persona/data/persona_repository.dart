import '../../../core/network/api_service.dart';
import '../domain/persona_model.dart';
import 'persona_form_data.dart';

class PersonaRepository {
  const PersonaRepository(this._api);
  final ApiService _api;

  Future<List<PersonaModel>> fetchAll() async {
    final data = await _api.getPersonas();
    return data.map(PersonaModel.fromJson).toList();
  }

  Future<PersonaModel> fetchActive() async {
    final data = await _api.getActivePersona();
    final personaData = data['persona'] as Map<String, dynamic>;
    return PersonaModel.fromJson(personaData);
  }

  Future<void> setActive(String personaId) async {
    await _api.setActivePersona(personaId);
  }

  Future<PersonaModel> createPersona(PersonaFormData data) async {
    final res = await _api.createPersona(data.toJson());
    return PersonaModel.fromJson(res);
  }

  Future<PersonaModel> updatePersona(String personaId, PersonaFormData data) async {
    final res = await _api.updatePersona(personaId, data.toJson());
    return PersonaModel.fromJson(res);
  }

  Future<void> deletePersona(String personaId) async {
    await _api.deletePersona(personaId);
  }
}
