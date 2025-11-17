# ChefGPT Mobile App

AI-powered mobile cooking and nutrition assistant built with Flutter.

## Features

- **AI Chatbot**: Intelligent cooking assistant powered by GPT-4.1/Claude
- **Recipe Discovery**: Search and browse thousands of recipes
- **Ingredient Recognition**: Use your camera to identify ingredients
- **Meal Planning**: Auto-generate weekly meal plans
- **Shopping Lists**: Smart grocery list management
- **Social Feed**: Share recipes and connect with community
- **Nutrition Tracking**: Monitor calories and macros

## Tech Stack

- **Framework**: Flutter 3.0+
- **State Management**: Riverpod
- **Networking**: Dio + Retrofit
- **Routing**: GoRouter
- **Backend**: FastAPI (separate repository)
- **Database**: PostgreSQL + pgvector (via backend)
- **Auth**: Supabase Auth
- **Storage**: Supabase Storage

## Project Structure

```
lib/
├── core/                    # Core utilities and configuration
│   ├── constants/          # App constants and API endpoints
│   ├── network/            # API client and network layer
│   ├── router/             # Navigation and routing
│   ├── theme/              # App theme and colors
│   └── utils/              # Utility functions
├── features/               # Feature modules
│   ├── auth/              # Authentication
│   ├── chat/              # AI Chatbot
│   ├── recipes/           # Recipe management
│   ├── meal_plan/         # Meal planning
│   ├── shopping_list/     # Shopping list
│   ├── social/            # Social feed
│   └── profile/           # User profile
└── shared/                # Shared components
    ├── models/           # Data models
    └── widgets/          # Reusable widgets
```

## Getting Started

### Prerequisites

- Flutter SDK 3.0 or higher
- Dart SDK 3.0 or higher
- Android Studio / VS Code with Flutter extensions
- iOS development: Xcode (macOS only)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/chefgpt.git
cd chefgpt/mobile
```

2. Install dependencies:
```bash
flutter pub get
```

3. Generate code (for models and API):
```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

4. Set up environment variables:
Create a `.env` file in the root directory:
```
API_BASE_URL=https://api.chefgpt.app
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

5. Run the app:
```bash
flutter run
```

## Building for Production

### Android
```bash
flutter build apk --release
# or for App Bundle
flutter build appbundle --release
```

### iOS
```bash
flutter build ios --release
```

## Code Generation

This project uses code generation for:
- JSON serialization (`json_serializable`)
- API clients (`retrofit`)
- Riverpod providers (`riverpod_generator`)

Run the following command when you modify models or API definitions:
```bash
flutter pub run build_runner watch --delete-conflicting-outputs
```

## Testing

Run unit tests:
```bash
flutter test
```

Run widget tests:
```bash
flutter test --coverage
```

## API Integration

The app connects to the ChefGPT backend API. Key endpoints:

- `/auth/*` - Authentication
- `/chat/query` - AI chatbot
- `/recipes/*` - Recipe management
- `/ingredients/recognize` - Image recognition
- `/mealplan/generate` - Meal planning
- `/shopping-list/*` - Shopping list management
- `/posts/*` - Social feed

## Configuration

### Backend URL
Update the base URL in `lib/core/constants/app_constants.dart`:
```dart
static const String baseUrl = 'https://your-api-url.com';
```

### Firebase Setup
1. Create a Firebase project
2. Add your `google-services.json` (Android) and `GoogleService-Info.plist` (iOS)
3. Initialize Firebase in `main.dart`

### Supabase Setup
1. Create a Supabase project
2. Update credentials in `main.dart`:
```dart
await Supabase.initialize(
  url: 'YOUR_SUPABASE_URL',
  anonKey: 'YOUR_SUPABASE_ANON_KEY',
);
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary software for internal development and research.

## Support

For issues and questions, please contact the development team.
