import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_service.dart';
import '../../../core/theme/app_colors.dart';
import '../../../shared/models/post_model.dart';

final _postsProvider = FutureProvider<List<PostModel>>((ref) async {
  final api = ref.read(apiServiceProvider);
  final res = await api.getMockPosts();
  final posts = (res['posts'] as List<dynamic>? ?? [])
      .map((p) => PostModel.fromJson(p as Map<String, dynamic>))
      .toList();
  return posts;
});

class SocialScreen extends ConsumerWidget {
  const SocialScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final postsAsync = ref.watch(_postsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Cong dong'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.refresh(_postsProvider),
          ),
        ],
      ),
      body: postsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline,
                  size: 48, color: AppColors.error),
              const SizedBox(height: 12),
              Text('Khong tai duoc bai dang',
                  style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              ElevatedButton(
                onPressed: () => ref.refresh(_postsProvider),
                child: const Text('Thu lai'),
              ),
            ],
          ),
        ),
        data: (posts) => RefreshIndicator(
          onRefresh: () async => ref.refresh(_postsProvider),
          child: posts.isEmpty
              ? const Center(child: Text('Chua co bai dang nao'))
              : ListView.builder(
                  itemCount: posts.length,
                  itemBuilder: (_, i) => _PostCard(post: posts[i]),
                ),
        ),
      ),
    );
  }
}

class _PostCard extends StatelessWidget {
  final PostModel post;
  const _PostCard({required this.post});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ListTile(
            leading: CircleAvatar(
              backgroundColor: AppColors.primaryLight,
              child: Text(
                post.authorName.isNotEmpty
                    ? post.authorName[0].toUpperCase()
                    : '?',
                style: const TextStyle(
                    color: AppColors.primary, fontWeight: FontWeight.bold),
              ),
            ),
            title: Text(post.authorName,
                style: const TextStyle(fontWeight: FontWeight.w600)),
            subtitle: Text(post.createdAt,
                style: const TextStyle(fontSize: 12)),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Text(post.content),
          ),
          Padding(
            padding:
                const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            child: Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.favorite_border, size: 20),
                  onPressed: null,
                ),
                Text('${post.likeCount}',
                    style: Theme.of(context).textTheme.bodySmall),
                const SizedBox(width: 8),
                IconButton(
                  icon: const Icon(Icons.comment_outlined, size: 20),
                  onPressed: null,
                ),
                Text('${post.commentCount}',
                    style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
