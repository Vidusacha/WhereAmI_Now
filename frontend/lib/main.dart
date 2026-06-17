import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'screens/admin_shell.dart';
import 'screens/entities_screen.dart';
import 'screens/entity_types_screen.dart';
import 'screens/axes_screen.dart';
import 'screens/questions_screen.dart';
import 'screens/documents_screen.dart';

import 'screens/system_screen.dart';

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
          path: '/entity-types',
          builder: (context, state) => const EntityTypesScreen(),
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
        GoRoute(
          path: '/system',
          builder: (context, state) => const SystemScreen(),
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
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: Colors.transparent,
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF00FF41), // Matrix bright green
          onPrimary: Colors.black,
          secondary: Color(0xFF008F11), // Darker green
          onSecondary: Colors.white,
          background: Color(0xFF000500),
          onBackground: Color(0xFF00FF41),
          surface: Color(0xFF071207), // Very dark green-black surface
          onSurface: Color(0xFF00FF41),
          error: Colors.redAccent,
          onError: Colors.black,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF000500),
          foregroundColor: Color(0xFF00FF41),
          elevation: 0,
        ),
        navigationRailTheme: const NavigationRailThemeData(
          backgroundColor: Colors.transparent,
          selectedIconTheme: IconThemeData(color: Color(0xFF00FF41)),
          unselectedIconTheme: IconThemeData(color: Color(0xFF008F11)),
          selectedLabelTextStyle: TextStyle(color: Color(0xFF00FF41), fontFamily: 'monospace'),
          unselectedLabelTextStyle: TextStyle(color: Color(0xFF008F11), fontFamily: 'monospace'),
        ),
        textTheme: const TextTheme(
          displayLarge: TextStyle(color: Color(0xFF00FF41), fontFamily: 'monospace', fontWeight: FontWeight.bold),
          titleLarge: TextStyle(color: Color(0xFF00FF41), fontFamily: 'monospace', fontWeight: FontWeight.bold),
          bodyLarge: TextStyle(color: Color(0xFF33FF33), fontFamily: 'monospace'),
          bodyMedium: TextStyle(color: Color(0xFF33FF33), fontFamily: 'monospace'),
        ),
        inputDecorationTheme: const InputDecorationTheme(
          labelStyle: TextStyle(color: Color(0xFF00FF41), fontFamily: 'monospace'),
          enabledBorder: OutlineInputBorder(
            borderSide: BorderSide(color: Color(0xFF008F11)),
          ),
          focusedBorder: OutlineInputBorder(
            borderSide: BorderSide(color: Color(0xFF00FF41), width: 2),
          ),
        ),
        dividerTheme: const DividerThemeData(
          color: Color(0xFF008F11),
          thickness: 1,
        ),
      ),
      routerConfig: _router,
    );
  }
}
