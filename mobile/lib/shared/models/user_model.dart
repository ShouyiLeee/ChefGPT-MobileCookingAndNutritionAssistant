import 'package:json_annotation/json_annotation.dart';
import 'package:equatable/equatable.dart';

part 'user_model.g.dart';

@JsonSerializable()
class UserModel extends Equatable {
  final String id;
  final String email;
  final String? name;
  final String? avatarUrl;
  final DateTime createdAt;
  final DateTime? updatedAt;

  const UserModel({
    required this.id,
    required this.email,
    this.name,
    this.avatarUrl,
    required this.createdAt,
    this.updatedAt,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) => _$UserModelFromJson(json);
  Map<String, dynamic> toJson() => _$UserModelToJson(this);

  @override
  List<Object?> get props => [id, email, name, avatarUrl, createdAt, updatedAt];
}

@JsonSerializable()
class ProfileModel extends Equatable {
  final String userId;
  final int? age;
  final double? weight;
  final double? height;
  final String? dietaryPreference;
  final List<String>? allergies;
  final String? goal; // weight_loss, muscle_gain, maintenance
  final int? targetCalories;

  const ProfileModel({
    required this.userId,
    this.age,
    this.weight,
    this.height,
    this.dietaryPreference,
    this.allergies,
    this.goal,
    this.targetCalories,
  });

  factory ProfileModel.fromJson(Map<String, dynamic> json) => _$ProfileModelFromJson(json);
  Map<String, dynamic> toJson() => _$ProfileModelToJson(this);

  @override
  List<Object?> get props => [userId, age, weight, height, dietaryPreference, allergies, goal, targetCalories];
}
