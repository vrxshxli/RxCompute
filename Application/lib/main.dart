import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'config/routes.dart';
import 'core/theme/app_theme.dart';

// ─── BLoCs ────────────────────────────────────────────────
import 'features/theme/bloc/theme_bloc.dart';
import 'features/auth/bloc/auth_bloc.dart';
import 'features/home/bloc/home_bloc.dart';
import 'features/chat/bloc/chat_bloc.dart';
import 'features/medicine/bloc/medicine_bloc.dart';
import 'features/orders/bloc/order_bloc.dart';
import 'features/profile/bloc/profile_bloc.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(statusBarColor: Colors.transparent),
  );
  runApp(const RxApp());
}

class RxApp extends StatelessWidget {
  const RxApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(create: (_) => ThemeBloc()),
        BlocProvider(create: (_) => AuthBloc()),
        BlocProvider(create: (_) => HomeBloc()..add(LoadHomeDataEvent())),
        BlocProvider(create: (_) => ChatBloc()..add(LoadChatEvent())),
        BlocProvider(create: (_) => MedicineBloc()..add(LoadMedicinesEvent())),
        BlocProvider(create: (_) => OrderBloc()..add(LoadOrdersEvent())),
        BlocProvider(create: (_) => ProfileBloc()..add(LoadProfileEvent())),
      ],
      child: BlocBuilder<ThemeBloc, ThemeState>(
        builder: (context, themeState) {
          return MaterialApp(
            title: 'RxCompute',
            debugShowCheckedModeBanner: false,
            theme: AppTheme.light,
            darkTheme: AppTheme.dark,
            themeMode: themeState.mode,
            initialRoute: AppRoutes.splash,
            routes: AppRoutes.routes,
          );
        },
      ),
    );
  }
}
