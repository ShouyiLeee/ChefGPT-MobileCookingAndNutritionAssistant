/// AP2 Agentic Payment — Dart domain models.
/// Manual fromJson/toJson (no code generation).
library;

// ── CartMandate (AP2 Cart Mandate) ───────────────────────────────────────────

class CartMandateItem {
  final String productId;
  final String productName;
  final String productEmoji;
  final String unit;
  final int quantity;
  final double unitPrice;
  final double subtotal;

  const CartMandateItem({
    required this.productId,
    required this.productName,
    required this.productEmoji,
    required this.unit,
    required this.quantity,
    required this.unitPrice,
    required this.subtotal,
  });

  factory CartMandateItem.fromJson(Map<String, dynamic> json) => CartMandateItem(
        productId: json['product_id'] as String,
        productName: json['product_name'] as String,
        productEmoji: json['product_emoji'] as String? ?? '🛒',
        unit: json['unit'] as String? ?? 'phần',
        quantity: (json['quantity'] as num).toInt(),
        unitPrice: (json['unit_price'] as num).toDouble(),
        subtotal: (json['subtotal'] as num).toDouble(),
      );

  Map<String, dynamic> toJson() => {
        'product_id': productId,
        'product_name': productName,
        'product_emoji': productEmoji,
        'unit': unit,
        'quantity': quantity,
        'unit_price': unitPrice,
        'subtotal': subtotal,
      };
}

class CartMandate {
  final String storeId;
  final String storeName;
  final List<CartMandateItem> items;
  final double subtotal;
  final double deliveryFee;
  final double estimatedTotal;
  final String intentDescription;

  const CartMandate({
    required this.storeId,
    required this.storeName,
    required this.items,
    required this.subtotal,
    required this.deliveryFee,
    required this.estimatedTotal,
    this.intentDescription = '',
  });

  factory CartMandate.fromJson(Map<String, dynamic> json) => CartMandate(
        storeId: json['store_id'] as String,
        storeName: json['store_name'] as String,
        items: (json['items'] as List<dynamic>)
            .map((e) => CartMandateItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        subtotal: (json['subtotal'] as num).toDouble(),
        deliveryFee: (json['delivery_fee'] as num).toDouble(),
        estimatedTotal: (json['estimated_total'] as num).toDouble(),
        intentDescription: json['intent_description'] as String? ?? '',
      );

  Map<String, dynamic> toJson() => {
        'store_id': storeId,
        'store_name': storeName,
        'items': items.map((i) => i.toJson()).toList(),
        'subtotal': subtotal,
        'delivery_fee': deliveryFee,
        'estimated_total': estimatedTotal,
        'intent_description': intentDescription,
      };
}

// ── Shopping Suggestion ───────────────────────────────────────────────────────

class ShoppingSuggestion {
  final CartMandate cartMandate;
  final double estimatedTotal;
  final bool requiresConfirmation;
  final int? mandateId;

  const ShoppingSuggestion({
    required this.cartMandate,
    required this.estimatedTotal,
    this.requiresConfirmation = true,
    this.mandateId,
  });

  factory ShoppingSuggestion.fromJson(Map<String, dynamic> json) =>
      ShoppingSuggestion(
        cartMandate:
            CartMandate.fromJson(json['cart_mandate'] as Map<String, dynamic>),
        estimatedTotal: (json['estimated_total'] as num).toDouble(),
        requiresConfirmation: json['requires_confirmation'] as bool? ?? true,
        mandateId: json['mandate_id'] as int?,
      );
}

// ── Agent Order ───────────────────────────────────────────────────────────────

class OrderItemModel {
  final String productId;
  final String productName;
  final String productEmoji;
  final int quantity;
  final String unit;
  final double unitPrice;
  final double subtotal;

  const OrderItemModel({
    required this.productId,
    required this.productName,
    required this.productEmoji,
    required this.quantity,
    required this.unit,
    required this.unitPrice,
    required this.subtotal,
  });

  factory OrderItemModel.fromJson(Map<String, dynamic> json) => OrderItemModel(
        productId: json['product_id'] as String,
        productName: json['product_name'] as String,
        productEmoji: json['product_emoji'] as String? ?? '🛒',
        quantity: (json['quantity'] as num).toInt(),
        unit: json['unit'] as String? ?? 'phần',
        unitPrice: (json['unit_price'] as num).toDouble(),
        subtotal: (json['subtotal'] as num).toDouble(),
      );
}

class AgentOrder {
  final int id;
  final String storeId;
  final String storeName;
  final String status;
  final double subtotal;
  final double deliveryFee;
  final double total;
  final String paymentMethod;
  final String? transactionId;
  final String? intentDescription;
  final List<OrderItemModel> items;
  final DateTime createdAt;

  const AgentOrder({
    required this.id,
    required this.storeId,
    required this.storeName,
    required this.status,
    required this.subtotal,
    required this.deliveryFee,
    required this.total,
    required this.paymentMethod,
    this.transactionId,
    this.intentDescription,
    required this.items,
    required this.createdAt,
  });

  factory AgentOrder.fromJson(Map<String, dynamic> json) => AgentOrder(
        id: json['id'] as int,
        storeId: json['store_id'] as String,
        storeName: json['store_name'] as String,
        status: json['status'] as String,
        subtotal: (json['subtotal'] as num).toDouble(),
        deliveryFee: (json['delivery_fee'] as num).toDouble(),
        total: (json['total'] as num).toDouble(),
        paymentMethod: json['payment_method'] as String,
        transactionId: json['transaction_id'] as String?,
        intentDescription: json['intent_description'] as String?,
        items: (json['items'] as List<dynamic>)
            .map((e) => OrderItemModel.fromJson(e as Map<String, dynamic>))
            .toList(),
        createdAt: DateTime.parse(json['created_at'] as String),
      );
}

// ── Payment Mandate Model ─────────────────────────────────────────────────────

class PaymentMandateModel {
  final int id;
  final String paymentMethod;
  final double spendingLimit;
  final List<String> preferredStoreIds;
  final bool autoBuyEnabled;

  const PaymentMandateModel({
    required this.id,
    required this.paymentMethod,
    required this.spendingLimit,
    required this.preferredStoreIds,
    required this.autoBuyEnabled,
  });

  factory PaymentMandateModel.fromJson(Map<String, dynamic> json) =>
      PaymentMandateModel(
        id: json['id'] as int,
        paymentMethod: json['payment_method'] as String,
        spendingLimit: (json['spending_limit'] as num).toDouble(),
        preferredStoreIds: (json['preferred_store_ids'] as List<dynamic>)
            .map((e) => e as String)
            .toList(),
        autoBuyEnabled: json['auto_buy_enabled'] as bool? ?? false,
      );

  Map<String, dynamic> toJson() => {
        'payment_method': paymentMethod,
        'spending_limit': spendingLimit,
        'preferred_store_ids': preferredStoreIds,
        'auto_buy_enabled': autoBuyEnabled,
      };
}
