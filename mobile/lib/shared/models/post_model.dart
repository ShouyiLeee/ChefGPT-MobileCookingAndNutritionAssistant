import 'package:json_annotation/json_annotation.dart';
import 'package:equatable/equatable.dart';

part 'post_model.g.dart';

@JsonSerializable()
class PostModel extends Equatable {
  final int id;
  final String authorId;
  final String? authorName;
  final String? authorAvatar;
  final String content;
  final List<String>? imageUrls;
  final String? videoUrl;
  final int? recipeId;
  final int likesCount;
  final int commentsCount;
  final bool isLikedByMe;
  final DateTime createdAt;

  const PostModel({
    required this.id,
    required this.authorId,
    this.authorName,
    this.authorAvatar,
    required this.content,
    this.imageUrls,
    this.videoUrl,
    this.recipeId,
    this.likesCount = 0,
    this.commentsCount = 0,
    this.isLikedByMe = false,
    required this.createdAt,
  });

  factory PostModel.fromJson(Map<String, dynamic> json) => _$PostModelFromJson(json);
  Map<String, dynamic> toJson() => _$PostModelToJson(this);

  PostModel copyWith({
    int? id,
    String? authorId,
    String? authorName,
    String? authorAvatar,
    String? content,
    List<String>? imageUrls,
    String? videoUrl,
    int? recipeId,
    int? likesCount,
    int? commentsCount,
    bool? isLikedByMe,
    DateTime? createdAt,
  }) {
    return PostModel(
      id: id ?? this.id,
      authorId: authorId ?? this.authorId,
      authorName: authorName ?? this.authorName,
      authorAvatar: authorAvatar ?? this.authorAvatar,
      content: content ?? this.content,
      imageUrls: imageUrls ?? this.imageUrls,
      videoUrl: videoUrl ?? this.videoUrl,
      recipeId: recipeId ?? this.recipeId,
      likesCount: likesCount ?? this.likesCount,
      commentsCount: commentsCount ?? this.commentsCount,
      isLikedByMe: isLikedByMe ?? this.isLikedByMe,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  @override
  List<Object?> get props => [id, authorId, authorName, authorAvatar, content, imageUrls, videoUrl, recipeId, likesCount, commentsCount, isLikedByMe, createdAt];
}
