import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../auth/domain/auth_state.dart';
import '../../memory/domain/memory_state.dart';
import '../../persona/domain/persona_state.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;

    return Scaffold(
      appBar: AppBar(title: const Text('Hồ sơ')),
      body: ListView(
        children: [
          // Header
          Container(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                CircleAvatar(
                  radius: 50,
                  backgroundColor: AppColors.primaryLight,
                  child: Text(
                    user?.name?.isNotEmpty == true
                        ? user!.name![0].toUpperCase()
                        : (user?.email.isNotEmpty == true
                            ? user!.email[0].toUpperCase()
                            : 'U'),
                    style: const TextStyle(
                      fontSize: 36,
                      color: AppColors.primary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  user?.name ?? 'Người dùng',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
                const SizedBox(height: 4),
                Text(
                  user?.email ?? '',
                  style: Theme.of(context)
                      .textTheme
                      .bodyMedium
                      ?.copyWith(color: AppColors.textSecondary),
                ),
              ],
            ),
          ),

          const Divider(),

          // ── AI Features ─────────────────────────────────────────────────
          _sectionHeader(context, 'Nhân vật & Trí nhớ AI'),
          const _PersonaMenuItem(),
          _item(
            context, Icons.add_circle_outline, 'Tạo nhân vật AI mới',
            () => context.push('/persona-form'),
            subtitle: 'Tùy chỉnh phong cách & prompt riêng',
            color: AppColors.primary,
          ),
          const _MemoryMenuItem(),

          const Divider(),

          // ── AI Shopping ─────────────────────────────────────────────────
          _sectionHeader(context, 'Mua sắm AI (AP2)'),
          _item(
            context, Icons.account_balance_wallet_outlined, 'Ví AI & Hạn mức',
            () => context.push('/agent-wallet'),
          ),
          _item(
            context, Icons.receipt_long_outlined, 'Đơn hàng AI',
            () => context.push('/orders'),
          ),
          _item(
            context, Icons.smart_toy_outlined, 'AP2 — Quy trình thanh toán AI',
            () => context.push('/ap2-flow'),
            subtitle: 'Xem cách AI mua sắm & cơ chế đồng thuận',
            color: AppColors.accent,
          ),

          const Divider(),

          // ── Navigation ───────────────────────────────────────────────────
          _sectionHeader(context, 'Điều hướng nhanh'),
          _item(
            context, Icons.chat_bubble, 'Chat với ChefGPT',
            () => context.go('/home'),
          ),
          _item(
            context, Icons.restaurant_menu, 'Gợi ý món ăn',
            () => context.go('/recipes'),
          ),
          _item(
            context, Icons.calendar_month, 'Kế hoạch bữa ăn',
            () => context.go('/mealplan'),
          ),
          _item(
            context, Icons.shopping_cart, 'Danh sách mua sắm',
            () => context.go('/grocery'),
          ),
          _item(
            context, Icons.people, 'Cộng đồng',
            () => context.go('/social'),
          ),

          const Divider(),

          ListTile(
            leading: const Icon(Icons.logout, color: AppColors.error),
            title: const Text(
              'Đăng xuất',
              style: TextStyle(color: AppColors.error),
            ),
            onTap: () => _confirmLogout(context, ref),
          ),

          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _sectionHeader(BuildContext context, String label) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 2),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.8,
            ),
      ),
    );
  }

  Widget _item(
    BuildContext context,
    IconData icon,
    String title,
    VoidCallback onTap, {
    String? subtitle,
    Color? color,
  }) {
    return ListTile(
      leading: Icon(icon, color: color ?? AppColors.textPrimary),
      title: Text(title),
      subtitle: subtitle != null
          ? Text(subtitle,
              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),)
          : null,
      trailing: const Icon(Icons.chevron_right),
      onTap: onTap,
    );
  }

  void _confirmLogout(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Đăng xuất'),
        content: const Text('Bạn có chắc muốn đăng xuất?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Huỷ'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              ref.read(authProvider.notifier).logout();
              context.go('/login');
            },
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
            child: const Text('Đăng xuất'),
          ),
        ],
      ),
    );
  }
}

class _PersonaMenuItem extends ConsumerWidget {
  const _PersonaMenuItem();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final persona = ref.watch(personaProvider).activePersona;
    final label = persona != null
        ? '${persona.icon} ${persona.name}'
        : '👨‍🍳 Chọn nhân vật';

    return ListTile(
      leading: const Icon(Icons.smart_toy_outlined, color: AppColors.primary),
      title: const Text('Nhân vật AI'),
      subtitle: Text(label, style: const TextStyle(fontSize: 13)),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => context.push('/persona-select'),
    );
  }
}

class _MemoryMenuItem extends ConsumerWidget {
  const _MemoryMenuItem();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final memories = ref.watch(memoryProvider).memories;
    final subtitle = memories.isEmpty
        ? 'ChefGPT chưa biết gì về bạn'
        : '${memories.length} thông tin đã lưu';

    return ListTile(
      leading: const Icon(Icons.psychology_outlined, color: AppColors.primary),
      title: const Text('Bộ nhớ AI'),
      subtitle: Text(subtitle, style: const TextStyle(fontSize: 13)),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => context.push('/memory'),
    );
  }
}
