import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_colors.dart';
import '../../../shared/widgets/quick_action_button.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ChefGPT'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              // Clear chat history
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Quick Actions
          Container(
            padding: const EdgeInsets.all(16),
            color: AppColors.surface,
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  QuickActionButton(
                    icon: Icons.camera_alt,
                    label: 'Scan Ingredients',
                    onTap: () {
                      // Navigate to camera
                    },
                  ),
                  const SizedBox(width: 12),
                  QuickActionButton(
                    icon: Icons.restaurant,
                    label: 'Suggest Recipes',
                    onTap: () {
                      // Quick suggest
                    },
                  ),
                  const SizedBox(width: 12),
                  QuickActionButton(
                    icon: Icons.shopping_cart,
                    label: 'Shopping List',
                    onTap: () {
                      // Navigate to shopping list
                    },
                  ),
                  const SizedBox(width: 12),
                  QuickActionButton(
                    icon: Icons.calendar_today,
                    label: 'Meal Plan',
                    onTap: () {
                      // Navigate to meal plan
                    },
                  ),
                  const SizedBox(width: 12),
                  QuickActionButton(
                    icon: Icons.favorite,
                    label: 'Eat Clean',
                    onTap: () {
                      // Eat clean mode
                    },
                  ),
                ],
              ),
            ),
          ),
          const Divider(height: 1),

          // Chat Messages
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: 0, // TODO: Connect to chat state
              itemBuilder: (context, index) {
                return const SizedBox(); // TODO: Chat message widget
              },
            ),
          ),

          // Input Area
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.surface,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 10,
                  offset: const Offset(0, -5),
                ),
              ],
            ),
            child: Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.image),
                  onPressed: () {
                    // Pick image
                  },
                ),
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    decoration: const InputDecoration(
                      hintText: 'Ask me anything about cooking...',
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.symmetric(horizontal: 16),
                    ),
                    maxLines: null,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.send),
                  color: AppColors.primary,
                  onPressed: () {
                    // Send message
                    final message = _messageController.text.trim();
                    if (message.isNotEmpty) {
                      // TODO: Send to chat provider
                      _messageController.clear();
                    }
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
