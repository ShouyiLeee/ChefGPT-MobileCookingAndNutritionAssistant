import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';
import '../domain/order_models.dart';
import '../domain/order_state.dart';

class AgentWalletScreen extends ConsumerStatefulWidget {
  const AgentWalletScreen({super.key});

  @override
  ConsumerState<AgentWalletScreen> createState() => _AgentWalletScreenState();
}

class _AgentWalletScreenState extends ConsumerState<AgentWalletScreen> {
  double _spendingLimit = 500.0;
  String _paymentMethod = 'cod';
  final Set<String> _allowedStores = {
    'bhx', 'winmart', 'coopmart', 'lotte', 'bigc',
  };

  bool _formLoaded = false;

  static const _stores = [
    ('bhx', 'Bách Hóa Xanh', '🟢'),
    ('winmart', 'Winmart', '🔵'),
    ('coopmart', 'CoopMart', '🔴'),
    ('lotte', 'Lotte Mart', '🟡'),
    ('bigc', 'Big C', '🟠'),
  ];

  static const _methods = [
    ('cod', 'Tiền mặt COD', Icons.money),
    ('momo', 'MoMo', Icons.wallet),
    ('zalopay', 'ZaloPay', Icons.payment),
    ('bank_transfer', 'Chuyển khoản', Icons.account_balance),
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(agentWalletProvider.notifier).load();
    });
  }

  void _applyMandate(PaymentMandateModel m) {
    if (_formLoaded) return;
    setState(() {
      _spendingLimit = m.spendingLimit.clamp(50.0, 2000.0);
      _paymentMethod = m.paymentMethod;
      _allowedStores
        ..clear()
        ..addAll(
          m.preferredStoreIds.isEmpty
              ? _stores.map((s) => s.$1)
              : m.preferredStoreIds,
        );
      _formLoaded = true;
    });
  }

  Future<void> _save() async {
    final model = PaymentMandateModel(
      id: 0,
      paymentMethod: _paymentMethod,
      spendingLimit: _spendingLimit,
      preferredStoreIds: _allowedStores.toList(),
      autoBuyEnabled: false,
    );
    final ok = await ref.read(agentWalletProvider.notifier).save(model);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(ok ? 'Đã lưu cài đặt Ví AI ✓' : 'Lưu thất bại, thử lại'),
        backgroundColor: ok ? AppColors.success : AppColors.error,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final walletState = ref.watch(agentWalletProvider);

    if (walletState.mandate != null && !_formLoaded) {
      _applyMandate(walletState.mandate!);
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Ví AI & Hạn mức Thanh toán')),
      body: walletState.isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // ── Spending Limit ──────────────────────────────────────────
                const _SectionHeader(
                  icon: Icons.speed,
                  title: 'Hạn mức chi tiêu',
                ),
                const SizedBox(height: 8),
                Text(
                  'Tối đa ${_spendingLimit.toStringAsFixed(0)}k VND / giao dịch',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: AppColors.primary,
                        fontWeight: FontWeight.bold,
                      ),
                  textAlign: TextAlign.center,
                ),
                Slider(
                  value: _spendingLimit,
                  min: 50,
                  max: 2000,
                  divisions: 39,
                  activeColor: AppColors.primary,
                  label: '${_spendingLimit.toStringAsFixed(0)}k',
                  onChanged: (v) => setState(() => _spendingLimit = v),
                ),
                const Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('50k', style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                    Text('2,000k', style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                  ],
                ),

                const SizedBox(height: 24),

                // ── Payment Method ──────────────────────────────────────────
                const _SectionHeader(
                  icon: Icons.credit_card,
                  title: 'Phương thức thanh toán',
                ),
                const SizedBox(height: 8),
                RadioGroup<String>(
                  groupValue: _paymentMethod,
                  onChanged: (v) =>
                      setState(() => _paymentMethod = v ?? _paymentMethod),
                  child: Column(
                    children: _methods.map((m) => RadioListTile<String>(
                          value: m.$1,
                          title: Text(m.$2),
                          secondary: Icon(m.$3, color: AppColors.primary),
                          activeColor: AppColors.primary,
                          contentPadding: EdgeInsets.zero,
                        ),).toList(),
                  ),
                ),

                const SizedBox(height: 24),

                // ── Allowed Stores ──────────────────────────────────────────
                const _SectionHeader(
                  icon: Icons.store,
                  title: 'Cửa hàng được phép đặt',
                ),
                const SizedBox(height: 8),
                ..._stores.map((s) => CheckboxListTile(
                      value: _allowedStores.contains(s.$1),
                      onChanged: (checked) => setState(() {
                        if (checked == true) {
                          _allowedStores.add(s.$1);
                        } else {
                          _allowedStores.remove(s.$1);
                        }
                      }),
                      title: Text('${s.$3} ${s.$2}'),
                      activeColor: AppColors.primary,
                      contentPadding: EdgeInsets.zero,
                    ),),

                const SizedBox(height: 24),

                // ── Auto Buy (coming soon) ──────────────────────────────────
                const _SectionHeader(
                  icon: Icons.auto_awesome,
                  title: 'Tự động mua',
                ),
                ListTile(
                  leading: const Icon(Icons.lock_outline,
                      color: AppColors.textSecondary,),
                  title: const Text('Cho phép AI đặt không cần xác nhận'),
                  subtitle: const Text('Sắp ra mắt'),
                  trailing: Chip(
                    label: const Text('Sắp ra mắt',
                        style: TextStyle(fontSize: 11),),
                    backgroundColor: AppColors.accent.withValues(alpha: 0.2),
                  ),
                  enabled: false,
                  contentPadding: EdgeInsets.zero,
                ),

                const SizedBox(height: 32),

                // ── Save Button ─────────────────────────────────────────────
                FilledButton.icon(
                  onPressed:
                      walletState.isSaving ? null : _save,
                  icon: walletState.isSaving
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.save),
                  label: const Text('Lưu cài đặt'),
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    minimumSize: const Size.fromHeight(48),
                  ),
                ),

                const SizedBox(height: 16),
              ],
            ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final IconData icon;
  final String title;
  const _SectionHeader({required this.icon, required this.title});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 18, color: AppColors.primary),
        const SizedBox(width: 8),
        Text(
          title,
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
        ),
        const SizedBox(width: 8),
        const Expanded(child: Divider()),
      ],
    );
  }
}
