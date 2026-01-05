import 'package:flutter/material.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _controller = PageController();
  int _index = 0;

  final List<_OnbData> _pages = const [
    _OnbData(
      icon: Icons.medication,
      title: 'Smart Refills',
      text: 'Auto reminders and one-tap refills for your medicines.',
    ),
    _OnbData(
      icon: Icons.alarm,
      title: 'Timely Reminders',
      text: 'Never miss a dose with customizable schedules.',
    ),
    _OnbData(
      icon: Icons.support_agent,
      title: 'AI Pharmacist',
      text: 'Chat for quick help and safe usage guidance.',
    ),
  ];

  void _next() {
    if (_index < _pages.length - 1) {
      _controller.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
    } else {
      Navigator.pushReplacementNamed(context, '/auth/signup');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: PageView.builder(
                controller: _controller,
                itemCount: _pages.length,
                onPageChanged: (i) => setState(() => _index = i),
                itemBuilder: (_, i) {
                  final p = _pages[i];
                  return Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(p.icon, size: 120, color: Colors.teal),
                        const SizedBox(height: 24),
                        Text(p.title, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800)),
                        const SizedBox(height: 12),
                        Text(p.text, style: const TextStyle(color: Colors.black54), textAlign: TextAlign.center),
                      ],
                    ),
                  );
                },
              ),
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(
                _pages.length,
                (i) => Container(
                  width: 8,
                  height: 8,
                  margin: const EdgeInsets.symmetric(horizontal: 4, vertical: 16),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: i == _index ? Colors.teal : Colors.teal.withOpacity(0.3),
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
              child: Row(
                children: [
                  TextButton(
                    onPressed: () => Navigator.pushReplacementNamed(context, '/auth/login'),
                    child: const Text('Skip'),
                  ),
                  const Spacer(),
                  ElevatedButton(
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.teal),
                    onPressed: _next,
                    child: Text(_index == _pages.length - 1 ? 'Get Started' : 'Next', style: const TextStyle(color: Colors.white)),
                  )
                ],
              ),
            )
          ],
        ),
      ),
    );
  }
}

class _OnbData {
  final IconData icon;
  final String title;
  final String text;
  const _OnbData({required this.icon, required this.title, required this.text});
}
