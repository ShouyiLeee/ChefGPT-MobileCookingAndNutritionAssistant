import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:uuid/uuid.dart';

import '../../../core/network/api_service.dart';
import '../../../core/theme/app_colors.dart';
import '../../../shared/models/chat_message.dart';
import '../../orders/domain/order_models.dart';
import '../../persona/domain/persona_model.dart';
import '../../persona/domain/persona_state.dart';
import '../../persona/presentation/persona_chip.dart';

final _chatMessagesProvider =
    StateNotifierProvider<_ChatNotifier, List<ChatMessage>>(
        (ref) => _ChatNotifier(ref.read(apiServiceProvider), ref),);

class _ChatNotifier extends StateNotifier<List<ChatMessage>> {
  final ApiService _api;
  final Ref _ref;
  final _uuid = const Uuid();

  _ChatNotifier(this._api, this._ref) : super([]);

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

    final personaId = _ref.read(personaProvider).activePersona?.id;

    try {
      final history = state
          .where((m) => !m.isLoading)
          .map((m) => {
                'role': m.type == MessageType.user ? 'user' : 'model',
                'parts': [m.message],
              })
          .toList();

      final res = await _api.sendChat(text, history, personaId: personaId);
      final reply = res['message'] as String? ?? 'Xin lỗi, có lỗi xảy ra.';

      ShoppingSuggestion? suggestion;
      final rawSuggestion = res['shopping_suggestion'];
      if (rawSuggestion != null && rawSuggestion is Map<String, dynamic>) {
        try {
          suggestion = ShoppingSuggestion.fromJson(rawSuggestion);
        } catch (_) {
          // ignore malformed suggestion
        }
      }

      state = state
          .map((m) => m.id == loadingId
              ? m.copyWith(
                  message: reply,
                  isLoading: false,
                  shoppingSuggestion: suggestion,
                )
              : m)
          .toList();
    } catch (e) {
      state = state
          .map((m) => m.id == loadingId
              ? m.copyWith(
                  message: ApiService.parseError(e), isLoading: false,)
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
          const PersonaChip(),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Xóa lịch sử',
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

/// Quick action chips — reads from active persona's quick_actions list
class _QuickActions extends ConsumerWidget {
  final void Function(String) onTap;
  const _QuickActions({required this.onTap});

  static const _defaults = [
    'Gợi ý món từ trứng và cà chua',
    'Món eat clean cho bữa sáng',
    'Công thức phở bò đơn giản',
    'Thực đơn tăng cơ 2000 kcal',
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final persona = ref.watch(personaProvider).activePersona;
    final actions = (persona?.quickActions.isNotEmpty == true)
        ? persona!.quickActions
        : _defaults;

    return SizedBox(
      height: 48,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        children: actions
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

class _EmptyChat extends ConsumerWidget {
  const _EmptyChat();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final persona =
        ref.watch(personaProvider).activePersona ?? PersonaModel.defaultPersona;
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(persona.icon, style: const TextStyle(fontSize: 64)),
          const SizedBox(height: 16),
          Text(
            'Xin chào! Tôi là ${persona.name}',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 8),
          Text(
            persona.description,
            textAlign: TextAlign.center,
            style: Theme.of(context)
                .textTheme
                .bodyMedium
                ?.copyWith(color: AppColors.textSecondary),
          ),
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
      child: Column(
        crossAxisAlignment:
            isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          Container(
            margin: const EdgeInsets.only(bottom: 4),
            padding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            constraints: BoxConstraints(
                maxWidth: MediaQuery.of(context).size.width * 0.78,),
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
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : Text(
                    message.message,
                    style: TextStyle(
                      color:
                          isUser ? Colors.white : AppColors.textPrimary,
                      fontSize: 14,
                    ),
                  ),
          ),
          if (!isUser && message.shoppingSuggestion != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: _AgentShoppingCard(
                suggestion: message.shoppingSuggestion!,
              ),
            ),
          if (isUser || message.shoppingSuggestion == null)
            const SizedBox(height: 8),
        ],
      ),
    );
  }
}

// ── Agent Shopping Card ────────────────────────────────────────────────────

enum _CardState { idle, loading, confirmed, declined }

class _AgentShoppingCard extends ConsumerStatefulWidget {
  final ShoppingSuggestion suggestion;
  const _AgentShoppingCard({required this.suggestion});

  @override
  ConsumerState<_AgentShoppingCard> createState() => _AgentShoppingCardState();
}

class _AgentShoppingCardState extends ConsumerState<_AgentShoppingCard> {
  _CardState _cardState = _CardState.idle;
  String? _error;

  Future<void> _confirm() async {
    setState(() {
      _cardState = _CardState.loading;
      _error = null;
    });
    try {
      final api = ref.read(apiServiceProvider);
      await api.confirmPurchase(
        cartMandate: widget.suggestion.cartMandate.toJson(),
        paymentMandateId: widget.suggestion.mandateId,
      );
      setState(() => _cardState = _CardState.confirmed);
      await Future<void>.delayed(const Duration(seconds: 1));
      if (mounted) context.push('/orders');
    } catch (e) {
      setState(() {
        _cardState = _CardState.idle;
        _error = ApiService.parseError(e);
      });
    }
  }

  void _decline() => setState(() => _cardState = _CardState.declined);

  @override
  Widget build(BuildContext context) {
    final cart = widget.suggestion.cartMandate;
    final hasMandate = widget.suggestion.mandateId != null;

    if (_cardState == _CardState.confirmed) {
      return const _StatusBadge(
        icon: Icons.check_circle,
        color: Colors.green,
        label: 'Đã đặt hàng! Chuyển đến lịch sử đơn hàng...',
      );
    }
    if (_cardState == _CardState.declined) {
      return const _StatusBadge(
        icon: Icons.cancel,
        color: Colors.grey,
        label: 'Đã từ chối',
      );
    }

    return Container(
      width: MediaQuery.of(context).size.width * 0.85,
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppColors.primary.withValues(alpha: 0.4)),
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.08),
              borderRadius:
                  const BorderRadius.vertical(top: Radius.circular(12)),
            ),
            child: const Row(
              children: [
                Text('🤖', style: TextStyle(fontSize: 16)),
                SizedBox(width: 6),
                Expanded(
                  child: Text(
                    'Agent muốn mua sắm cho bạn',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: AppColors.primary,
                      fontSize: 13,
                    ),
                  ),
                ),
              ],
            ),
          ),

          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Store name
                Text(
                  '🏪 ${cart.storeName}',
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 8),

