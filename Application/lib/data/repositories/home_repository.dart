import '../../config/api_config.dart';
import '../models/home_summary_model.dart';
import '../providers/api_provider.dart';

class HomeRepository {
  final ApiProvider _api = ApiProvider();

  Future<HomeSummaryModel> getSummary() async {
    final res = await _api.dio.get(ApiConfig.homeSummary);
    return HomeSummaryModel.fromJson(res.data);
  }
}
