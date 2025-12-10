import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  // Use 10.0.2.2 for Android Emulator to access localhost
  // Use IP address for physical device
  static const String baseUrl = 'http://10.0.2.2:5000/api';
  final Dio _dio = Dio(BaseOptions(
    baseUrl: baseUrl,
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 10),
  ));

  Future<String?> login(String username, String password) async {
    try {
      final response = await _dio.post('/login', data: {
        'username': username,
        'password': password,
      });

      if (response.statusCode == 200) {
        final token = response.data['access_token'];
        // Ideally pass user info back too
        return token;
      }
    } catch (e) {
      print('Login Error: $e');
      rethrow;
    }
    return null;
  }

  Future<Map<String, dynamic>> fetchSyncData(String token) async {
    try {
      final response = await _dio.get('/sync', options: Options(
        headers: {'Authorization': 'Bearer $token'}
      ));
      return response.data;
    } catch (e) {
      print('Sync Pull Error: $e');
      rethrow;
    }
  }

  Future<void> pushSyncData(String token, Map<String, dynamic> data) async {
    try {
      await _dio.post('/sync',
        data: data,
        options: Options(headers: {'Authorization': 'Bearer $token'})
      );
    } catch (e) {
      print('Sync Push Error: $e');
      rethrow;
    }
  }
}