                // Items list (max 3 + overflow)
                ...cart.items.take(3).map((item) => Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Row(
                        children: [
                          Text(item.productEmoji,
                              style: const TextStyle(fontSize: 14),),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              item.productName,
                              style: const TextStyle(fontSize: 13),
                            ),
                          ),
                          Text(
                            'x${item.quantity}',
                            style: const TextStyle(
                              fontSize: 12,
                              color: AppColors.textSecondary,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            '${item.subtotal.toStringAsFixed(0)}k',
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ),),
                if (cart.items.length > 3)
                  Text(
                    '+${cart.items.length - 3} sản phẩm khác',
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppColors.textSecondary,
                      fontStyle: FontStyle.italic,
                    ),
                  ),

                const Divider(height: 16),

                // Total
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Tổng cộng',
                        style: TextStyle(fontWeight: FontWeight.w600),),
                    Text(
                      '${widget.suggestion.estimatedTotal.toStringAsFixed(0)}k VND',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        color: AppColors.primary,
                        fontSize: 15,
                      ),
                    ),
                  ],
                ),

                // No mandate warning
                if (!hasMandate) ...[
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.orange.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.orange.shade200),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.warning_amber_rounded,
                            size: 16, color: Colors.orange.shade700,),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            'Cần thiết lập Ví AI trước khi đặt hàng',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.orange.shade700,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],

                // Error message
                if (_error != null) ...[
                  const SizedBox(height: 6),
                  Text(
                    _error!,
                    style:
                        const TextStyle(color: Colors.red, fontSize: 12),
                  ),
                ],

                const SizedBox(height: 12),

                // Action buttons
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: _cardState == _CardState.loading
                            ? null
                            : _decline,
                        child: const Text('Từ chối'),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: FilledButton(
                        onPressed: (_cardState == _CardState.loading ||
                                !hasMandate)
                            ? (hasMandate
                                ? null
                                : () => context.push('/agent-wallet'))
                            : _confirm,
                        style: FilledButton.styleFrom(
                          backgroundColor: hasMandate
                              ? AppColors.primary
                              : Colors.orange,
                        ),
                        child: _cardState == _CardState.loading
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : Text(
                                hasMandate ? 'Xác nhận' : 'Thiết lập Ví AI',
                              ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final IconData icon;
  final Color color;
  final String label;
  const _StatusBadge({
    required this.icon,
    required this.color,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 16),
          const SizedBox(width: 6),
          Text(label, style: TextStyle(color: color, fontSize: 13)),
        ],
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
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, -5),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              decoration: InputDecoration(
                hintText: 'Hỏi về nấu ăn, dinh dưỡng...',
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
