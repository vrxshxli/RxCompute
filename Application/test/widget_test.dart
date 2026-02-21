import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:rxcompute/main.dart';
import 'package:rxcompute/providers/theme_provider.dart';

void main() {
  testWidgets('App launches and shows splash screen', (WidgetTester tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider(
        create: (_) => ThemeProvider(),
        child: const RxApp(),
      ),
    );

    // Verify RxCompute logo text is present on splash
    expect(find.text('Rx'), findsOneWidget);
    expect(find.text('Compute'), findsOneWidget);
  });
}