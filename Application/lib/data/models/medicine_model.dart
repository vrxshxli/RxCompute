class MedicineModel {
  final int id;
  final String name;
  final String pzn;
  final double price;
  final String? package;
  final int stock;
  final bool rxRequired;
  final String? description;
  int quantity;

  MedicineModel({
    required this.id,
    required this.name,
    required this.pzn,
    required this.price,
    this.package,
    required this.stock,
    this.rxRequired = false,
    this.description,
    this.quantity = 1,
  });

  factory MedicineModel.fromJson(Map<String, dynamic> json) => MedicineModel(
        id: json['id'],
        name: json['name'],
        pzn: json['pzn'],
        price: (json['price'] as num).toDouble(),
        package: json['package'],
        stock: json['stock'] ?? 0,
        rxRequired: json['rx_required'] ?? false,
        description: json['description'],
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'pzn': pzn,
        'price': price,
        'package': package,
        'stock': stock,
        'rx_required': rxRequired,
        'description': description,
      };

  String get formattedPrice => '€${price.toStringAsFixed(2)}';

  String get stockStatus =>
      stock == 0 ? 'out' : stock < 10 ? 'low' : 'ok';
}
