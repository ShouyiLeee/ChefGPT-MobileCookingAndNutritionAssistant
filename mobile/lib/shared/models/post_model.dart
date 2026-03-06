import 'package:equatable/equatable.dart';

class PostModel extends Equatable {
  final int id;
  final String authorId;
  final String authorName;
  final String? authorAvatar;
  final String content;
  final List<String> imageUrls;
  final int likeCount;
  final int commentCount;
  final bool isLikedByMe;
  final DateTime createdAt;

  const PostModel({
    required this.id,
    required this.authorId,
    required this.authorName,
    this.authorAvatar,
    required this.content,
    this.imageUrls = const [],
    required this.likeCount,
    required this.commentCount,
    required this.isLikedByMe,
    required this.createdAt,
  });

  factory PostModel.fromJson(Map<String, dynamic> json) {
    final rawUrls = json['image_urls'];
    final imageUrls = rawUrls is List
        ? rawUrls.map((e) => e as String).toList()
        : <String>[];
    return PostModel(
      id: json['id'] as int,
      authorId: json['author_id'] as String? ?? '',
      authorName: json['author_name'] as String? ?? 'ChefGPT User',
      authorAvatar: json['author_avatar'] as String?,
      content: json['content'] as String? ?? '',
      imageUrls: imageUrls,
      likeCount: json['like_count'] as int? ?? 0,
      commentCount: json['comment_count'] as int? ?? 0,
      isLikedByMe: json['is_liked_by_me'] as bool? ?? false,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
    );
  }

  PostModel copyWith({int? likeCount, int? commentCount, bool? isLikedByMe}) =>
      PostModel(
        id: id,
        authorId: authorId,
        authorName: authorName,
        authorAvatar: authorAvatar,
        content: content,
        imageUrls: imageUrls,
        likeCount: likeCount ?? this.likeCount,
        commentCount: commentCount ?? this.commentCount,
        isLikedByMe: isLikedByMe ?? this.isLikedByMe,
        createdAt: createdAt,
      );

  String get timeAgo {
    final diff = DateTime.now().difference(createdAt);
    if (diff.inSeconds < 60) return 'Vua xong';
    if (diff.inMinutes < 60) return '${diff.inMinutes} phut truoc';
    if (diff.inHours < 24) return '${diff.inHours} gio truoc';
    if (diff.inDays < 7) return '${diff.inDays} ngay truoc';
    if (diff.inDays < 30) return '${(diff.inDays / 7).floor()} tuan truoc';
    if (diff.inDays < 365) return '${(diff.inDays / 30).floor()} thang truoc';
    return '${(diff.inDays / 365).floor()} nam truoc';
  }

  @override
  List<Object?> get props =>
      [id, authorId, content, likeCount, commentCount, isLikedByMe, createdAt];
}
