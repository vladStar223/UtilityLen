/// Конфигурация подключения к бэкенду UtilityLens
class ApiConfig {
  /// Адрес боевого бэкенда на сервере
  static const String defaultBaseUrl = "http://136.234.72.54:8000";

  /// Локальный адрес для Android эмулятора (если бэкенд запущен на хосте)
  static const String emulatorBaseUrl = "http://10.0.2.2:8000";

  /// Базовый префикс API
  static const String apiPrefix = "/api/v1";

  /// Текущий активный URL (по умолчанию боевой сервер)
  static String baseUrl = defaultBaseUrl;

  static String get casesEndpoint => "$baseUrl$apiPrefix/cases";
  static String get compareEndpoint => "$baseUrl$apiPrefix/compare";
  static String get chatStreamEndpoint => "$baseUrl$apiPrefix/chat/stream";
  static String get healthEndpoint => "$baseUrl/health";
}
