import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

// ═══════════════════════════════════════════════════════════════════════════════
// MODELS
// ═══════════════════════════════════════════════════════════════════════════════

class _Store {
  final String id;
  final String name;
  final String tagline;
  final Color primary;
  final Color dark;
  final String emoji;
  final String deliveryTime;
  final int minOrder;
  final double deliveryFee;
  const _Store({
    required this.id, required this.name, required this.tagline,
    required this.primary, required this.dark, required this.emoji,
    required this.deliveryTime, required this.minOrder, required this.deliveryFee,
  });
}

class _Product {
  final String id;
  final String name;
  final double price;
  final double? originalPrice;
  final String unit;
  final String emoji;
  final String category;
  final String storeId;
  const _Product({
    required this.id, required this.name, required this.price,
    this.originalPrice, required this.unit, required this.emoji,
    required this.category, required this.storeId,
  });
  int get discount => originalPrice != null
      ? ((originalPrice! - price) / originalPrice! * 100).round() : 0;
}

class _CartItem {
  final _Product product;
  final int qty;
  const _CartItem({required this.product, required this.qty});
  _CartItem withQty(int q) => _CartItem(product: product, qty: q);
  double get subtotal => product.price * qty;
}

// ═══════════════════════════════════════════════════════════════════════════════
// MOCK DATA
// ═══════════════════════════════════════════════════════════════════════════════

const _stores = [
  _Store(id: 'bhx', name: 'Bách Hóa Xanh', tagline: 'Tươi ngon mỗi ngày',
      primary: Color(0xFF00A651), dark: Color(0xFF007A3D), emoji: '🟢',
      deliveryTime: '30–45 phút', minOrder: 150, deliveryFee: 15),
  _Store(id: 'winmart', name: 'WinMart', tagline: 'Giá tốt, chất lượng cao',
      primary: Color(0xFFE31837), dark: Color(0xFFAA0F27), emoji: '🛒',
      deliveryTime: '45–60 phút', minOrder: 200, deliveryFee: 20),
  _Store(id: 'coopmart', name: 'Co.opMart', tagline: 'Lợi ích hội viên',
      primary: Color(0xFF004B8D), dark: Color(0xFF003366), emoji: '🔵',
      deliveryTime: '60–90 phút', minOrder: 250, deliveryFee: 25),
  _Store(id: 'lotte', name: 'Lotte Mart', tagline: 'Shopping vui hơn',
      primary: Color(0xFFD40A10), dark: Color(0xFF9E070C), emoji: '🛍️',
      deliveryTime: '45–60 phút', minOrder: 200, deliveryFee: 18),
  _Store(id: 'bigc', name: 'Go! / Big C', tagline: 'Đa dạng hàng hóa',
      primary: Color(0xFFF7941D), dark: Color(0xFFCC7700), emoji: '🧺',
      deliveryTime: '30–45 phút', minOrder: 150, deliveryFee: 15),
];

const _categories = ['Tất cả', 'Rau củ', 'Thịt & Cá', 'Trứng & Sữa', 'Đồ khô', 'Đồ uống', 'Bánh kẹo'];

