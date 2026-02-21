import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import '../providers/api_provider.dart';
import '../../config/api_config.dart';

class AuthRepository {
  final ApiProvider _api = ApiProvider();
  final FirebaseAuth _firebaseAuth = FirebaseAuth.instance;
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: ['email', 'profile'],
  );

  // ─── Phone OTP ────────────────────────────────────────────
  Future<Map<String, dynamic>> sendOtp(String phone) async {
    final res = await _api.dio.post(
      ApiConfig.sendOtp,
      data: {'phone': phone},
    );
    return res.data;
  }

  Future<Map<String, dynamic>> verifyOtp(String phone, String otp) async {
    final res = await _api.dio.post(
      ApiConfig.verifyOtp,
      data: {'phone': phone, 'otp': otp},
    );
    final data = res.data;
    // Save JWT token from backend
    await _api.saveToken(data['access_token']);
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
    final res = await _api.dio.post(
      ApiConfig.googleAuth,
      data: {'id_token': firebaseIdToken},
    );

    final data = res.data;
    // Save our backend JWT token
    await _api.saveToken(data['access_token']);
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
  }

  Future<bool> isLoggedIn() async {
    return await _api.hasToken();
  }
}
