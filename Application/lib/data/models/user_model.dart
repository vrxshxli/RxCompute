class UserModel {
  final int id;
  final String? phone;
  final String? googleId;
  final String? name;
  final int? age;
  final String? gender;
  final String? email;
  final String? locationText;
  final double? locationLat;
  final double? locationLng;
  final String? pushToken;
  final String? profilePicture;
  final String? allergies;
  final String? conditions;
  final bool isVerified;
  final bool isRegistered;

  const UserModel({
    required this.id,
    this.phone,
    this.googleId,
    this.name,
    this.age,
    this.gender,
    this.email,
    this.locationText,
    this.locationLat,
    this.locationLng,
    this.pushToken,
    this.profilePicture,
    this.allergies,
    this.conditions,
    this.isVerified = false,
    this.isRegistered = false,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) => UserModel(
        id: json['id'],
        phone: json['phone'],
        googleId: json['google_id'],
        name: json['name'],
        age: json['age'],
        gender: json['gender'],
        email: json['email'],
        locationText: json['location_text'],
        locationLat: (json['location_lat'] as num?)?.toDouble(),
        locationLng: (json['location_lng'] as num?)?.toDouble(),
        pushToken: json['push_token'],
        profilePicture: json['profile_picture'],
        allergies: json['allergies'],
        conditions: json['conditions'],
        isVerified: json['is_verified'] ?? false,
        isRegistered: json['is_registered'] ?? false,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'phone': phone,
        'name': name,
        'age': age,
        'gender': gender,
        'email': email,
        'location_text': locationText,
        'location_lat': locationLat,
        'location_lng': locationLng,
        'allergies': allergies,
        'conditions': conditions,
      };

  String get initials {
    if (name == null || name!.isEmpty) return '??';
    final p = name!.split(' ');
    return p.length >= 2
        ? '${p[0][0].toUpperCase()}${p[1][0].toUpperCase()}'
        : name!.substring(0, 2).toUpperCase();
  }

  String get firstName => name?.split(' ').first ?? 'User';

  List<String> get allergyList =>
      allergies?.split(',').map((e) => e.trim()).where((e) => e.isNotEmpty).toList() ?? [];

  List<String> get conditionList =>
      conditions?.split(',').map((e) => e.trim()).where((e) => e.isNotEmpty).toList() ?? [];
}
