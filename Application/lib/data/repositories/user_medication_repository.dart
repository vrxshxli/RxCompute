import '../../config/api_config.dart';
import '../models/user_medication_model.dart';
import '../providers/api_provider.dart';

class UserMedicationRepository {
  final ApiProvider _api = ApiProvider();

  Future<List<UserMedicationModel>> getUserMedications() async {
    final res = await _api.dio.get('${ApiConfig.userMedications}/');
    return (res.data as List).map((e) => UserMedicationModel.fromJson(e)).toList();
  }

  Future<UserMedicationModel> addMedication({
    int? medicineId,
    String? customName,
    required String dosageInstruction,
    required int frequencyPerDay,
    required int quantityUnits,
  }) async {
    final res = await _api.dio.post(
      '${ApiConfig.userMedications}/',
      data: {
        if (medicineId != null) 'medicine_id': medicineId,
        if (customName != null && customName.trim().isNotEmpty) 'custom_name': customName.trim(),
        'dosage_instruction': dosageInstruction,
        'frequency_per_day': frequencyPerDay,
        'quantity_units': quantityUnits,
      },
    );
    return UserMedicationModel.fromJson(res.data);
  }
}