const _allProducts = [
  // Bách Hóa Xanh
  _Product(id: 'b1', name: 'Cải ngọt', price: 5, unit: 'bó', emoji: '🥬', category: 'Rau củ', storeId: 'bhx'),
  _Product(id: 'b2', name: 'Cà chua', price: 15, originalPrice: 20, unit: 'kg', emoji: '🍅', category: 'Rau củ', storeId: 'bhx'),
  _Product(id: 'b3', name: 'Dưa leo', price: 8, unit: 'kg', emoji: '🥒', category: 'Rau củ', storeId: 'bhx'),
  _Product(id: 'b4', name: 'Thịt ba chỉ', price: 85, originalPrice: 95, unit: 'kg', emoji: '🥩', category: 'Thịt & Cá', storeId: 'bhx'),
  _Product(id: 'b5', name: 'Gà ta nguyên con', price: 110, unit: 'con ~1.2kg', emoji: '🍗', category: 'Thịt & Cá', storeId: 'bhx'),
  _Product(id: 'b6', name: 'Cá basa phi lê', price: 55, unit: 'kg', emoji: '🐟', category: 'Thịt & Cá', storeId: 'bhx'),
  _Product(id: 'b7', name: 'Trứng gà ta', price: 35, unit: '10 quả', emoji: '🥚', category: 'Trứng & Sữa', storeId: 'bhx'),
  _Product(id: 'b8', name: 'Sữa tươi Vinamilk', price: 28, unit: 'lít', emoji: '🥛', category: 'Trứng & Sữa', storeId: 'bhx'),
  _Product(id: 'b9', name: 'Gạo ST25', price: 35, unit: 'kg', emoji: '🍚', category: 'Đồ khô', storeId: 'bhx'),
  _Product(id: 'b10', name: 'Nước mắm Nam Ngư', price: 25, originalPrice: 30, unit: 'chai', emoji: '🫙', category: 'Đồ khô', storeId: 'bhx'),
  _Product(id: 'b11', name: 'Nước suối Aquafina', price: 8, unit: 'chai 1.5L', emoji: '💧', category: 'Đồ uống', storeId: 'bhx'),
  _Product(id: 'b12', name: 'Bánh quy Oreo', price: 22, unit: 'hộp', emoji: '🍪', category: 'Bánh kẹo', storeId: 'bhx'),

  // WinMart
  _Product(id: 'w1', name: 'Rau muống', price: 5, unit: 'bó', emoji: '🌿', category: 'Rau củ', storeId: 'winmart'),
  _Product(id: 'w2', name: 'Cà rốt Đà Lạt', price: 12, originalPrice: 18, unit: 'kg', emoji: '🥕', category: 'Rau củ', storeId: 'winmart'),
  _Product(id: 'w3', name: 'Khoai tây', price: 20, unit: 'kg', emoji: '🥔', category: 'Rau củ', storeId: 'winmart'),
  _Product(id: 'w4', name: 'Thịt bò Mỹ', price: 180, originalPrice: 220, unit: 'kg', emoji: '🥩', category: 'Thịt & Cá', storeId: 'winmart'),
  _Product(id: 'w5', name: 'Cá hồi Na Uy', price: 95, unit: '100g', emoji: '🐠', category: 'Thịt & Cá', storeId: 'winmart'),
  _Product(id: 'w6', name: 'Tôm thẻ đông lạnh', price: 120, unit: 'kg', emoji: '🦐', category: 'Thịt & Cá', storeId: 'winmart'),
  _Product(id: 'w7', name: 'Sữa TH True Milk', price: 32, unit: 'lít', emoji: '🥛', category: 'Trứng & Sữa', storeId: 'winmart'),
  _Product(id: 'w8', name: 'Phô mai Président', price: 65, originalPrice: 80, unit: 'hộp 200g', emoji: '🧀', category: 'Trứng & Sữa', storeId: 'winmart'),
  _Product(id: 'w9', name: 'Dầu ăn Neptune', price: 45, originalPrice: 55, unit: 'chai 1L', emoji: '🫗', category: 'Đồ khô', storeId: 'winmart'),
  _Product(id: 'w10', name: 'Mì ý Barilla', price: 38, unit: 'gói 500g', emoji: '🍝', category: 'Đồ khô', storeId: 'winmart'),
  _Product(id: 'w11', name: 'Trà xanh 0 độ', price: 12, unit: 'chai 500ml', emoji: '🍵', category: 'Đồ uống', storeId: 'winmart'),
  _Product(id: 'w12', name: 'Socola KitKat', price: 25, unit: 'thanh', emoji: '🍫', category: 'Bánh kẹo', storeId: 'winmart'),

  // Co.opMart
  _Product(id: 'c1', name: 'Súp lơ xanh', price: 18, originalPrice: 25, unit: 'kg', emoji: '🥦', category: 'Rau củ', storeId: 'coopmart'),
  _Product(id: 'c2', name: 'Hành tây', price: 10, unit: 'kg', emoji: '🧅', category: 'Rau củ', storeId: 'coopmart'),
  _Product(id: 'c3', name: 'Nấm đông cô', price: 35, originalPrice: 45, unit: 'kg', emoji: '🍄', category: 'Rau củ', storeId: 'coopmart'),
  _Product(id: 'c4', name: 'Sườn non', price: 95, unit: 'kg', emoji: '🍖', category: 'Thịt & Cá', storeId: 'coopmart'),
  _Product(id: 'c5', name: 'Bạch tuộc tươi', price: 75, originalPrice: 90, unit: 'kg', emoji: '🐙', category: 'Thịt & Cá', storeId: 'coopmart'),
  _Product(id: 'c6', name: 'Trứng vịt', price: 40, unit: '10 quả', emoji: '🥚', category: 'Trứng & Sữa', storeId: 'coopmart'),
  _Product(id: 'c7', name: 'Nước mắm Phú Quốc', price: 42, originalPrice: 50, unit: 'chai 500ml', emoji: '🫙', category: 'Đồ khô', storeId: 'coopmart'),
  _Product(id: 'c8', name: 'Tương ớt Chinsu', price: 20, unit: 'chai 250g', emoji: '🌶️', category: 'Đồ khô', storeId: 'coopmart'),
  _Product(id: 'c9', name: 'Coca Cola', price: 15, unit: 'lon 330ml', emoji: '🥤', category: 'Đồ uống', storeId: 'coopmart'),
  _Product(id: 'c10', name: 'Nước cam ép', price: 35, originalPrice: 45, unit: 'chai 1L', emoji: '🍊', category: 'Đồ uống', storeId: 'coopmart'),
  _Product(id: 'c11', name: 'Kẹo dẻo Trolli', price: 28, unit: 'gói', emoji: '🍬', category: 'Bánh kẹo', storeId: 'coopmart'),
  _Product(id: 'c12', name: 'Bánh bông lan', price: 22, unit: 'hộp', emoji: '🧁', category: 'Bánh kẹo', storeId: 'coopmart'),

  // Lotte Mart
  _Product(id: 'l1', name: 'Kimchi cải thảo', price: 45, unit: 'kg', emoji: '🥗', category: 'Rau củ', storeId: 'lotte'),
  _Product(id: 'l2', name: 'Tỏi Hàn Quốc', price: 30, originalPrice: 40, unit: 'kg', emoji: '🧄', category: 'Rau củ', storeId: 'lotte'),
  _Product(id: 'l3', name: 'Thịt bò Hàn', price: 220, originalPrice: 260, unit: 'kg', emoji: '🥩', category: 'Thịt & Cá', storeId: 'lotte'),
  _Product(id: 'l4', name: 'Bạch tuộc HQ', price: 90, unit: 'kg', emoji: '🐙', category: 'Thịt & Cá', storeId: 'lotte'),
  _Product(id: 'l5', name: 'Trứng tươi HQ', price: 55, unit: 'hộp 10 quả', emoji: '🥚', category: 'Trứng & Sữa', storeId: 'lotte'),
  _Product(id: 'l6', name: 'Sữa chua Yoplait', price: 18, unit: 'hộp', emoji: '🫙', category: 'Trứng & Sữa', storeId: 'lotte'),
  _Product(id: 'l7', name: 'Mì Shin Ramyun', price: 25, originalPrice: 32, unit: 'gói', emoji: '🍜', category: 'Đồ khô', storeId: 'lotte'),
  _Product(id: 'l8', name: 'Tương Gochujang', price: 55, unit: 'hộp', emoji: '🌶️', category: 'Đồ khô', storeId: 'lotte'),
  _Product(id: 'l9', name: 'Ion Water HK', price: 22, unit: 'chai 900ml', emoji: '💧', category: 'Đồ uống', storeId: 'lotte'),
  _Product(id: 'l10', name: 'Bánh gạo Hàn Quốc', price: 35, originalPrice: 45, unit: 'gói', emoji: '🍘', category: 'Bánh kẹo', storeId: 'lotte'),

  // Go! / Big C
  _Product(id: 'g1', name: 'Ớt chuông', price: 28, originalPrice: 35, unit: 'kg', emoji: '🫑', category: 'Rau củ', storeId: 'bigc'),
  _Product(id: 'g2', name: 'Bắp ngô', price: 10, unit: '2 trái', emoji: '🌽', category: 'Rau củ', storeId: 'bigc'),
  _Product(id: 'g3', name: 'Thịt gà đùi', price: 75, unit: 'kg', emoji: '🍗', category: 'Thịt & Cá', storeId: 'bigc'),
  _Product(id: 'g4', name: 'Cá ngừ đóng hộp', price: 28, unit: 'hộp 185g', emoji: '🐟', category: 'Thịt & Cá', storeId: 'bigc'),
  _Product(id: 'g5', name: 'Sữa chua Vinamilk', price: 15, unit: 'hộp', emoji: '🫙', category: 'Trứng & Sữa', storeId: 'bigc'),
  _Product(id: 'g6', name: 'Bơ Anchor', price: 55, originalPrice: 68, unit: 'hộp 200g', emoji: '🧈', category: 'Trứng & Sữa', storeId: 'bigc'),
  _Product(id: 'g7', name: 'Mì tôm Hảo Hảo', price: 5, unit: 'gói', emoji: '🍜', category: 'Đồ khô', storeId: 'bigc'),
  _Product(id: 'g8', name: 'Dầu hào Maggi', price: 32, originalPrice: 38, unit: 'chai', emoji: '🫗', category: 'Đồ khô', storeId: 'bigc'),
  _Product(id: 'g9', name: 'Bia Tiger', price: 22, unit: 'lon 330ml', emoji: '🍺', category: 'Đồ uống', storeId: 'bigc'),
  _Product(id: 'g10', name: 'Pepsi 1.5L', price: 13, originalPrice: 18, unit: 'chai', emoji: '🥤', category: 'Đồ uống', storeId: 'bigc'),
  _Product(id: 'g11', name: 'Snack Pringles', price: 38, unit: 'hộp', emoji: '🍟', category: 'Bánh kẹo', storeId: 'bigc'),
  _Product(id: 'g12', name: 'Kẹo Halls', price: 12, originalPrice: 15, unit: 'hộp', emoji: '🍬', category: 'Bánh kẹo', storeId: 'bigc'),
];

