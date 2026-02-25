import '../providers/api_provider.dart';
import '../models/user_model.dart';
import '../../config/api_config.dart';

class UserRepository {
  final ApiProvider _api = ApiProvider();

  Future<UserModel> getProfile() async {
    final res = await _api.dio.get(ApiConfig.profile);
    return UserModel.fromJson(res.data);
  }

  Future<UserModel> updateProfile({
    String? name,
    int? age,
    String? gender,
    String? email,
    String? pushToken,
    String? allergies,
    String? conditions,
  }) async {
    final data = <String, dynamic>{};
    if (name != null) data['name'] = name;
    if (age != null) data['age'] = age;
    if (gender != null) data['gender'] = gender;
    if (email != null) data['email'] = email;
    if (pushToken != null) data['push_token'] = pushToken;
    if (allergies != null) data['allergies'] = allergies;
    if (conditions != null) data['conditions'] = conditions;

    final res = await _api.dio.put(ApiConfig.profile, data: data);
    return UserModel.fromJson(res.data);
  }
}
