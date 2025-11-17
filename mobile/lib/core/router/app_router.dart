import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../features/auth/presentation/login_screen.dart';
import '../../features/auth/presentation/signup_screen.dart';
import '../../features/chat/presentation/chat_screen.dart';
import '../../features/recipes/presentation/recipes_screen.dart';
import '../../features/social/presentation/social_screen.dart';
import '../../features/profile/presentation/profile_screen.dart';
import '../navigation/main_navigation.dart';

class AppRouter {
  static final GoRouter router = GoRouter(
    initialLocation: '/home',
    routes: [
      // Auth Routes
      GoRoute(
        path: '/login',
        name: 'login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/signup',
        name: 'signup',
        builder: (context, state) => const SignupScreen(),
      ),

      // Main Navigation with Bottom Nav Bar
      ShellRoute(
        builder: (context, state, child) => MainNavigation(child: child),
        routes: [
          GoRoute(
            path: '/home',
            name: 'home',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: ChatScreen(),
            ),
          ),
          GoRoute(
            path: '/recipes',
            name: 'recipes',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: RecipesScreen(),
            ),
          ),
          GoRoute(
            path: '/social',
            name: 'social',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: SocialScreen(),
            ),
          ),
          GoRoute(
            path: '/profile',
            name: 'profile',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: ProfileScreen(),
            ),
          ),
        ],
      ),

      // Detail Routes (Full Screen)
      GoRoute(
        path: '/recipe/:id',
        name: 'recipe-detail',
        builder: (context, state) {
          final id = state.pathParameters['id'];
          return Scaffold(
            appBar: AppBar(title: const Text('Recipe Detail')),
            body: Center(child: Text('Recipe $id')),
          );
        },
      ),
    ],

    errorBuilder: (context, state) => Scaffold(
      body: Center(
        child: Text('Page not found: ${state.uri}'),
      ),
    ),
  );
}
