class AppConstants {
  // API Configuration — đổi theo môi trường chạy:
  // Flutter web (Chrome):        http://localhost:8000
  // Android emulator:            http://10.0.2.2:8000
  // Android device trên WiFi:    http://192.168.1.143:8000  (IP máy tính hiện tại)
  static const String baseUrl = 'http://localhost:8000';

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