// ═══════════════════════════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════════════════════════

class _ShopState {
  final _Store? store;
  final String category;
  final List<_CartItem> cart;
  const _ShopState({this.store, this.category = 'Tất cả', this.cart = const []});

  _ShopState copyWith({_Store? store, bool clearStore = false, String? category, List<_CartItem>? cart}) =>
      _ShopState(
        store: clearStore ? null : store ?? this.store,
        category: category ?? this.category,
        cart: cart ?? this.cart,
      );

  int get cartCount => cart.fold(0, (s, c) => s + c.qty);
  double get cartTotal => cart.fold(0.0, (s, c) => s + c.subtotal);
  int qtyOf(String id) {
    final i = cart.indexWhere((c) => c.product.id == id);
    return i >= 0 ? cart[i].qty : 0;
  }
}

class _ShopNotifier extends StateNotifier<_ShopState> {
  _ShopNotifier() : super(const _ShopState());

  void selectStore(_Store s) => state = state.copyWith(store: s, category: 'Tất cả');
  void backToStores() => state = state.copyWith(clearStore: true);
  void setCategory(String c) => state = state.copyWith(category: c);

  void add(_Product p) {
    final cart = [...state.cart];
    final i = cart.indexWhere((c) => c.product.id == p.id);
    if (i >= 0) {
      cart[i] = cart[i].withQty(cart[i].qty + 1);
    } else {
      cart.add(_CartItem(product: p, qty: 1));
    }
    state = state.copyWith(cart: cart);
  }

  void remove(_Product p) {
    final cart = [...state.cart];
    final i = cart.indexWhere((c) => c.product.id == p.id);
    if (i < 0) return;
    if (cart[i].qty <= 1) {
      cart.removeAt(i);
    } else {
      cart[i] = cart[i].withQty(cart[i].qty - 1);
    }
    state = state.copyWith(cart: cart);
  }

  void clearCart() => state = state.copyWith(cart: []);
}

final _shopProvider =
    StateNotifierProvider<_ShopNotifier, _ShopState>((_) => _ShopNotifier());

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN SCREEN
// ═══════════════════════════════════════════════════════════════════════════════

