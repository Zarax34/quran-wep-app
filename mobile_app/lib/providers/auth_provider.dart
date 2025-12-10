import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';
import '../services/sync_service.dart';

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref.watch(apiServiceProvider), ref.watch(syncServiceProvider));
});

enum AuthStatus { initial, authenticated, unauthenticated, loading }

class AuthState {
  final AuthStatus status;
  final String? token;
  final String? error;

  AuthState({this.status = AuthStatus.initial, this.token, this.error});
}

class AuthNotifier extends StateNotifier<AuthState> {
  final ApiService _apiService;
  final SyncService _syncService;

  AuthNotifier(this._apiService, this._syncService) : super(AuthState()) {
    checkLoginStatus();
  }

  Future<void> checkLoginStatus() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    if (token != null) {
      state = AuthState(status: AuthStatus.authenticated, token: token);
      // Trigger sync in background on load
      _syncService.syncPull();
    } else {
      state = AuthState(status: AuthStatus.unauthenticated);
    }
  }

  Future<void> login(String username, String password) async {
    state = AuthState(status: AuthStatus.loading);
    try {
      final token = await _apiService.login(username, password);
      if (token != null) {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('auth_token', token);
        state = AuthState(status: AuthStatus.authenticated, token: token);
        await _syncService.syncPull();
      } else {
        state = AuthState(status: AuthStatus.unauthenticated, error: 'Login failed');
      }
    } catch (e) {
      state = AuthState(status: AuthStatus.unauthenticated, error: e.toString());
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    state = AuthState(status: AuthStatus.unauthenticated);
  }
}
