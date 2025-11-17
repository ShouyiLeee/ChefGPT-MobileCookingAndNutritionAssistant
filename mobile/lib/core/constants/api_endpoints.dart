class ApiEndpoints {
  // Auth
  static const String login = '/auth/login';
  static const String signup = '/auth/signup';
  static const String logout = '/auth/logout';
  static const String refreshToken = '/auth/refresh';

  // Recipes
  static const String recipes = '/recipes';
  static String recipeDetail(int id) => '/recipes/$id';
  static const String searchRecipes = '/recipes/search';

  // Ingredients
  static const String recognizeIngredients = '/ingredients/recognize';
  static const String ingredients = '/ingredients';

  // Chat
  static const String chatQuery = '/chat/query';
  static const String chatHistory = '/chat/history';

  // Meal Plan
  static const String generateMealPlan = '/mealplan/generate';
  static const String mealPlans = '/mealplan';

  // Shopping List
  static const String shoppingLists = '/shopping-list';
  static String shoppingListDetail(int id) => '/shopping-list/$id';

  // Social/Posts
  static const String posts = '/posts';
  static String postDetail(int id) => '/posts/$id';
  static String postLike(int id) => '/posts/$id/like';
  static String postComments(int id) => '/posts/$id/comments';

  // Profile
  static const String profile = '/profile';
  static const String updateProfile = '/profile/update';
}