class GroceryScreen extends ConsumerWidget {
  const GroceryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final st = ref.watch(_shopProvider);
    return Scaffold(
      backgroundColor: const Color(0xFFF5F5F7),
      body: AnimatedSwitcher(
        duration: const Duration(milliseconds: 380),
        transitionBuilder: (child, anim) => FadeTransition(
          opacity: anim,
          child: SlideTransition(
            position: Tween(begin: const Offset(0.06, 0), end: Offset.zero)
                .animate(CurvedAnimation(parent: anim, curve: Curves.easeOutCubic)),
            child: child,
          ),
        ),
        child: st.store == null
            ? const _StoreListView(key: ValueKey('stores'))
            : _ProductsView(key: ValueKey(st.store!.id)),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// STORE SELECTION
// ═══════════════════════════════════════════════════════════════════════════════

class _StoreListView extends ConsumerWidget {
  const _StoreListView({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return CustomScrollView(
      slivers: [
        SliverToBoxAdapter(
          child: Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFF1A1A2E), Color(0xFF16213E)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
            padding: EdgeInsets.fromLTRB(20, MediaQuery.of(context).padding.top + 16, 20, 28),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Text('🛒', style: TextStyle(fontSize: 26)),
                  ),
                  const SizedBox(width: 14),
                  Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
                    Text('Mua sắm', style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
                    Text('Giao tận nhà trong 1 giờ', style: TextStyle(color: Colors.white60, fontSize: 13)),
                  ]),
                ]),
                const SizedBox(height: 20),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.09),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.white.withOpacity(0.15)),
                  ),
                  child: Row(children: const [
                    Icon(Icons.location_on_rounded, color: Color(0xFF4CAF50), size: 18),
                    SizedBox(width: 8),
                    Text('123 Nguyễn Văn Linh, Q.7, TP.HCM',
                        style: TextStyle(color: Colors.white70, fontSize: 13)),
                  ]),
                ),
              ],
            ),
          ),
        ),
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(16, 20, 16, 8),
          sliver: SliverToBoxAdapter(
            child: Text('Chọn cửa hàng',
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: Colors.grey.shade800)),
          ),
        ),
        SliverPadding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          sliver: SliverGrid(
            delegate: SliverChildBuilderDelegate(
              (ctx, i) => _StoreCard(store: _stores[i]),
              childCount: _stores.length,
            ),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              mainAxisSpacing: 14,
              crossAxisSpacing: 14,
              childAspectRatio: 0.82,
            ),
          ),
        ),
        const SliverToBoxAdapter(child: SizedBox(height: 32)),
      ],
    );
  }
}

class _StoreCard extends ConsumerStatefulWidget {
  final _Store store;
  const _StoreCard({required this.store});

  @override
  ConsumerState<_StoreCard> createState() => _StoreCardState();
}

class _StoreCardState extends ConsumerState<_StoreCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 120));
    _scale = Tween(begin: 1.0, end: 0.94).animate(
        CurvedAnimation(parent: _ctrl, curve: Curves.easeIn));
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.store;
    return GestureDetector(
      onTapDown: (_) => _ctrl.forward(),
      onTapUp: (_) async {
        await _ctrl.reverse();
        if (!mounted) return;
        HapticFeedback.lightImpact();
        ref.read(_shopProvider.notifier).selectStore(s);
      },
      onTapCancel: () => _ctrl.reverse(),
      child: ScaleTransition(
        scale: _scale,
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            gradient: LinearGradient(
              colors: [s.primary, s.dark],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            boxShadow: [
              BoxShadow(color: s.primary.withOpacity(0.35), blurRadius: 16, offset: const Offset(0, 8)),
            ],
          ),
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(s.emoji, style: const TextStyle(fontSize: 38)),
              const Spacer(),
              Text(s.name,
                  style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.bold),
                  maxLines: 2),
              const SizedBox(height: 4),
              Text(s.tagline,
                  style: TextStyle(color: Colors.white.withOpacity(0.75), fontSize: 11),
                  maxLines: 1, overflow: TextOverflow.ellipsis),
              const SizedBox(height: 10),
              Wrap(spacing: 6, runSpacing: 4, children: [
                _InfoBadge(Icons.delivery_dining_rounded, s.deliveryTime),
                _InfoBadge(Icons.shopping_bag_outlined, 'Min ${s.minOrder}k'),
              ]),
            ],
          ),
        ),
      ),
    );
  }
}

class _InfoBadge extends StatelessWidget {
  final IconData icon;
  final String text;
  const _InfoBadge(this.icon, this.text);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.2),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 11, color: Colors.white.withOpacity(0.9)),
        const SizedBox(width: 4),
        Text(text, style: TextStyle(fontSize: 10, color: Colors.white.withOpacity(0.9))),
      ]),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// PRODUCTS VIEW
// ═══════════════════════════════════════════════════════════════════════════════

class _ProductsView extends ConsumerStatefulWidget {
  const _ProductsView({super.key});

  @override
  ConsumerState<_ProductsView> createState() => _ProductsViewState();
}

class _ProductsViewState extends ConsumerState<_ProductsView> {
  @override
  Widget build(BuildContext context) {
    final st = ref.watch(_shopProvider);
    final store = st.store!;
    final products = _allProducts
        .where((p) => p.storeId == store.id && (st.category == 'Tất cả' || p.category == st.category))
        .toList();

    return Stack(
      children: [
        CustomScrollView(
          slivers: [
            _StoreHeader(store: store),
            SliverPersistentHeader(
              pinned: true,
              delegate: _CategoryHeaderDelegate(store: store),
            ),
            products.isEmpty
                ? SliverFillRemaining(
                    child: Center(
                      child: Column(mainAxisSize: MainAxisSize.min, children: [
                        const Text('😕', style: TextStyle(fontSize: 48)),
                        const SizedBox(height: 12),
                        Text('Không có sản phẩm', style: TextStyle(color: Colors.grey.shade500)),
                      ]),
                    ),
                  )
                : SliverPadding(
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 120),
                    sliver: SliverGrid(
                      delegate: SliverChildBuilderDelegate(
                        (ctx, i) => _ProductCard(product: products[i], store: store),
                        childCount: products.length,
                      ),
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2,
                        mainAxisSpacing: 14,
                        crossAxisSpacing: 14,
                        childAspectRatio: 0.72,
                      ),
                    ),
                  ),
          ],
        ),
        // Floating cart bar
        Positioned(
          bottom: 0, left: 0, right: 0,
          child: _CartBar(store: store),
        ),
      ],
    );
  }
}

