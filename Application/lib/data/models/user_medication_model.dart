class UserMedicationModel {
  final int id;
  final int? medicineId;
  final String name;
  final String dosageInstruction;
  final int frequencyPerDay;
  final int quantityUnits;
  final int daysLeft;
  final bool rxRequired;

  const UserMedicationModel({
    required this.id,
    this.medicineId,
    required this.name,
    required this.dosageInstruction,
    required this.frequencyPerDay,
    required this.quantityUnits,
    required this.daysLeft,
    required this.rxRequired,
  });

  factory UserMedicationModel.fromJson(Map<String, dynamic> json) =>
      UserMedicationModel(
        id: json['id'],
        medicineId: json['medicine_id'],
        name: json['name'],
        dosageInstruction: json['dosage_instruction'],
        frequencyPerDay: json['frequency_per_day'] ?? 1,
        quantityUnits: json['quantity_units'] ?? 0,
        daysLeft: json['days_left'] ?? 0,
        rxRequired: json['rx_required'] ?? false,
      );
}
