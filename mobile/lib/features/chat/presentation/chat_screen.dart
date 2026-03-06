import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';
import '../../../core/network/api_service.dart';
import '../../../core/theme/app_colors.dart';
import '../../../shared/models/chat_message.dart';

final _chatMessagesProvider =
    StateNotifierProvider<_ChatNotifier, List<ChatMessage>>(
        (ref) => _ChatNotifier(ref.read(apiServiceProvider)));

class _ChatNotifier extends StateNotifier<List<ChatMessage>> {
  final ApiService _api;
  final _uuid = const Uuid();

  _ChatNotifier(this._api) : super([]);

  Future<void> send(String text) async {
    final userMsg = ChatMessage(
      id: _uuid.v4(),
      message: text,
      type: MessageType.user,
      timestamp: DateTime.now(),
    );
    final loadingId = _uuid.v4();
    final loadingMsg = ChatMessage(
      id: loadingId,
      message: '',
      type: MessageType.assistant,
      timestamp: DateTime.now(),
      isLoading: true,
    );
    state = [...state, userMsg, loadingMsg];

    try {
      final history = state
          .where((m) => !m.isLoading)
          .map((m) => {
                'role': m.type == MessageType.user ? 'user' : 'model',
                'parts': [m.message],
              })
          .toList();

      final res = await _api.sendChat(text, history);
      final reply = res['message'] as String? ?? 'Xin loi, co loi xay ra.';

      state = state
          .map((m) =>
              m.id == loadingId ? m.copyWith(message: reply, isLoading: false) : m)
          .toList();
    } catch (e) {
      state = state
          .map((m) => m.id == loadingId
              ? m.copyWith(
                  message: 'Loi ket noi. Vui long thu lai.', isLoading: false)
              : m)
          .toList();
    }
  }

  void clear() => state = [];
}

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final TextEditingController _ctrl = TextEditingController();
  final ScrollController _scroll = ScrollController();

  @override
  void dispose() {
    _ctrl.dispose();
    _scroll.dispose();
    super.dispose();
  }

  void _send() {
    final text = _ctrl.text.trim();
    if (text.isEmpty) return;
    _ctrl.clear();
    ref.read(_chatMessagesProvider.notifier).send(text);
    Future.delayed(const Duration(milliseconds: 300), () {
      if (_scroll.hasClients) {
        _scroll.animateTo(
          _scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final messages = ref.watch(_chatMessagesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('ChefGPT'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Xoa lich su',
            onPressed: () => ref.read(_chatMessagesProvider.notifier).clear(),
          ),
        ],
      ),
      body: Column(
        children: [
          _QuickActions(onTap: (q) {
            _ctrl.text = q;
            _send();
          }),
          const Divider(height: 1),
          Expanded(
            child: messages.isEmpty
                ? const _EmptyChat()
                : ListView.builder(
                    controller: _scroll,
                    padding: const EdgeInsets.all(16),
                    itemCount: messages.length,
                    itemBuilder: (_, i) => _MessageBubble(message: messages[i]),
                  ),
          ),
          _InputBar(controller: _ctrl, onSend: _send),
        ],
      ),
    );
  }
}

class _QuickActions extends StatelessWidget {
  final void Function(String) onTap;
  const _QuickActions({required this.onTap});

  static const _actions = [
    'Goi y mon tu trung va ca chua',
    'Mon eat clean cho bua sang',
    'Cong thuc pho bo don gian',
    'Thuc don tang co 2000 kcal',
  ];

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 48,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        children: _actions
            .map((a) => Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ActionChip(
                    label: Text(a, style: const TextStyle(fontSize: 12)),
                    onPressed: () => onTap(a),
                    backgroundColor: AppColors.surface,
                  ),
                ))
            .toList(),
      ),
    );
  }
}

class _EmptyChat extends StatelessWidget {
  const _EmptyChat();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.restaurant, size: 64, color: AppColors.primary),
          const SizedBox(height: 16),
          Text('Xin chao! Toi la ChefGPT',
              style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          Text('Hoi toi bat ky dieu gi ve nau an',
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: AppColors.textSecondary)),
        ],
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  final ChatMessage message;
  const _MessageBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    final isUser = message.type == MessageType.user;
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        constraints:
            BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.78),
        decoration: BoxDecoration(
          color: isUser ? AppColors.primary : AppColors.surface,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isUser ? 16 : 4),
            bottomRight: Radius.circular(isUser ? 4 : 16),
          ),
        ),
        child: message.isLoading
            ? const SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(strokeWidth: 2))
            : Text(
                message.message,
                style: TextStyle(
                  color: isUser ? Colors.white : AppColors.textPrimary,
                  fontSize: 14,
                ),
              ),
      ),
    );
  }
}

class _InputBar extends StatelessWidget {
  final TextEditingController controller;
  final VoidCallback onSend;
  const _InputBar({required this.controller, required this.onSend});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, -5),
          )
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              decoration: InputDecoration(
                hintText: 'Hoi ve nau an, dinh duong...',
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide.none,
                ),
                contentPadding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              ),
              maxLines: null,
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => onSend(),
            ),
          ),
          const SizedBox(width: 8),
          FilledButton(
            onPressed: onSend,
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.primary,
              shape: const CircleBorder(),
              padding: const EdgeInsets.all(12),
            ),
            child: const Icon(Icons.send, color: Colors.white),
          ),
        ],
      ),
    );
  }
}