class _StoreHeader extends ConsumerWidget {
  final _Store store;
  const _StoreHeader({required this.store});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SliverToBoxAdapter(
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [store.primary, store.dark],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        padding: EdgeInsets.fromLTRB(16, MediaQuery.of(context).padding.top + 10, 16, 20),
        child: Row(children: [
          GestureDetector(
            onTap: () {
              HapticFeedback.selectionClick();
              ref.read(_shopProvider.notifier).backToStores();
            },
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white, size: 18),
            ),
          ),
          const SizedBox(width: 14),
          Text(store.emoji, style: const TextStyle(fontSize: 28)),
          const SizedBox(width: 10),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(store.name,
                  style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
              Text('${store.deliveryTime} • Phí ship ${store.deliveryFee.toInt()}k',
                  style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 12)),
            ]),
          ),
        ]),
      ),
    );
  }
}

class _CategoryHeaderDelegate extends SliverPersistentHeaderDelegate {
  final _Store store;
  _CategoryHeaderDelegate({required this.store});

  @override
  double get minExtent => 56;
  @override
  double get maxExtent => 56;

  @override
  Widget build(BuildContext context, double shrinkOffset, bool overlapsContent) {
    return Consumer(builder: (ctx, ref, _) {
      final selected = ref.watch(_shopProvider).category;
      return Container(
        color: Colors.white,
        child: ListView.separated(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          itemCount: _categories.length,
          separatorBuilder: (_, __) => const SizedBox(width: 8),
          itemBuilder: (_, i) {
            final cat = _categories[i];
            final active = cat == selected;
            return GestureDetector(
              onTap: () {
                HapticFeedback.selectionClick();
                ref.read(_shopProvider.notifier).setCategory(cat);
              },
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                decoration: BoxDecoration(
                  color: active ? store.primary : Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(20),
                  border: active ? null : Border.all(color: Colors.grey.shade200),
                ),
                child: Text(cat,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: active ? FontWeight.w600 : FontWeight.normal,
                      color: active ? Colors.white : Colors.grey.shade700,
                    )),
              ),
            );
          },
        ),
      );
    });
  }

  @override
  bool shouldRebuild(_CategoryHeaderDelegate old) => old.store.id != store.id;
}

// ═══════════════════════════════════════════════════════════════════════════════
// PRODUCT CARD
// ═══════════════════════════════════════════════════════════════════════════════

class _ProductCard extends ConsumerStatefulWidget {
  final _Product product;
  final _Store store;
  const _ProductCard({required this.product, required this.store});

  @override
  ConsumerState<_ProductCard> createState() => _ProductCardState();
}

class _ProductCardState extends ConsumerState<_ProductCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _bounce;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 350));
    _bounce = TweenSequence([
      TweenSequenceItem(tween: Tween(begin: 1.0, end: 1.25), weight: 40),
      TweenSequenceItem(tween: Tween(begin: 1.25, end: 0.9), weight: 30),
      TweenSequenceItem(tween: Tween(begin: 0.9, end: 1.0), weight: 30),
    ]).animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  void _onAdd() {
    HapticFeedback.lightImpact();
    _ctrl.forward(from: 0);
    ref.read(_shopProvider.notifier).add(widget.product);
  }

  @override
  Widget build(BuildContext context) {
    final qty = ref.watch(_shopProvider).qtyOf(widget.product.id);
    final p = widget.product;

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 12, offset: const Offset(0, 4))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Product image area
          Expanded(
            flex: 5,
            child: Container(
              decoration: BoxDecoration(
                color: widget.store.primary.withOpacity(0.06),
                borderRadius: const BorderRadius.vertical(top: Radius.circular(18)),
              ),
              child: Stack(
                children: [
                  Center(child: Text(p.emoji, style: const TextStyle(fontSize: 52))),
                  if (p.discount > 0)
                    Positioned(
                      top: 8, right: 8,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                        decoration: BoxDecoration(
                          color: Colors.red.shade500,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text('-${p.discount}%',
                            style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold)),
                      ),
                    ),
                ],
              ),
            ),
          ),
          // Info area
          Expanded(
            flex: 6,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(p.name,
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                      maxLines: 2, overflow: TextOverflow.ellipsis),
                  const SizedBox(height: 2),
                  Text(p.unit, style: TextStyle(fontSize: 11, color: Colors.grey.shade500)),
                  const Spacer(),
                  Row(children: [
                    Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text('${p.price.toInt()}k',
                          style: TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.bold,
                              color: widget.store.primary)),
                      if (p.originalPrice != null)
                        Text('${p.originalPrice!.toInt()}k',
                            style: TextStyle(
                                fontSize: 11,
                                color: Colors.grey.shade400,
                                decoration: TextDecoration.lineThrough)),
                    ]),
                    const Spacer(),
                    qty == 0
                        ? ScaleTransition(
                            scale: _bounce,
                            child: GestureDetector(
                              onTap: _onAdd,
                              child: Container(
                                width: 34, height: 34,
                                decoration: BoxDecoration(
                                  color: widget.store.primary,
                                  shape: BoxShape.circle,
                                  boxShadow: [BoxShadow(
                                      color: widget.store.primary.withOpacity(0.4),
                                      blurRadius: 8, offset: const Offset(0, 3))],
                                ),
                                child: const Icon(Icons.add, color: Colors.white, size: 20),
                              ),
                            ),
                          )
                        : _QtyControl(
                            qty: qty,
                            color: widget.store.primary,
                            onAdd: _onAdd,
                            onRemove: () {
                              HapticFeedback.selectionClick();
                              ref.read(_shopProvider.notifier).remove(p);
                            },
                          ),
                  ]),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _QtyControl extends StatelessWidget {
  final int qty;
  final Color color;
  final VoidCallback onAdd;
  final VoidCallback onRemove;
  const _QtyControl({required this.qty, required this.color, required this.onAdd, required this.onRemove});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 32,
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        _Btn(icon: Icons.remove, onTap: onRemove, color: color),
        AnimatedSwitcher(
          duration: const Duration(milliseconds: 180),
          transitionBuilder: (child, anim) => ScaleTransition(scale: anim, child: child),
          child: Text('$qty',
              key: ValueKey(qty),
              style: TextStyle(fontWeight: FontWeight.bold, color: color, fontSize: 14)),
        ),
        _Btn(icon: Icons.add, onTap: onAdd, color: color),
      ]),
    );
  }
}

