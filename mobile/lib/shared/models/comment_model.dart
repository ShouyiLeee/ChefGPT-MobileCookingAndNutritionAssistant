import 'package:equatable/equatable.dart';

class CommentModel extends Equatable {
  final int id;
  final String userId;
  final String userName;
  final String? userAvatar;
  final String content;
  final int likeCount;
  final int? parentId;
  final DateTime createdAt;

  const CommentModel({
    required this.id,
    required this.userId,
    required this.userName,
    this.userAvatar,
    required this.content,
    required this.likeCount,
    this.parentId,
    required this.createdAt,
  });

  factory CommentModel.fromJson(Map<String, dynamic> json) => CommentModel(
        id: json['id'] as int,
        userId: json['user_id'] as String? ?? '',
        userName: json['user_name'] as String? ?? 'ChefGPT User',
        userAvatar: json['user_avatar'] as String?,
        content: json['content'] as String? ?? '',
        likeCount: json['like_count'] as int? ?? 0,
        parentId: json['parent_id'] as int?,
        createdAt: json['created_at'] != null
            ? DateTime.tryParse(json['created_at'] as String) ?? DateTime.now()
            : DateTime.now(),
      );

  String get timeAgo {
    final diff = DateTime.now().difference(createdAt);
    if (diff.inSeconds < 60) return 'Vừa xong';
    if (diff.inMinutes < 60) return '${diff.inMinutes}ph';
    if (diff.inHours < 24) return '${diff.inHours}g';
    return '${diff.inDays}ng';
  }

  @override
  List<Object?> get props => [id, userId, content, likeCount, createdAt];
}
