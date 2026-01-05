import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiClient {
  ApiClient._();
  static final ApiClient instance = ApiClient._();

  // Point to your FastAPI base
  String baseUrl = 'http://192.168.220.1:8000';
  String? _token;

  void setBaseUrl(String url) {
    baseUrl = url;
  }

  void setToken(String? token) {
    _token = token;
  }

  Map<String, String> _headers([Map<String, String>? extra]) {
    final h = <String, String>{
      'Content-Type': 'application/json',
    };
    if (_token != null && _token!.isNotEmpty) {
      h['Authorization'] = 'Bearer $_token';
    }
    if (extra != null) h.addAll(extra);
    return h;
  }

  Future<http.Response> get(String path) async {
    final url = Uri.parse('$baseUrl$path');
    return http.get(url, headers: _headers());
  }

  Future<http.Response> post(String path, Map<String, dynamic> body) async {
    final url = Uri.parse('$baseUrl$path');
    return http.post(url, headers: _headers(), body: jsonEncode(body));
  }
}
