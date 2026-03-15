import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../core/theme/app_colors.dart';
import '../domain/order_models.dart';
import '../domain/order_state.dart';

class OrderHistoryScreen extends ConsumerStatefulWidget {
  const OrderHistoryScreen({super.key});

  @override
  ConsumerState<OrderHistoryScreen> createState() =>
      _OrderHistoryScreenState();
}

class _OrderHistoryScreenState extends ConsumerState<OrderHistoryScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(orderHistoryProvider.notifier).load();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(orderHistoryProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Đơn hàng AI'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(orderHistoryProvider.notifier).load(),
          ),
        ],
      ),
      body: _buildBody(state),
    );
  }

  Widget _buildBody(OrderHistoryState state) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 48, color: AppColors.error),
            const SizedBox(height: 12),
            Text(state.error!, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: () =>
                  ref.read(orderHistoryProvider.notifier).load(),
              child: const Text('Thử lại'),
            ),
          ],
        ),
      );
    }
    if (state.orders.isEmpty) {
      return const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('🤖', style: TextStyle(fontSize: 56)),
            SizedBox(height: 16),
            Text(
              'Chưa có đơn hàng nào',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: AppColors.textPrimary,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Hãy chat với ChefGPT để bắt đầu mua sắm',
              style: TextStyle(color: AppColors.textSecondary),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.all(12),
      itemCount: state.orders.length,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (context, i) => _OrderCard(
        order: state.orders[i],
        onTap: () => _showDetail(context, state.orders[i]),
      ),
    );
  }

  void _showDetail(BuildContext context, AgentOrder order) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _OrderDetailSheet(order: order),
    );
  }
}

// ── Order Card ─────────────────────────────────────────────────────────────

class _OrderCard extends StatelessWidget {
  final AgentOrder order;
  final VoidCallback onTap;
  const _OrderCard({required this.order, required this.onTap});

  static String _storeEmoji(String storeId) {
    return switch (storeId) {
      'bhx' => '🟢',
      'winmart' => '🔵',
      'coopmart' => '🔴',
      'lotte' => '🟡',
      'bigc' => '🟠',
      _ => '🏪',
    };
  }