class _Btn extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  final Color color;
  const _Btn({required this.icon, required this.onTap, required this.color});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
        child: Icon(icon, size: 16, color: color),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// CART BAR
// ═══════════════════════════════════════════════════════════════════════════════

class _CartBar extends ConsumerWidget {
  final _Store store;
  const _CartBar({required this.store});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final st = ref.watch(_shopProvider);
    final count = st.cartCount;

    return AnimatedSlide(
      offset: count == 0 ? const Offset(0, 1) : Offset.zero,
      duration: const Duration(milliseconds: 350),
      curve: Curves.easeOutBack,
      child: AnimatedOpacity(
        opacity: count == 0 ? 0 : 1,
        duration: const Duration(milliseconds: 200),
        child: Container(
          margin: EdgeInsets.fromLTRB(16, 0, 16, MediaQuery.of(context).padding.bottom + 16),
          child: GestureDetector(
            onTap: () => _showCart(context, ref, store),
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(colors: [store.primary, store.dark],
                    begin: Alignment.centerLeft, end: Alignment.centerRight),
                borderRadius: BorderRadius.circular(18),
                boxShadow: [BoxShadow(color: store.primary.withOpacity(0.45),
                    blurRadius: 20, offset: const Offset(0, 8))],
              ),
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
              child: Row(children: [
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Stack(clipBehavior: Clip.none, children: [
                    const Icon(Icons.shopping_cart_rounded, color: Colors.white, size: 20),
                    if (count > 0)
                      Positioned(
                        top: -6, right: -6,
                        child: Container(
                          padding: const EdgeInsets.all(3),
                          decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle),
                          child: Text('$count',
                              style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: store.primary)),
                        ),
                      ),
                  ]),
                ),
                const SizedBox(width: 12),
                Text('$count món', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                const Spacer(),
                Text('${st.cartTotal.toInt()}k',
                    style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                const SizedBox(width: 10),
                const Icon(Icons.chevron_right_rounded, color: Colors.white),
              ]),
            ),
          ),
        ),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// CART SHEET
// ═══════════════════════════════════════════════════════════════════════════════

void _showCart(BuildContext context, WidgetRef ref, _Store store) {
  HapticFeedback.mediumImpact();
  showModalBottomSheet(
    context: context,
    backgroundColor: Colors.transparent,
    isScrollControlled: true,
    builder: (ctx) => DraggableScrollableSheet(
      initialChildSize: 0.65,
      minChildSize: 0.4,
      maxChildSize: 0.92,
      builder: (ctx, sc) => Consumer(builder: (ctx, ref2, _) {
        final st = ref2.watch(_shopProvider);
        return Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          ),
          child: Column(children: [
            // Handle
            Center(child: Container(
              margin: const EdgeInsets.only(top: 10, bottom: 4),
              width: 40, height: 4,
              decoration: BoxDecoration(color: Colors.grey.shade300, borderRadius: BorderRadius.circular(2)),
            )),
            // Header
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 12),
              child: Row(children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(color: store.primary.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
                  child: Icon(Icons.shopping_cart_rounded, color: store.primary, size: 22),
                ),
                const SizedBox(width: 12),
                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(store.name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  Text('${st.cartCount} sản phẩm', style: TextStyle(color: Colors.grey.shade500, fontSize: 12)),
                ])),
                TextButton(
                  onPressed: () {
                    ref2.read(_shopProvider.notifier).clearCart();
                    Navigator.pop(ctx);
                  },
                  child: Text('Xóa tất cả', style: TextStyle(color: Colors.red.shade400, fontSize: 12)),
                ),
              ]),
            ),
            Divider(height: 1, color: Colors.grey.shade100),
            // Items
            Expanded(
              child: st.cart.isEmpty
                  ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
                      const Text('🛒', style: TextStyle(fontSize: 52)),
                      const SizedBox(height: 12),
                      Text('Giỏ hàng trống', style: TextStyle(color: Colors.grey.shade400, fontSize: 15)),
                    ]))
                  : ListView.separated(
                      controller: sc,
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      itemCount: st.cart.length,
                      separatorBuilder: (_, __) => Divider(height: 1, indent: 72, color: Colors.grey.shade100),
                      itemBuilder: (_, i) {
                        final item = st.cart[i];
                        return ListTile(
                          contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
                          leading: Container(
                            width: 48, height: 48,
                            decoration: BoxDecoration(
                              color: store.primary.withOpacity(0.08),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Center(child: Text(item.product.emoji, style: const TextStyle(fontSize: 26))),
                          ),
                          title: Text(item.product.name,
                              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                          subtitle: Text('${item.product.price.toInt()}k / ${item.product.unit}',
                              style: TextStyle(color: Colors.grey.shade500, fontSize: 12)),
                          trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                            Text('${item.subtotal.toInt()}k',
                                style: TextStyle(fontWeight: FontWeight.bold, color: store.primary, fontSize: 14)),
                            const SizedBox(width: 10),
                            _QtyControl(
                              qty: item.qty, color: store.primary,
                              onAdd: () {
                                HapticFeedback.selectionClick();
                                ref2.read(_shopProvider.notifier).add(item.product);
                              },
                              onRemove: () {
                                HapticFeedback.selectionClick();
                                ref2.read(_shopProvider.notifier).remove(item.product);
                              },
                            ),
                          ]),
                        );
                      },
                    ),
            ),
            // Footer summary
            if (st.cart.isNotEmpty) ...[
              Container(
                padding: const EdgeInsets.fromLTRB(20, 14, 20, 4),
                decoration: BoxDecoration(
                  color: Colors.white,
                  border: Border(top: BorderSide(color: Colors.grey.shade100, width: 1)),
                ),
                child: Column(children: [
                  _SummaryRow('Tạm tính', '${st.cartTotal.toInt()}k'),
                  const SizedBox(height: 4),
                  _SummaryRow('Phí giao hàng', '${store.deliveryFee.toInt()}k'),
                  const SizedBox(height: 8),
                  Divider(color: Colors.grey.shade200),
                  const SizedBox(height: 4),
                  _SummaryRow('Tổng cộng',
                      '${(st.cartTotal + store.deliveryFee).toInt()}k',
                      bold: true, color: store.primary),
                  const SizedBox(height: 14),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: store.primary,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 15),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                        elevation: 0,
                      ),
                      onPressed: () {
                        Navigator.pop(ctx);
                        _showCheckout(context, ref, store);
                      },
                      child: const Text('Tiến hành thanh toán',
                          style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
                    ),
                  ),
                  SizedBox(height: MediaQuery.of(ctx).padding.bottom + 8),
                ]),
              ),
            ],
          ]),
        );
      }),
    ),
  );
}

