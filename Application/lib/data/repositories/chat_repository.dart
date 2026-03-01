import 'package:dio/dio.dart';
import '../../config/api_config.dart';
import '../providers/api_provider.dart';

class ChatRepository {
  final ApiProvider _api = ApiProvider();

  Future<String> uploadPrescription(String filePath) async {
    final fileName = filePath.split('\\').last.split('/').last;
    final form = FormData.fromMap({
      'file': await MultipartFile.fromFile(filePath, filename: fileName),
    });
    final res = await _api.dio.post(ApiConfig.chatUploadPrescription, data: form);
    return res.data['file_url'] as String;
  }

  Future<Map<String, dynamic>> assistMessage({
    required String message,
    required String languageCode,
    required String stage,
    String? currentMedicine,
    List<String> candidateMedicines = const [],
  }) async {
    final payload = <String, dynamic>{
      'message': message,
      'language_code': languageCode,
      'stage': stage,
      if (currentMedicine != null && currentMedicine.trim().isNotEmpty) 'current_medicine': currentMedicine.trim(),
      'candidate_medicines': candidateMedicines,
    };
    final res = await _api.dio.post(ApiConfig.chatAssistant, data: payload);
    if (res.data is Map<String, dynamic>) {
      return Map<String, dynamic>.from(res.data as Map<String, dynamic>);
    }
    if (res.data is Map) {
      return Map<String, dynamic>.from((res.data as Map).map((k, v) => MapEntry(k.toString(), v)));
    }
    return const <String, dynamic>{};
  }
}
