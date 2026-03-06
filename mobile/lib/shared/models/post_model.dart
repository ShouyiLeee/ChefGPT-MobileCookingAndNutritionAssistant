import 'package:equatable/equatable.dart';

class PostModel extends Equatable {
  final int id;
  final String authorName;
  final String? authorAvatar;
  final String content;
  final int likeCount;
  final int commentCount;
  final String createdAt;

  const PostModel({
    required this.id,
    required this.authorName,
    this.authorAvatar,
    required this.content,
    required this.likeCount,
    required this.commentCount,
    required this.createdAt,
  });

  factory PostModel.fromJson(Map<String, dynamic> json) {
    final author = json['author'] as Map<String, dynamic>?;
    return PostModel(
      id: json['id'] as int,
      authorName: author?['name'] as String? ?? 'Anonymous',
      authorAvatar: author?['avatar_url'] as String?,
      content: json['content'] as String? ?? '',
      likeCount: json['like_count'] as int? ?? 0,
      commentCount: json['comment_count'] as int? ?? 0,
      createdAt: json['created_at'] as String? ?? '',
    );
  }

  @override
  List<Object?> get props =>
      [id, authorName, content, likeCount, commentCount, createdAt];
}