class _SummaryRow extends StatelessWidget {
  final String label;
  final String value;
  final bool bold;
  final Color? color;
  const _SummaryRow(this.label, this.value, {this.bold = false, this.color});

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Text(label, style: TextStyle(color: bold ? Colors.grey.shade800 : Colors.grey.shade500,
          fontWeight: bold ? FontWeight.w600 : FontWeight.normal, fontSize: bold ? 15 : 13)),
      const Spacer(),
      Text(value, style: TextStyle(
          fontWeight: bold ? FontWeight.bold : FontWeight.w500,
          fontSize: bold ? 17 : 13,
          color: color ?? (bold ? Colors.grey.shade900 : Colors.grey.shade700))),
    ]);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// CHECKOUT SHEET
// ═══════════════════════════════════════════════════════════════════════════════

void _showCheckout(BuildContext context, WidgetRef ref, _Store store) {
  showModalBottomSheet(
    context: context,
    backgroundColor: Colors.transparent,
    isScrollControlled: true,
    builder: (_) => _CheckoutSheet(store: store, ref: ref),
  );
}

class _CheckoutSheet extends StatefulWidget {
  final _Store store;
  final WidgetRef ref;
  const _CheckoutSheet({required this.store, required this.ref});

  @override
  State<_CheckoutSheet> createState() => _CheckoutSheetState();
}

