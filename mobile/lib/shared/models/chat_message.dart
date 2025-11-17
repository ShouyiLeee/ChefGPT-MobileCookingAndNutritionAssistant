import 'package:json_annotation/json_annotation.dart';
import 'package:equatable/equatable.dart';

part 'chat_message.g.dart';

@JsonSerializable()
class ChatMessage extends Equatable {
  final String id;
  final String message;
  final MessageType type;
  final DateTime timestamp;
  final MessageContent? content;
  final bool isLoading;

  const ChatMessage({
    required this.id,
    required this.message,
    required this.type,
    required this.timestamp,
    this.content,
    this.isLoading = false,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> json) => _$ChatMessageFromJson(json);
  Map<String, dynamic> toJson() => _$ChatMessageToJson(this);

  ChatMessage copyWith({
    String? id,
    String? message,
    MessageType? type,
    DateTime? timestamp,
    MessageContent? content,
    bool? isLoading,
  }) {
    return ChatMessage(
      id: id ?? this.id,
      message: message ?? this.message,
      type: type ?? this.type,
      timestamp: timestamp ?? this.timestamp,
      content: content ?? this.content,
      isLoading: isLoading ?? this.isLoading,
    );
  }

  @override
  List<Object?> get props => [id, message, type, timestamp, content, isLoading];
}

enum MessageType {
  @JsonValue('user')
  user,
  @JsonValue('assistant')
  assistant,
  @JsonValue('system')
  system,
}

@JsonSerializable()
class MessageContent extends Equatable {
  final List<int>? recipeIds;
  final List<String>? ingredients;
  final String? imageUrl;
  final Map<String, dynamic>? metadata;

  const MessageContent({
    this.recipeIds,
    this.ingredients,
    this.imageUrl,
    this.metadata,
  });

  factory MessageContent.fromJson(Map<String, dynamic> json) => _$MessageContentFromJson(json);
  Map<String, dynamic> toJson() => _$MessageContentToJson(this);

  @override
  List<Object?> get props => [recipeIds, ingredients, imageUrl, metadata];
}
