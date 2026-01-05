import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../services/api.dart';

class SignupScreen extends StatefulWidget {
  const SignupScreen({super.key});

  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {
  final _baseCtrl = TextEditingController(text: ApiClient.instance.baseUrl);
  final _tokenCtrl = TextEditingController();
  String? _error;
  bool _loading = false;
  bool _showAdvanced = false;

  @override
  void initState() {
    super.initState();
    _loadPrefs();
  }

  Future<void> _loadPrefs() async {
    final sp = await SharedPreferences.getInstance();
    final base = sp.getString('base_url');
    if (base != null) _baseCtrl.text = base;
  }

  Future<void> _verify() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final base = _baseCtrl.text.trim();
      final idToken = _tokenCtrl.text.trim();
      ApiClient.instance.setBaseUrl(base);

      final sp = await SharedPreferences.getInstance();
      await sp.setString('base_url', base);

      final res = await ApiClient.instance.post('/auth/verify', {"idToken": idToken});
      if (res.statusCode >= 200 && res.statusCode < 300) {
        if (!mounted) return;
        Navigator.pushReplacementNamed(context, '/auth/login');
      } else {
        setState(() => _error = 'Verify failed: ${res.statusCode}');
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 460),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Create your account', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 6),
                  const Text('Sign up to get started', style: TextStyle(color: Colors.black54)),
                  const SizedBox(height: 20),
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: const Color(0xFFE2E8F0)),
                    ),
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Firebase ID Token', style: TextStyle(fontWeight: FontWeight.w600)),
                        const SizedBox(height: 8),
                        TextField(
                          controller: _tokenCtrl,
                          decoration: const InputDecoration(hintText: 'Paste idToken from Firebase'),
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Switch(
                              value: _showAdvanced,
                              onChanged: (v) => setState(() => _showAdvanced = v),
                            ),
                            const Text('Advanced'),
                          ],
                        ),
                        if (_showAdvanced) ...[
                          const Text('FastAPI Base URL', style: TextStyle(fontWeight: FontWeight.w600)),
                          const SizedBox(height: 8),
                          TextField(
                            controller: _baseCtrl,
                            decoration: const InputDecoration(hintText: 'http://192.168.220.1:8000'),
                          ),
                          const SizedBox(height: 12),
                        ],
                        if (_error != null) ...[
                          Text(_error!, style: const TextStyle(color: Colors.red)),
                          const SizedBox(height: 8),
                        ],
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(
                            onPressed: _loading ? null : _verify,
                            child: Padding(
                              padding: const EdgeInsets.symmetric(vertical: 14.0),
                              child: Text(_loading ? 'Verifying…' : 'Verify & Continue'),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text('Already have an account? '),
                      TextButton(
                        onPressed: _loading ? null : () => Navigator.pushReplacementNamed(context, '/auth/login'),
                        child: const Text('Sign in'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
