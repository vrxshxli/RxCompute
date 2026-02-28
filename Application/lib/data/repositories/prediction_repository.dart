import '../providers/api_provider.dart';
import '../../config/api_config.dart';

class PredictionRepository {
  final ApiProvider _api = ApiProvider();

  Future<Map<String, dynamic>> getRefillCandidates({int? targetUserId}) async {
    final res = await _api.dio.get(
      '${ApiConfig.predictions}/refill/candidates',
      queryParameters: {
        if (targetUserId != null) 'target_user_id': targetUserId,
      },
    );
    return Map<String, dynamic>.from(res.data as Map);
  }

  Future<Map<String, dynamic>> confirmRefill({
    int? medicationId,
    int? medicineId,
    String? medicineName,
    required int quantityUnits,
    required String confirmationSource,
    String paymentMethod = 'online',
    String? prescriptionFile,
  }) async {
    final res = await _api.dio.post(
      '${ApiConfig.predictions}/refill/confirm',
      data: {
        if (medicationId != null) 'medication_id': medicationId,
        if (medicineId != null) 'medicine_id': medicineId,
        if (medicineName != null && medicineName.trim().isNotEmpty) 'medicine_name': medicineName.trim(),
        'quantity_units': quantityUnits,
        'confirmation_checked': true,
        'confirmation_source': confirmationSource,
        'payment_method': paymentMethod,
        if (prescriptionFile != null && prescriptionFile.trim().isNotEmpty) 'prescription_file': prescriptionFile.trim(),
      },
    );
    return Map<String, dynamic>.from(res.data as Map);
  }
}

