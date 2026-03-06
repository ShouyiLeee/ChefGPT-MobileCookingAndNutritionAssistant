import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../features/auth/presentation/login_screen.dart';
import '../../features/auth/presentation/signup_screen.dart';
import '../../features/auth/domain/auth_state.dart';
import '../../features/chat/presentation/chat_screen.dart';
import '../../features/recipes/presentation/recipes_screen.dart';
import '../../features/meal_plan/presentation/meal_plan_screen.dart';
import '../../features/grocery/presentation/grocery_screen.dart';
import '../../features/social/presentation/social_screen.dart';
import '../../features/profile/presentation/profile_screen.dart';
import '../navigation/main_navigation.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final notifier = ValueNotifier<int>(0);

  ref.listen<AuthState>(authProvider, (_, next) {
    notifier.value++;
  });

  final router = GoRouter(
    initialLocation: '/login',
    refreshListenable: notifier,
    redirect: (context, state) {
      final authState = ProviderScope.containerOf(context).read(authProvider);
      if (authState.isLoading) return null;

      final isLoggedIn = authState.isAuthenticated;
      final path = state.uri.path;
      final isOnAuthPage = path == '/login' || path == '/signup';

      if (!isLoggedIn && !isOnAuthPage) return '/login';
      if (isLoggedIn && isOnAuthPage) return '/home';
      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        name: 'login',
        builder: (_, __) => const LoginScreen(),
      ),
      GoRoute(
        path: '/signup',
        name: 'signup',
        builder: (_, __) => const SignupScreen(),
      ),
      ShellRoute(
        builder: (_, __, child) => MainNavigation(child: child),
        routes: [
          GoRoute(
            path: '/home',
            name: 'home',
            pageBuilder: (_, __) =>
                const NoTransitionPage(child: ChatScreen()),
          ),
          GoRoute(
            path: '/recipes',
            name: 'recipes',
            pageBuilder: (_, __) =>
                const NoTransitionPage(child: RecipesScreen()),
          ),
          GoRoute(
            path: '/mealplan',
            name: 'mealplan',
            pageBuilder: (_, __) =>
                const NoTransitionPage(child: MealPlanScreen()),
          ),
          GoRoute(
            path: '/grocery',
            name: 'grocery',
            pageBuilder: (_, __) =>
                const NoTransitionPage(child: GroceryScreen()),
          ),
          GoRoute(
            path: '/social',
            name: 'social',
            pageBuilder: (_, __) =>
                const NoTransitionPage(child: SocialScreen()),
          ),
          GoRoute(
            path: '/profile',
            name: 'profile',
            pageBuilder: (_, __) =>
                const NoTransitionPage(child: ProfileScreen()),
          ),
        ],
      ),
    ],
    errorBuilder: (_, state) => Scaffold(
      body: Center(child: Text('Page not found: \${state.uri}')),
    ),
  );

  ref.onDispose(() {
    notifier.dispose();
    router.dispose();
  });

  return router;
});
