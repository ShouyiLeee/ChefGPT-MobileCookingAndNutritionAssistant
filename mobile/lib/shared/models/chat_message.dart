import 'package:equatable/equatable.dart';

import '../../features/orders/domain/order_models.dart';

enum MessageType { user, assistant }

class ChatMessage extends Equatable {
  final String id;
  final String message;
  final MessageType type;
  final DateTime timestamp;
  final bool isLoading;
  final ShoppingSuggestion? shoppingSuggestion;

  const ChatMessage({
    required this.id,
    required this.message,
    required this.type,
    required this.timestamp,
    this.isLoading = false,
    this.shoppingSuggestion,
  });

  ChatMessage copyWith({
    String? id,
    String? message,
    MessageType? type,
    DateTime? timestamp,
    bool? isLoading,
    ShoppingSuggestion? shoppingSuggestion,
  }) {
    return ChatMessage(
      id: id ?? this.id,
      message: message ?? this.message,
      type: type ?? this.type,
      timestamp: timestamp ?? this.timestamp,
      isLoading: isLoading ?? this.isLoading,
      shoppingSuggestion: shoppingSuggestion ?? this.shoppingSuggestion,
    );
  }

  @override
  List<Object?> get props =>
      [id, message, type, timestamp, isLoading, shoppingSuggestion];
}
