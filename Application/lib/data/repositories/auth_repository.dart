import '../providers/api_provider.dart';
import '../../config/api_config.dart';

class AuthRepository {
  final ApiProvider _api = ApiProvider();

  Future<String> sendOtp(String phone) async {
    final res = await _api.dio.post(ApiConfig.sendOtp, data: {'phone': phone});
    return res.data['mock_otp'];
  }

  Future<Map<String, dynamic>> verifyOtp(String phone, String otp) async {
    final res = await _api.dio.post(
      ApiConfig.verifyOtp,
      data: {'phone': phone, 'otp': otp},
    );
    final data = res.data;
    // Save token
    await _api.saveToken(data['access_token']);
    return data;
  }

  Future<Map<String, dynamic>> registerUser({
    required String name,
    required int age,
    required String gender,
    String? email,
    String? allergies,
    String? conditions,
  }) async {
    final res = await _api.dio.post(ApiConfig.register, data: {
      'name': name,
      'age': age,
      'gender': gender,
      if (email != null) 'email': email,
      if (allergies != null) 'allergies': allergies,
      if (conditions != null) 'conditions': conditions,
    });
    return res.data;
  }

  Future<void> logout() async {
    await _api.clearToken();
  }

  Future<bool> isLoggedIn() async {
    return await _api.hasToken();
  }
}
