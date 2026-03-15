import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../domain/order_models.dart';
import '../domain/order_state.dart';

/// Visualizes the end-to-end AP2 Agentic Payment workflow:
/// Mandate → Intent → Cart → Consent → Payment → Tracking
class Ap2FlowScreen extends ConsumerWidget {
  const Ap2FlowScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final walletState = ref.watch(agentWalletProvider);
    final mandate = walletState.mandate;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Quy trình AP2'),
        centerTitle: true,
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          // ── Header banner ─────────────────────────────────────────────────
          _HeaderBanner(mandateConfigured: mandate != null),
          const SizedBox(height: 20),

          // ── Mandate status card ───────────────────────────────────────────
          _MandateStatusCard(mandate: mandate),
          const SizedBox(height: 24),

          // ── Flow title ────────────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Text(
              'Các bước hoạt động',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
            ),
          ),

          // ── Step cards ───────────────────────────────────────────────────
          ..._buildSteps(context, mandate),

          const SizedBox(height: 28),

          // ── Consent rules ─────────────────────────────────────────────────
          _ConsentRulesCard(mandate: mandate),

          const SizedBox(height: 24),

          // ── Quick actions ─────────────────────────────────────────────────
          Row(
            children: [
              Expanded(
                child: _ActionButton(
                  icon: Icons.account_balance_wallet_outlined,
                  label: 'Thiết lập Ví AI',
                  onTap: () => context.push('/agent-wallet'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _ActionButton(
                  icon: Icons.receipt_long_outlined,
                  label: 'Đơn hàng AI',
                  onTap: () => context.push('/orders'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  List<Widget> _buildSteps(BuildContext context, PaymentMandateModel? mandate) {
    final steps = [
      _FlowStep(
        index: 1,
        emoji: '🏦',
        title: 'Thiết lập Ví AI',
        subtitle: 'Bạn cấu hình một lần',
        description:
            'Bạn thiết lập hạn mức chi tiêu tối đa (ví dụ: 500k VND/giao dịch), '
            'phương thức thanh toán, và các cửa hàng được phép. '
            'Đây là "ủy quyền" (Mandate) — AI chỉ được hành động trong giới hạn này.',
        isComplete: mandate != null,
        tag: 'User Action',
        tagColor: AppColors.primary,
        details: mandate != null
            ? [
                '✓ Hạn mức: ${mandate.spendingLimit.toStringAsFixed(0)}k VND',
                '✓ TT: ${_methodLabel(mandate.paymentMethod)}',
              ]
            : ['⚠ Chưa thiết lập — AI chưa thể đặt hàng'],
      ),
      const _FlowStep(
        index: 2,
        emoji: '💬',
        title: 'Bạn chat với ChefGPT',
        subtitle: 'Tự nhiên như bình thường',
        description:
            'Bạn nhắn tin bình thường, ví dụ: "mua nguyên liệu nấu phở bò cho 4 người". '
            'Không cần lệnh đặc biệt. ChefGPT trả lời câu hỏi đồng thời '
            'phân tích song song để phát hiện ý định mua sắm.',
        isComplete: true,
        tag: 'User Action',
        tagColor: AppColors.primary,
      ),
      const _FlowStep(
        index: 3,
        emoji: '🤖',
        title: 'AI Phát hiện ý định',
        subtitle: 'Tự động trong 3 giây',
        description:
            'Gemini phân tích tin nhắn và trích xuất danh sách nguyên liệu '
            '(ví dụ: xương bò, hành, quế, hồi...). Bước này chạy nền song song '
            'với câu trả lời của AI — không làm chậm chat. '
            'Nếu timeout >3s, bước này bị bỏ qua để đảm bảo UX.',
        isComplete: true,
        tag: 'AI Automatic',
        tagColor: Colors.purple,
      ),
      const _FlowStep(
        index: 4,
        emoji: '🛒',
        title: 'Xây dựng giỏ hàng',
        subtitle: 'Agent chọn sản phẩm',
        description:
            'AI khớp nguyên liệu với catalog 60+ sản phẩm từ 5 cửa hàng '
            '(Bách Hóa Xanh, Winmart, CoopMart, Lotte, Big C). '
            'Chọn cửa hàng có nhiều sản phẩm khớp nhất. '
            'Kết quả là một "Cart Mandate" — giỏ hàng đề xuất kèm tổng giá.',
        isComplete: true,
        tag: 'AI Automatic',
        tagColor: Colors.purple,
      ),
      const _FlowStep(
        index: 5,
        emoji: '✅',
        title: 'Bạn xác nhận',
        subtitle: 'Đây là cơ chế đồng thuận',
        description:
            'Một thẻ xác nhận hiện trong chat với danh sách sản phẩm, cửa hàng, '
            'và tổng tiền. Bạn chọn [Xác nhận] hoặc [Từ chối]. '
            'AI KHÔNG được đặt hàng nếu không có xác nhận của bạn ở bước này — '
            'đây là nguyên tắc cốt lõi của AP2.',
        isComplete: true,
        tag: 'User Consent ⭐',
        tagColor: Colors.orange,
        highlight: true,
      ),
      const _FlowStep(
        index: 6,
        emoji: '💳',
        title: 'Thanh toán',
        subtitle: 'Trong hạn mức đã thiết lập',
        description:
            'Hệ thống kiểm tra tổng đơn hàng ≤ hạn mức Ví AI. '
            'Nếu hợp lệ, thực hiện thanh toán qua phương thức đã chọn. '
            'Đơn hàng được tạo với trạng thái "paid" và mã giao dịch. '
            'Nếu vượt hạn mức → báo lỗi, không thực hiện.',
        isComplete: true,
        tag: 'System',
        tagColor: Colors.teal,
      ),
      const _FlowStep(
        index: 7,
        emoji: '📦',
        title: 'Theo dõi đơn hàng',
        subtitle: 'Minh bạch hoàn toàn',
        description:
            'Mọi đơn hàng AI đặt đều xuất hiện trong "Đơn hàng AI" kèm '
            'trạng thái (đang chờ → đã xác nhận → đã thanh toán → đang giao → đã nhận), '
            'thời gian, mã giao dịch, và danh sách sản phẩm chi tiết. '
            'Bạn có thể huỷ đơn nếu chưa giao.',
        isComplete: true,
        tag: 'Transparency',
        tagColor: Colors.green,
      ),
    ];

    final widgets = <Widget>[];
    for (int i = 0; i < steps.length; i++) {
      widgets.add(steps[i]);
      if (i < steps.length - 1) {
        widgets.add(const _StepConnector());
      }
    }
    return widgets;
  }

  String _methodLabel(String method) {
    const labels = {
      'cod': 'Tiền mặt COD',
      'momo': 'MoMo',
      'zalopay': 'ZaloPay',
      'bank_transfer': 'Chuyển khoản',
    };
    return labels[method] ?? method;
  }
}

// ── Header banner ──────────────────────────────────────────────────────────────

class _HeaderBanner extends StatelessWidget {
  final bool mandateConfigured;
  const _HeaderBanner({required this.mandateConfigured});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppColors.primary.withValues(alpha: 0.12),
            Colors.purple.withValues(alpha: 0.08),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppColors.primary.withValues(alpha: 0.25),
        ),
      ),
      child: Row(
        children: [
          const Text('🤖', style: TextStyle(fontSize: 36)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'AP2 — Agentic Payment Protocol',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: AppColors.primary,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  'AI mua sắm thay bạn, trong giới hạn bạn đặt ra, '
                  'với sự đồng ý rõ ràng của bạn.',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.textSecondary,
                        height: 1.4,
                      ),
                ),
                const SizedBox(height: 6),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: mandateConfigured
                        ? Colors.green.withValues(alpha: 0.15)
                        : Colors.orange.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    mandateConfigured ? '✓ Ví AI đã cấu hình' : '⚠ Cần thiết lập Ví AI',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: mandateConfigured ? Colors.green[700] : Colors.orange[800],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Mandate status card ────────────────────────────────────────────────────────

class _MandateStatusCard extends StatelessWidget {
  final PaymentMandateModel? mandate;
  const _MandateStatusCard({required this.mandate});

  @override
  Widget build(BuildContext context) {
    if (mandate == null) {
      return Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.orange.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.orange.withValues(alpha: 0.3)),
        ),
        child: Row(
          children: [
            const Icon(Icons.warning_amber_rounded, color: Colors.orange, size: 20),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                'Chưa thiết lập Ví AI. AI không thể đặt hàng cho bạn cho đến khi cấu hình hạn mức và phương thức thanh toán.',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.orange[800],
                    ),
              ),
            ),
          ],
        ),
      );
    }

    const methodIcons = {
      'cod': Icons.money,
      'momo': Icons.wallet,
      'zalopay': Icons.payment,
      'bank_transfer': Icons.account_balance,
    };
    const methodLabels = {
      'cod': 'Tiền mặt COD',
      'momo': 'MoMo',
      'zalopay': 'ZaloPay',
      'bank_transfer': 'Chuyển khoản',
    };

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.green.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.green.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.shield_outlined, color: Colors.green, size: 18),
              const SizedBox(width: 6),
              Text(
                'Ví AI của bạn',
                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      color: Colors.green[700],
                      fontWeight: FontWeight.bold,
                    ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              _StatusPill(
                icon: Icons.speed,
                label: '${mandate!.spendingLimit.toStringAsFixed(0)}k VND / đơn',
              ),
              const SizedBox(width: 8),
              _StatusPill(
                icon: methodIcons[mandate!.paymentMethod] ?? Icons.payment,
                label: methodLabels[mandate!.paymentMethod] ?? mandate!.paymentMethod,
              ),
            ],
          ),
          if (mandate!.preferredStoreIds.isNotEmpty) ...[
            const SizedBox(height: 6),
            _StatusPill(
              icon: Icons.store,
              label: '${mandate!.preferredStoreIds.length} cửa hàng cho phép',
            ),
          ],
        ],
      ),
    );
  }
}

