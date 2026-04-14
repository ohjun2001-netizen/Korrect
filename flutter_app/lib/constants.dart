class AppConstants {
  // 서버 주소 - 환경에 맞게 변경
  static const String baseUrl = 'http://10.0.2.2:8000'; // 안드로이드 에뮬레이터
  // static const String baseUrl = 'http://localhost:8000'; // iOS 시뮬레이터
  // static const String baseUrl = 'http://192.168.0.x:8000'; // 실제 기기 (서버 IP로 변경)

  // UI 색상
  static const int primaryColor = 0xFF4CAF50;
  static const int accentColor = 0xFFFF9800;
  static const int bgColor = 0xFFF5F5F5;

  // 시나리오별 이모지
  static const Map<String, String> scenarioEmoji = {
    'hospital': '🏥',
    'bank': '🏦',
    'immigration': '🛂',
  };
}
