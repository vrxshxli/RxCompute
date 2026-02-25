import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../providers/api_provider.dart';
import '../../config/api_config.dart';

class AuthRepository {
  final ApiProvider _api = ApiProvider();
  final FirebaseAuth _firebaseAuth = FirebaseAuth.instance;
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: ['email', 'profile'],
  );
  static bool _didWarmup = false;
  static const String _loggedInKey = 'is_logged_in';

  // ─── Phone OTP ────────────────────────────────────────────
  Future<Map<String, dynamic>> sendOtp(String phone) async {
    final res = await _requestWithQuickRetry(
      () => _api.dio.post(
        ApiConfig.sendOtp,
        data: {'phone': phone},
      ),
    );
    return res.data;
  }

  Future<Map<String, dynamic>> verifyOtp(String phone, String otp) async {
    final res = await _requestWithQuickRetry(
      () => _api.dio.post(
        ApiConfig.verifyOtp,
        data: {'phone': phone, 'otp': otp},
      ),
    );
    final data = res.data;
    // Save JWT token from backend
    await _api.saveToken(data['access_token']);
    await _setLoggedInFlag(true);
    return data;
  }

  // ─── Google Sign-In via Firebase ──────────────────────────
  Future<Map<String, dynamic>?> signInWithGoogle() async {
    // 1. Trigger Google Sign-In
    final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
    if (googleUser == null) return null; // User cancelled

    // 2. Get Google auth credentials
    final GoogleSignInAuthentication googleAuth =
        await googleUser.authentication;

    // 3. Sign in to Firebase with Google credential
    final credential = GoogleAuthProvider.credential(
      accessToken: googleAuth.accessToken,
      idToken: googleAuth.idToken,
    );
    final UserCredential userCredential =
        await _firebaseAuth.signInWithCredential(credential);

    // 4. Get Firebase ID token
    final String? firebaseIdToken =
        await userCredential.user?.getIdToken();

    if (firebaseIdToken == null) {
      throw Exception('Failed to get Firebase ID token');
    }

    // 5. Send Firebase ID token to our backend for JWT
    final res = await _requestWithQuickRetry(
      () => _api.dio.post(
        ApiConfig.googleAuth,
        data: {'id_token': firebaseIdToken},
      ),
    );

    final data = res.data;
    // Save our backend JWT token
    await _api.saveToken(data['access_token']);
    await _setLoggedInFlag(true);
    return data;
  }

  // ─── Registration ─────────────────────────────────────────
  Future<Map<String, dynamic>> registerUser({
    required String name,
    required int age,
    required String gender,
    String? email,
    String? allergies,
    String? conditions,
  }) async {
    final res = await _api.dio.post(ApiConfig.register, data: {
      'name': name,
      'age': age,
      'gender': gender,
      if (email != null) 'email': email,
      if (allergies != null) 'allergies': allergies,
      if (conditions != null) 'conditions': conditions,
    });
    return res.data;
  }

  // ─── Session ──────────────────────────────────────────────
  Future<void> logout() async {
    try {
      await _firebaseAuth.signOut();
      await _googleSignIn.signOut();
    } catch (_) {}
    await _api.clearToken();
    await _setLoggedInFlag(false);
  }

  Future<bool> isLoggedIn() async {
    final tokenPresent = await _api.hasToken();
    if (tokenPresent) {
      await _setLoggedInFlag(true);
      return true;
    }
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_loggedInKey) ?? false;
  }

  // ─── Warm-up for cold starts (Render free plan) ─────────
  Future<void> warmupIfNeeded() async {
    if (_didWarmup) return;
    try {
      await _api.dio.get(
        '/',
        options: Options(
          sendTimeout: const Duration(seconds: 6),
          receiveTimeout: const Duration(seconds: 6),
        ),
      );
      _didWarmup = true;
    } catch (_) {
      // Ignore warmup failures; real auth calls handle retry.
    }
  }

  Future<Response<dynamic>> _requestWithQuickRetry(
    Future<Response<dynamic>> Function() request,
  ) async {
    try {
      return await request();
    } on DioException catch (e) {
      final shouldRetry =
          e.type == DioExceptionType.connectionTimeout ||
          e.type == DioExceptionType.connectionError ||
          e.response?.statusCode == 502 ||
          e.response?.statusCode == 503 ||
          e.response?.statusCode == 504;
      if (!shouldRetry) rethrow;
      await Future.delayed(const Duration(milliseconds: 800));
      return request();
    }
  }

  Future<void> _setLoggedInFlag(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_loggedInKey, value);
  }
}
