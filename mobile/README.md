# ChefGPT Mobile App

Flutter app trợ lý nấu ăn và dinh dưỡng AI, kết nối với ChefGPT FastAPI backend.

## Tech Stack

| Layer | Công nghệ |
|-------|-----------|
| Framework | Flutter 3.x |
| State Management | Riverpod (flutter_riverpod) |
| Networking | Dio |
| Navigation | GoRouter |
| Storage | flutter_secure_storage |
| Image | image_picker |

## Tính năng

| Feature | Mô tả |
|---------|-------|
| AI Chat | Chat với trợ lý nấu ăn, persona thay đổi phong cách trả lời |
| Recipe Suggestion | Nhập nguyên liệu text hoặc chụp ảnh → AI gợi ý 3 món |
| Meal Planner | Tạo thực đơn tuần theo mục tiêu |
| AI Persona | Chọn hoặc tạo custom AI persona (Đầu bếp Á, Âu, Dinh dưỡng, ...) |
| User Memory | Xem và quản lý dị ứng, sở thích mà AI đã học được |
| Profile | Quản lý tài khoản, persona, memory |
| Grocery | Mock danh sách mua sắm |
| Social | Mock feed bài đăng công thức |

## Cấu trúc thư mục

```
lib/
├── core/
│   ├── constants/
│   │   └── app_constants.dart     # baseUrl, storage keys, ...
│   ├── network/
│   │   └── api_service.dart       # Dio client — tất cả API calls
│   ├── router/
│   │   └── app_router.dart        # GoRouter config
│   ├── theme/
│   │   └── app_colors.dart        # Color palette
│   └── navigation/
│       └── main_navigation.dart   # Bottom navigation bar (5 tabs)
├── features/
│   ├── auth/
│   │   ├── domain/auth_state.dart         # AuthState + AuthNotifier
│   │   └── presentation/
│   │       ├── login_screen.dart
│   │       └── signup_screen.dart
│   ├── chat/
│   │   └── presentation/chat_screen.dart  # AI chat + PersonaChip trên AppBar
│   ├── recipes/
│   │   └── presentation/recipes_screen.dart
│   ├── meal_plan/
│   │   └── presentation/meal_plan_screen.dart
│   ├── persona/
│   │   ├── data/
│   │   │   ├── persona_repository.dart    # GET/POST/PUT/DELETE /personas
│   │   │   └── persona_form_data.dart     # DTO cho create/update
│   │   ├── domain/
│   │   │   ├── persona_model.dart         # PersonaModel + canEdit()
│   │   │   └── persona_state.dart         # PersonaState + PersonaNotifier
│   │   └── presentation/
│   │       ├── persona_selection_screen.dart  # Grid chọn persona + FAB tạo mới
│   │       └── persona_form_screen.dart       # Form tạo/chỉnh sửa custom persona
│   ├── memory/
│   │   ├── data/memory_repository.dart        # GET/POST/DELETE /memory/me
│   │   ├── domain/
│   │   │   ├── memory_model.dart              # MemoryModel + MemoryCategory
│   │   │   └── memory_state.dart              # MemoryState + MemoryNotifier
│   │   └── presentation/memory_screen.dart    # Grouped list + swipe-to-delete
│   ├── grocery/
│   │   └── presentation/grocery_screen.dart
│   ├── social/
│   │   └── presentation/social_screen.dart
│   └── profile/
│       └── presentation/profile_screen.dart   # Persona + Memory menu items
└── main.dart
```

## Routes

| Path | Screen | Auth |
|------|--------|------|
| `/login` | LoginScreen | No |
| `/signup` | SignupScreen | No |
| `/home` | ChatScreen | Yes |
| `/recipes` | RecipesScreen | Yes |
| `/mealplan` | MealPlanScreen | Yes |
| `/grocery` | GroceryScreen | Yes |
| `/social` | SocialScreen | Yes |
| `/profile` | ProfileScreen | Yes |
| `/persona-select` | PersonaSelectionScreen | Yes |
| `/memory` | MemoryScreen | Yes |

## Cài đặt và chạy

### Yêu cầu

- Flutter SDK 3.x
- Dart SDK 3.x
- Android Studio / VS Code với Flutter extension
- ChefGPT backend đang chạy tại `http://localhost:8000`

### Chạy app

```bash
cd mobile
flutter pub get
flutter run
```

> **Không có code generation** — project dùng manual `fromJson`/`toJson`. Không cần chạy `build_runner`.

### Build APK

```bash
flutter build apk --debug
# hoặc release
flutter build apk --release
```

## Cấu hình Backend URL

Đổi `baseUrl` trong `lib/core/constants/app_constants.dart`:

```dart
// Android emulator
static const String baseUrl = 'http://10.0.2.2:8000';

// Android thật hoặc iOS (cùng WiFi)
static const String baseUrl = 'http://192.168.x.x:8000';

// iOS Simulator
static const String baseUrl = 'http://localhost:8000';
```

## API Client

Tất cả API calls đi qua `ApiService` (`lib/core/network/api_service.dart`) — plain Dio, không Retrofit.

Token tự động gắn vào header qua interceptor. 401 → tự động thử refresh token → redirect login nếu thất bại.

## State Management (Riverpod)

| Provider | File | Quản lý |
|----------|------|---------|
| `authProvider` | `auth/domain/auth_state.dart` | Login, token, user info |
| `personaProvider` | `persona/domain/persona_state.dart` | Danh sách personas, active persona |
| `memoryProvider` | `memory/domain/memory_state.dart` | User memories |

### Persona persistence

Khi app khởi động:
1. Đọc `active_persona_id` từ `FlutterSecureStorage` → hiển thị chip ngay lập tức (no network wait)
2. Background fetch danh sách đầy đủ từ server
3. Resolve persona đầy đủ từ list

### Memory

- Load khi vào `MemoryScreen`
- Swipe-to-delete (Dismissible) với optimistic update + rollback nếu API lỗi
- Pull-to-refresh

## Persona System

**Chọn persona**: `PersonaSelectionScreen` — grid 2 cột, persona active có border + check icon.

**Tạo custom persona**: FAB "Tạo mới" → `PersonaFormScreen` với:
- Live preview card cập nhật real-time
- Color picker (10 preset colors)
- System prompt, recipe prefix, meal plan prefix
- Quick actions (tối đa 6, add/remove)
- isPublic toggle

**Edit/Delete**: Long-press card → bottom sheet với Edit/Delete options (chỉ owner thấy).

**PersonaChip trên ChatScreen AppBar**: Hiển thị `"${persona.icon} ${persona.name}"`, tap → bottom sheet persona grid.

## Memory System

`MemoryScreen` hiển thị memories grouped theo 6 categories:

| Category | Icon | Label |
|----------|------|-------|
| `dietary` | 🚫 | Chế độ ăn |
| `preference` | ✅ | Sở thích |
| `aversion` | ❌ | Không thích |
| `goal` | 🎯 | Mục tiêu |
| `constraint` | ⚠️ | Ràng buộc |
| `context` | 📝 | Thông tin khác |

Thêm memory thủ công qua bottom sheet `_AddMemorySheet` (dropdown category + text input).
