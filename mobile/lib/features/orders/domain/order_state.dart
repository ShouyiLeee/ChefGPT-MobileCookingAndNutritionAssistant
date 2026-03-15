import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_service.dart';
import 'order_models.dart';

// ── Order History ──────────────────────────────────────────────────────────

class OrderHistoryState {
  final List<AgentOrder> orders;
  final bool isLoading;
  final String? error;

  const OrderHistoryState({
    this.orders = const [],
    this.isLoading = false,
    this.error,
  });

  OrderHistoryState copyWith({
    List<AgentOrder>? orders,
    bool? isLoading,
    String? error,
  }) =>
      OrderHistoryState(
        orders: orders ?? this.orders,
        isLoading: isLoading ?? this.isLoading,
        error: error,
      );
}

class OrderHistoryNotifier extends StateNotifier<OrderHistoryState> {
  final ApiService _api;

  OrderHistoryNotifier(this._api) : super(const OrderHistoryState());

  Future<void> load() async {
    state = state.copyWith(isLoading: true);
    try {
      final data = await _api.getOrders();
      final orders = data
          .map((e) => AgentOrder.fromJson(e as Map<String, dynamic>))
          .toList();
      state = state.copyWith(orders: orders, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: ApiService.parseError(e));
    }
  }

  Future<void> cancel(int orderId) async {
    // Optimistic update
    final prev = state.orders;
    state = state.copyWith(
      orders: prev
          .map((o) => o.id == orderId ? _withStatus(o, 'cancelled') : o)
          .toList(),
    );
    try {
      await _api.cancelOrder(orderId);
    } catch (_) {
      // Rollback on failure
      state = state.copyWith(orders: prev);
    }
  }

  AgentOrder _withStatus(AgentOrder o, String status) => AgentOrder(
        id: o.id,
        storeId: o.storeId,
        storeName: o.storeName,
        status: status,
        subtotal: o.subtotal,
        deliveryFee: o.deliveryFee,
        total: o.total,
        paymentMethod: o.paymentMethod,
        transactionId: o.transactionId,
        intentDescription: o.intentDescription,
        items: o.items,
        createdAt: o.createdAt,
      );
}

final orderHistoryProvider =
    StateNotifierProvider<OrderHistoryNotifier, OrderHistoryState>((ref) {
  final api = ref.read(apiServiceProvider);
  return OrderHistoryNotifier(api);
});

// ── Agent Wallet (Payment Mandate) ────────────────────────────────────────

class AgentWalletState {
  final PaymentMandateModel? mandate;
  final bool isLoading;
  final bool isSaving;
  final String? error;

  const AgentWalletState({
    this.mandate,
    this.isLoading = false,
    this.isSaving = false,
    this.error,
  });

  AgentWalletState copyWith({
    PaymentMandateModel? mandate,
    bool? isLoading,
    bool? isSaving,
    String? error,
  }) =>
      AgentWalletState(
        mandate: mandate ?? this.mandate,
        isLoading: isLoading ?? this.isLoading,
        isSaving: isSaving ?? this.isSaving,
        error: error,
      );
}

class AgentWalletNotifier extends StateNotifier<AgentWalletState> {
  final ApiService _api;

  AgentWalletNotifier(this._api) : super(const AgentWalletState());

  Future<void> load() async {
    state = state.copyWith(isLoading: true);
    try {
      final data = await _api.getPaymentMandate();
      state = state.copyWith(
        mandate: PaymentMandateModel.fromJson(data),
        isLoading: false,
      );
    } catch (e) {
      // 404 means no mandate yet — not an error state
      final msg = ApiService.parseError(e);
      if (msg.contains('404') || msg.contains('Chưa thiết lập')) {
        state = state.copyWith(isLoading: false);
      } else {
        state = state.copyWith(isLoading: false, error: msg);
      }
    }
  }

  Future<bool> save(PaymentMandateModel m) async {
    state = state.copyWith(isSaving: true);
    try {
      final data = await _api.savePaymentMandate(m.toJson());
      state = state.copyWith(
        mandate: PaymentMandateModel.fromJson(data),
        isSaving: false,
      );
      return true;
    } catch (e) {
      state = state.copyWith(
        isSaving: false,
        error: ApiService.parseError(e),
      );
      return false;
    }
  }
}

final agentWalletProvider =
    StateNotifierProvider<AgentWalletNotifier, AgentWalletState>((ref) {
  final api = ref.read(apiServiceProvider);
  return AgentWalletNotifier(api);
});