class _CheckoutSheetState extends State<_CheckoutSheet>
    with SingleTickerProviderStateMixin {
  int _payment = 0; // 0=COD, 1=MoMo, 2=ZaloPay, 3=Banking
  bool _ordered = false;
  late AnimationController _successCtrl;
  late Animation<double> _successScale;

  final _payments = [
    {'icon': '💵', 'name': 'Tiền mặt (COD)', 'desc': 'Thanh toán khi nhận hàng'},
    {'icon': '🌸', 'name': 'MoMo', 'desc': 'Ví điện tử MoMo'},
    {'icon': '🔵', 'name': 'ZaloPay', 'desc': 'Ví điện tử ZaloPay'},
    {'icon': '🏦', 'name': 'Chuyển khoản', 'desc': 'Ngân hàng trực tuyến'},
  ];

  @override
  void initState() {
    super.initState();
    _successCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 600));
    _successScale = CurvedAnimation(parent: _successCtrl, curve: Curves.elasticOut);
  }

  @override
  void dispose() {
    _successCtrl.dispose();
    super.dispose();
  }

  void _placeOrder() {
    HapticFeedback.heavyImpact();
    setState(() => _ordered = true);
    _successCtrl.forward();
    Future.delayed(const Duration(seconds: 2), () {
      if (!mounted) return;
      widget.ref.read(_shopProvider.notifier).clearCart();
      Navigator.pop(context);
    });
  }

  @override
  Widget build(BuildContext context) {
    final st = widget.ref.watch(_shopProvider);
    final total = st.cartTotal + widget.store.deliveryFee;
    final bottom = MediaQuery.of(context).padding.bottom;

    return Container(
      height: MediaQuery.of(context).size.height * 0.88,
      decoration: const BoxDecoration(
        color: Color(0xFFF8F8FA),
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: _ordered ? _SuccessView(scale: _successScale, store: widget.store) : Column(
        children: [
          Center(child: Container(
            margin: const EdgeInsets.only(top: 10, bottom: 4),
            width: 40, height: 4,
            decoration: BoxDecoration(color: Colors.grey.shade300, borderRadius: BorderRadius.circular(2)),
          )),
          // Header
          Container(
            color: Colors.white,
            padding: const EdgeInsets.fromLTRB(20, 10, 20, 16),
            child: Row(children: [
              GestureDetector(
                onTap: () => Navigator.pop(context),
                child: const Icon(Icons.close, size: 22, color: Colors.black54),
              ),
              const SizedBox(width: 14),
              const Text('Thanh toán', style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
            ]),
          ),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                // Delivery address
                _SectionCard(
                  title: 'Địa chỉ giao hàng',
                  icon: Icons.location_on_rounded,
                  iconColor: Colors.red.shade400,
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    const Text('Nguyễn Văn A', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                    const SizedBox(height: 2),
                    Text('0901 234 567', style: TextStyle(color: Colors.grey.shade600, fontSize: 13)),
                    const SizedBox(height: 2),
                    Text('123 Nguyễn Văn Linh, P.Tân Phú, Q.7, TP.HCM',
                        style: TextStyle(color: Colors.grey.shade600, fontSize: 13)),
                    const SizedBox(height: 8),
                    OutlinedButton.icon(
                      onPressed: () {},
                      icon: const Icon(Icons.edit_outlined, size: 15),
                      label: const Text('Thay đổi'),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                        textStyle: const TextStyle(fontSize: 12),
                        side: BorderSide(color: widget.store.primary),
                        foregroundColor: widget.store.primary,
                      ),
                    ),
                  ]),
                ),
                const SizedBox(height: 14),
                // Payment method
                _SectionCard(
                  title: 'Phương thức thanh toán',
                  icon: Icons.payment_rounded,
                  iconColor: Colors.blue.shade400,
                  child: Column(
                    children: List.generate(_payments.length, (i) {
                      final p = _payments[i];
                      final active = i == _payment;
                      return GestureDetector(
                        onTap: () => setState(() => _payment = i),
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: active ? widget.store.primary.withOpacity(0.06) : Colors.transparent,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: active ? widget.store.primary : Colors.grey.shade200,
                              width: active ? 1.5 : 1,
                            ),
                          ),
                          child: Row(children: [
                            Text(p['icon']!, style: const TextStyle(fontSize: 22)),
                            const SizedBox(width: 12),
                            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                              Text(p['name']!, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                              Text(p['desc']!, style: TextStyle(color: Colors.grey.shade500, fontSize: 11)),
                            ])),
                            if (active)
                              Icon(Icons.check_circle_rounded, color: widget.store.primary, size: 20),
                          ]),
                        ),
                      );
                    }),
                  ),
                ),
                const SizedBox(height: 14),
                // Order summary
                _SectionCard(
                  title: 'Đơn hàng từ ${widget.store.name}',
                  icon: Icons.receipt_long_rounded,
                  iconColor: Colors.orange.shade400,
                  child: Column(children: [
                    ...st.cart.map((item) => Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Row(children: [
                        Text(item.product.emoji, style: const TextStyle(fontSize: 18)),
                        const SizedBox(width: 8),
                        Expanded(child: Text('${item.product.name} x${item.qty}',
                            style: const TextStyle(fontSize: 13))),
                        Text('${item.subtotal.toInt()}k',
                            style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                      ]),
                    )),
                    Divider(color: Colors.grey.shade200),
                    _SummaryRow('Tạm tính', '${st.cartTotal.toInt()}k'),
                    const SizedBox(height: 4),
                    _SummaryRow('Phí giao hàng', '${widget.store.deliveryFee.toInt()}k'),
                    const SizedBox(height: 8),
                    Divider(color: Colors.grey.shade200),
                    const SizedBox(height: 4),
                    _SummaryRow('Tổng thanh toán', '${total.toInt()}k',
                        bold: true, color: widget.store.primary),
                  ]),
                ),
                const SizedBox(height: 14),
                // Delivery time estimate
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: widget.store.primary.withOpacity(0.06),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: widget.store.primary.withOpacity(0.2)),
                  ),
                  child: Row(children: [
                    Icon(Icons.timer_outlined, color: widget.store.primary, size: 20),
                    const SizedBox(width: 10),
                    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      const Text('Thời gian giao dự kiến', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                      Text(widget.store.deliveryTime, style: TextStyle(color: widget.store.primary, fontSize: 12)),
                    ])),
                  ]),
                ),
              ]),
            ),
          ),
          // Order button
          Container(
            padding: EdgeInsets.fromLTRB(16, 12, 16, bottom + 12),
            decoration: const BoxDecoration(
              color: Colors.white,
              boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 12, offset: Offset(0, -4))],
            ),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: widget.store.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  elevation: 0,
                ),
                onPressed: _placeOrder,
                child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                  const Icon(Icons.check_circle_outline_rounded, size: 20),
                  const SizedBox(width: 8),
                  Text('Đặt hàng • ${total.toInt()}k',
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                ]),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color iconColor;
  final Widget child;
  const _SectionCard({required this.title, required this.icon, required this.iconColor, required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 10, offset: const Offset(0, 2))],
      ),
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Icon(icon, color: iconColor, size: 18),
          const SizedBox(width: 8),
          Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
        ]),
        const SizedBox(height: 14),
        child,
      ]),
    );
  }
}

class _SuccessView extends StatelessWidget {
  final Animation<double> scale;
  final _Store store;
  const _SuccessView({required this.scale, required this.store});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        ScaleTransition(
          scale: scale,
          child: Container(
            width: 100, height: 100,
            decoration: BoxDecoration(
              color: store.primary.withOpacity(0.12),
              shape: BoxShape.circle,
            ),
            child: Icon(Icons.check_circle_rounded, color: store.primary, size: 60),
          ),
        ),
        const SizedBox(height: 20),
        const Text('Đặt hàng thành công!',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Text('Đơn hàng của bạn đang được chuẩn bị',
            style: TextStyle(color: Colors.grey.shade500, fontSize: 14)),
        const SizedBox(height: 4),
        Text('Dự kiến giao trong ${store.deliveryTime}',
            style: TextStyle(color: store.primary, fontSize: 13, fontWeight: FontWeight.w600)),
      ]),
    );
  }
}
