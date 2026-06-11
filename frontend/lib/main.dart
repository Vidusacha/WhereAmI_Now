import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'screens/admin_shell.dart';
import 'screens/entities_screen.dart';
import 'screens/axes_screen.dart';
import 'screens/questions_screen.dart';
import 'screens/documents_screen.dart';

void main() {
  runApp(const MyApp());
}

final _router = GoRouter(
  initialLocation: '/entities',
  routes: [
    ShellRoute(
      builder: (context, state, child) {
        return AdminShell(child: child);
      },
      routes: [
        GoRoute(
          path: '/entities',
          builder: (context, state) => const EntitiesScreen(),
        ),
        GoRoute(
          path: '/axes',
          builder: (context, state) => const AxesScreen(),
        ),
        GoRoute(
          path: '/questions',
          builder: (context, state) => const QuestionsScreen(),
        ),
        GoRoute(
          path: '/documents',
          builder: (context, state) => const DocumentsScreen(),
        ),
      ],
    ),
  ],
);

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'WhereAmI Admin',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      routerConfig: _router,
    );
  }
}
