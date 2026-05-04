import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = "http://10.0.2.2:8000";

  static Future<Map<String, dynamic>?> login(
    String email,
    String password,
  ) async {
    try {
      final response = await http.post(
        Uri.parse("$baseUrl/api/v1/auth/login"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"email": email, "password": password}),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        return {
          "error": true,
          "message": jsonDecode(response.body)["detail"] ?? "Login failed",
        };
      }
    } catch (e) {
      return {
        "error": true,
        "message": "Connection error. Check backend/server.",
      };
    }
  }

  static Future<Map<String, dynamic>?> logActivity(
    Map<String, dynamic> activityData,
  ) async {
    try {
      final response = await http.post(
        Uri.parse("$baseUrl/api/v1/activity/log"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(activityData),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        return {
          "error": true,
          "message":
              jsonDecode(response.body)["detail"] ?? "Activity logging failed",
        };
      }
    } catch (e) {
      return {
        "error": true,
        "message": "Connection error. Check backend/server.",
      };
    }
  }

  static Future<Map<String, dynamic>?> fetchPredictions() async {
    try {
      final response = await http.get(
        Uri.parse("$baseUrl/api/v1/predictions"),
        headers: {"Content-Type": "application/json"},
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        return {
          "error": true,
          "message":
              jsonDecode(response.body)["detail"] ??
              "Failed to fetch predictions",
        };
      }
    } catch (e) {
      return {
        "error": true,
        "message": "Connection error. Check backend/server.",
      };
    }
  }
}