  @override
  Widget build(BuildContext context) {
    final fmt = DateFormat('dd/MM HH:mm');
    return Card(
      elevation: 1,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Text(_storeEmoji(order.storeId),
                      style: const TextStyle(fontSize: 20),),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      order.storeName,
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ),
                  _StatusChip(status: order.status),
                ],
              ),
              const SizedBox(height: 6),
              Text(
                fmt.format(order.createdAt.toLocal()),
                style: const TextStyle(
                  fontSize: 12,
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                order.items
                    .take(2)
                    .map((i) => '${i.productEmoji} ${i.productName}')
                    .join(' · '),
                style: const TextStyle(fontSize: 13),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              if (order.items.length > 2)
                Text(
                  '+${order.items.length - 2} sản phẩm khác',
                  style: const TextStyle(
                      fontSize: 12, color: AppColors.textSecondary,),
                ),
              const SizedBox(height: 6),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Tổng cộng',
                      style: TextStyle(
                          fontSize: 13, color: AppColors.textSecondary,),),
                  Text(
                    '${order.total.toStringAsFixed(0)}k VND',
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      color: AppColors.primary,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Status Chip ────────────────────────────────────────────────────────────

class _StatusChip extends StatelessWidget {
  final String status;
  const _StatusChip({required this.status});

  static (String, Color) _info(String s) => switch (s) {
        'pending_confirmation' => ('Chờ xác nhận', Colors.orange),
        'confirmed' => ('Đã xác nhận', Colors.blue),
        'paid' => ('Đã thanh toán', Colors.green),
        'delivered' => ('Đã giao', Colors.teal),
        'cancelled' => ('Đã huỷ', Colors.grey),
        _ => (s, Colors.grey),
      };

  @override
  Widget build(BuildContext context) {
    final (label, color) = _info(status);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 11,
          color: color,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

// ── Order Detail Sheet ─────────────────────────────────────────────────────

class _OrderDetailSheet extends ConsumerWidget {
  final AgentOrder order;
  const _OrderDetailSheet({required this.order});

  static const _cancellable = {'pending_confirmation', 'confirmed'};

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final fmt = DateFormat('dd/MM/yyyy HH:mm');

    return DraggableScrollableSheet(
      initialChildSize: 0.7,
      minChildSize: 0.4,
      maxChildSize: 0.95,
      expand: false,
      builder: (context, scrollCtrl) => ListView(
        controller: scrollCtrl,
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          // Handle
          Center(
            child: Container(
              width: 40,
              height: 4,
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: AppColors.divider,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),

          // Store + status
          Row(
            children: [
              Expanded(
                child: Text(
                  order.storeName,
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ),
              _StatusChip(status: order.status),
            ],
          ),
          const SizedBox(height: 16),

          // Items
          ...order.items.map((item) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  children: [
                    Text(item.productEmoji,
                        style: const TextStyle(fontSize: 20),),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(item.productName,
                              style: const TextStyle(
                                  fontWeight: FontWeight.w500,),),
                          Text('${item.unit} × ${item.quantity}',
                              style: const TextStyle(
                                  fontSize: 12,
                                  color: AppColors.textSecondary,),),
                        ],
                      ),
                    ),
                    Text(
                      '${item.subtotal.toStringAsFixed(0)}k',
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
              ),),

          const Divider(height: 24),

          // Pricing
          _PriceRow(label: 'Tạm tính', value: order.subtotal),
          const SizedBox(height: 4),
          _PriceRow(label: 'Phí giao hàng', value: order.deliveryFee),
          const SizedBox(height: 8),
          _PriceRow(
            label: 'Tổng cộng',
            value: order.total,
            bold: true,
            color: AppColors.primary,
          ),

          const SizedBox(height: 16),

          // Meta
          Wrap(
            spacing: 8,
            runSpacing: 6,
            children: [
              Chip(
                avatar: const Icon(Icons.payment, size: 16),
                label: Text(_methodLabel(order.paymentMethod)),
                padding: EdgeInsets.zero,
              ),
              Chip(
                avatar: const Icon(Icons.access_time, size: 16),
                label: Text(fmt.format(order.createdAt.toLocal())),
                padding: EdgeInsets.zero,
              ),
            ],
          ),

          if (order.transactionId != null) ...[
            const SizedBox(height: 8),
            Text(
              'ID: ${order.transactionId}',
              style: const TextStyle(
                fontSize: 11,
                fontFamily: 'monospace',
                color: AppColors.textSecondary,
              ),
            ),
          ],

          // Cancel button
          if (_cancellable.contains(order.status)) ...[
            const SizedBox(height: 24),
            OutlinedButton.icon(
              onPressed: () async {
                await ref
                    .read(orderHistoryProvider.notifier)
                    .cancel(order.id);
                if (context.mounted) Navigator.pop(context);
              },
              icon: const Icon(Icons.cancel_outlined, color: Colors.red),
              label: const Text('Huỷ đơn hàng',
                  style: TextStyle(color: Colors.red),),
              style: OutlinedButton.styleFrom(
                side: const BorderSide(color: Colors.red),
                minimumSize: const Size.fromHeight(44),
              ),
            ),
          ],
        ],
      ),
    );
  }

  static String _methodLabel(String method) => switch (method) {
        'cod' => 'Tiền mặt COD',
        'momo' => 'MoMo',
        'zalopay' => 'ZaloPay',
        'bank_transfer' => 'Chuyển khoản',
        _ => method,
      };
}

class _PriceRow extends StatelessWidget {
  final String label;
  final double value;
  final bool bold;
  final Color? color;
  const _PriceRow({
    required this.label,
    required this.value,
    this.bold = false,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    final style = TextStyle(
      fontWeight: bold ? FontWeight.bold : FontWeight.normal,
      color: color,
      fontSize: bold ? 15 : 14,
    );
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: style),
        Text('${value.toStringAsFixed(0)}k VND', style: style),
      ],
    );
  }
}
