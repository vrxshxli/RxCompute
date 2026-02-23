import 'user_medication_model.dart';

class HomeSummaryModel {
  final int todaysMedications;
  final UserMedicationModel? refillAlert;
  final double monthlyTotalSpend;
  final int monthlyOrderCount;
  final int activeOrderCount;

  const HomeSummaryModel({
    required this.todaysMedications,
    this.refillAlert,
    required this.monthlyTotalSpend,
    required this.monthlyOrderCount,
    required this.activeOrderCount,
  });

  factory HomeSummaryModel.fromJson(Map<String, dynamic> json) =>
      HomeSummaryModel(
        todaysMedications: json['todays_medications'] ?? 0,
        refillAlert: json['refill_alert'] != null
            ? UserMedicationModel.fromJson(json['refill_alert'])
            : null,
        monthlyTotalSpend: (json['monthly_total_spend'] as num?)?.toDouble() ?? 0,
        monthlyOrderCount: json['monthly_order_count'] ?? 0,
        activeOrderCount: json['active_order_count'] ?? 0,
      );
}