class _StatusPill extends StatelessWidget {
  final IconData icon;
  final String label;
  const _StatusPill({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.green.withValues(alpha: 0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 13, color: Colors.green[700]),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              color: Colors.green[800],
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}

// ── Step connector ─────────────────────────────────────────────────────────────

class _StepConnector extends StatelessWidget {
  const _StepConnector();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 28),
      child: SizedBox(
        height: 20,
        child: VerticalDivider(
          color: AppColors.primary.withValues(alpha: 0.25),
          thickness: 2,
          width: 2,
        ),
      ),
    );
  }
}

// ── Flow step card ─────────────────────────────────────────────────────────────

class _FlowStep extends StatelessWidget {
  final int index;
  final String emoji;
  final String title;
  final String subtitle;
  final String description;
  final bool isComplete;
  final String tag;
  final Color tagColor;
  final bool highlight;
  final List<String> details;

  const _FlowStep({
    required this.index,
    required this.emoji,
    required this.title,
    required this.subtitle,
    required this.description,
    required this.isComplete,
    required this.tag,
    required this.tagColor,
    this.highlight = false,
    this.details = const [],
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: highlight
              ? Colors.orange.withValues(alpha: 0.5)
              : AppColors.primary.withValues(alpha: 0.12),
          width: highlight ? 2 : 1,
        ),
        color: highlight
            ? Colors.orange.withValues(alpha: 0.04)
            : Theme.of(context).cardColor,
        boxShadow: highlight
            ? [
                BoxShadow(
                  color: Colors.orange.withValues(alpha: 0.08),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ]
            : null,
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Step header
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Index circle
                Container(
                  width: 28,
                  height: 28,
                  decoration: BoxDecoration(
                    color: AppColors.primary,
                    shape: BoxShape.circle,
                  ),
                  child: Center(
                    child: Text(
                      '$index',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(emoji, style: const TextStyle(fontSize: 18)),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              title,
                              style: Theme.of(context)
                                  .textTheme
                                  .titleSmall
                                  ?.copyWith(fontWeight: FontWeight.bold),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 2),
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: tagColor.withValues(alpha: 0.12),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              tag,
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                                color: tagColor,
                              ),
                            ),
                          ),
                          const SizedBox(width: 6),
                          Text(
                            subtitle,
                            style: Theme.of(context)
                                .textTheme
                                .bodySmall
                                ?.copyWith(
                                    color: AppColors.textSecondary,
                                    fontSize: 11),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            // Description
            Text(
              description,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppColors.textSecondary,
                    height: 1.5,
                  ),
            ),
            // Optional detail lines (e.g. mandate values)
            if (details.isNotEmpty) ...[
              const SizedBox(height: 8),
              ...details.map(
                (d) => Padding(
                  padding: const EdgeInsets.only(top: 3),
                  child: Text(
                    d,
                    style: TextStyle(
                      fontSize: 12,
                      color: d.startsWith('✓')
                          ? Colors.green[700]
                          : Colors.orange[800],
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

// ── Consent rules card ────────────────────────────────────────────────────────

class _ConsentRulesCard extends StatelessWidget {
  final PaymentMandateModel? mandate;
  const _ConsentRulesCard({required this.mandate});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.blue.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.blue.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.gavel_rounded, size: 18, color: Colors.blue),
              const SizedBox(width: 8),
              Text(
                'Nguyên tắc đồng thuận AP2',
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: Colors.blue[800],
                    ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          _RuleRow(
            icon: '🔒',
            rule: 'AI chỉ đặt hàng sau khi bạn bấm [Xác nhận]',
            positive: true,
          ),
          _RuleRow(
            icon: '💰',
            rule: 'Tổng đơn không vượt hạn mức Ví AI'
                '${mandate != null ? " (${mandate!.spendingLimit.toStringAsFixed(0)}k)" : ""}',
            positive: true,
          ),
          _RuleRow(
            icon: '🏪',
            rule: 'Chỉ đặt tại các cửa hàng bạn cho phép',
            positive: true,
          ),
          _RuleRow(
            icon: '📋',
            rule: 'Mọi đơn hàng được lưu và có thể xem lại',
            positive: true,
          ),
          _RuleRow(
            icon: '❌',
            rule: 'AI không tự động mua mà không hỏi',
            positive: false,
          ),
          _RuleRow(
            icon: '❌',
            rule: 'AI không vượt hạn mức dù bạn yêu cầu',
            positive: false,
          ),
        ],
      ),
    );
  }
}

class _RuleRow extends StatelessWidget {
  final String icon;
  final String rule;
  final bool positive;
  const _RuleRow({required this.icon, required this.rule, required this.positive});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(icon, style: const TextStyle(fontSize: 14)),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              rule,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: positive ? AppColors.textPrimary : AppColors.textSecondary,
                    height: 1.4,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Action button ─────────────────────────────────────────────────────────────

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  const _ActionButton({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: onTap,
      icon: Icon(icon, size: 18),
      label: Text(label, style: const TextStyle(fontSize: 13)),
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.primary,
        side: BorderSide(color: AppColors.primary.withValues(alpha: 0.4)),
        padding: const EdgeInsets.symmetric(vertical: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
    );
  }
}
