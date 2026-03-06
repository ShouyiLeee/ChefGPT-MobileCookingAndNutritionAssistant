class AppConstants {
  // API Configuration
  // Android emulator: http://10.0.2.2:8000
  // Chrome / Windows desktop: http://localhost:8000
  // Android device on same WiFi: http://192.168.1.110:8000
  // Android emulator: http://10.0.2.2:8000
  // Chrome/Windows desktop: http://localhost:8000
  static const String baseUrl = 'http://192.168.1.110:8000';

  // Timeouts
  static const Duration connectionTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 180);

  // Storage Keys
  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String userIdKey = 'user_id';

  // Image
  static const int maxImageSize = 5 * 1024 * 1024; // 5MB

  // App Info
  static const String appName = 'ChefGPT';
  static const String appVersion = '1.0.0';
}
