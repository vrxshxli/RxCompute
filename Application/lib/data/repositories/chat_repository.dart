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
}
