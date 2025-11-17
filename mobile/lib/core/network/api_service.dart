import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';
import '../../shared/models/recipe_model.dart';
import '../../shared/models/user_model.dart';
import '../../shared/models/chat_message.dart';
import '../../shared/models/post_model.dart';

part 'api_service.g.dart';

@RestApi()
abstract class ApiService {
  factory ApiService(Dio dio, {String baseUrl}) = _ApiService;

  // Auth Endpoints
  @POST('/auth/signup')
  Future<Map<String, dynamic>> signup(@Body() Map<String, dynamic> data);

  @POST('/auth/login')
  Future<Map<String, dynamic>> login(@Body() Map<String, dynamic> data);

  @POST('/auth/logout')
  Future<void> logout();

  // Recipe Endpoints
  @GET('/recipes')
  Future<List<RecipeModel>> getRecipes(@Query('search') String? search);

  @GET('/recipes/{id}')
  Future<RecipeModel> getRecipeDetail(@Path('id') int id);

  @POST('/recipes')
  Future<RecipeModel> createRecipe(@Body() Map<String, dynamic> data);

  @DELETE('/recipes/{id}')
  Future<void> deleteRecipe(@Path('id') int id);

  // Ingredients Recognition
  @POST('/ingredients/recognize')
  @MultiPart()
  Future<Map<String, dynamic>> recognizeIngredients(
    @Part(name: 'image') File image,
  );

  // Chat Endpoints
  @POST('/chat/query')
  Future<ChatMessage> sendChatMessage(@Body() Map<String, dynamic> data);

  @GET('/chat/history')
  Future<List<ChatMessage>> getChatHistory();

  // Meal Plan Endpoints
  @POST('/mealplan/generate')
  Future<Map<String, dynamic>> generateMealPlan(@Body() Map<String, dynamic> data);

  @GET('/mealplan')
  Future<List<Map<String, dynamic>>> getMealPlans();

  // Shopping List Endpoints
  @POST('/shopping-list')
  Future<Map<String, dynamic>> createShoppingList(@Body() Map<String, dynamic> data);

  @GET('/shopping-list')
  Future<List<Map<String, dynamic>>> getShoppingLists();

  @GET('/shopping-list/{id}')
  Future<Map<String, dynamic>> getShoppingListDetail(@Path('id') int id);

  // Social/Posts Endpoints
  @GET('/posts')
  Future<List<PostModel>> getPosts(@Query('page') int page);

  @GET('/posts/{id}')
  Future<PostModel> getPostDetail(@Path('id') int id);

  @POST('/posts')
  Future<PostModel> createPost(@Body() Map<String, dynamic> data);

  @POST('/posts/{id}/like')
  Future<void> likePost(@Path('id') int id);

  @GET('/posts/{id}/comments')
  Future<List<Map<String, dynamic>>> getPostComments(@Path('id') int id);

  // Profile Endpoints
  @GET('/profile')
  Future<ProfileModel> getProfile();

  @PUT('/profile/update')
  Future<ProfileModel> updateProfile(@Body() Map<String, dynamic> data);
}
