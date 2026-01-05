import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../services/api.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _tokenCtrl = TextEditingController();
  final _baseCtrl = TextEditingController(text: ApiClient.instance.baseUrl);
  bool _loading = false;
  String? _error;
  bool _showAdvanced = false;

  @override
  void initState() {
    super.initState();
    _loadPrefs();
  }

  Future<void> _loadPrefs() async {
    final sp = await SharedPreferences.getInstance();
    final base = sp.getString('base_url');
    final token = sp.getString('app_token');
    if (base != null) _baseCtrl.text = base;
    if (token != null) _tokenCtrl.text = token;
  }

  Future<void> _saveAndContinue() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final base = _baseCtrl.text.trim();
      final token = _tokenCtrl.text.trim();
      ApiClient.instance.setBaseUrl(base);
      ApiClient.instance.setToken(token);

      final sp = await SharedPreferences.getInstance();
      await sp.setString('base_url', base);
      await sp.setString('app_token', token);

      // quick health check
      final res = await ApiClient.instance.get('/health');
      if (res.statusCode >= 200 && res.statusCode < 300) {
        if (!mounted) return;
        Navigator.pushReplacementNamed(context, '/home');
      } else {
        setState(() => _error = 'API error: ${res.statusCode}');
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
                  const Text('Welcome back', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 6),
                  const Text('Sign in to continue', style: TextStyle(color: Colors.black54)),
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
                        const Text('App Token', style: TextStyle(fontWeight: FontWeight.w600)),
                        const SizedBox(height: 8),
                        TextField(
                          controller: _tokenCtrl,
                          decoration: const InputDecoration(hintText: 'Paste app_token'),
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
                            onPressed: _loading ? null : _saveAndContinue,
                            child: Padding(
                              padding: const EdgeInsets.symmetric(vertical: 14.0),
                              child: Text(_loading ? 'Checking…' : 'Sign in'),
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
                      const Text("Don't have an account? "),
                      TextButton(
                        onPressed: _loading ? null : () => Navigator.pushReplacementNamed(context, '/auth/signup'),
                        child: const Text('Create one'),
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
