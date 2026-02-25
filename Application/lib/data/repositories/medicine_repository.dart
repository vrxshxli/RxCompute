import '../providers/api_provider.dart';
import '../models/medicine_model.dart';
import '../../config/api_config.dart';

class MedicineRepository {
  final ApiProvider _api = ApiProvider();

  Future<List<MedicineModel>> getMedicines({String? search}) async {
    final params = <String, dynamic>{};
    if (search != null && search.isNotEmpty) params['search'] = search;

    final res = await _api.dio.get('${ApiConfig.medicines}/', queryParameters: params);
    return (res.data as List)
        .map((e) => MedicineModel.fromJson(e))
        .toList();
  }

  Future<MedicineModel> getMedicine(int id) async {
    final res = await _api.dio.get('${ApiConfig.medicines}/$id');
    return MedicineModel.fromJson(res.data);
  }
}
