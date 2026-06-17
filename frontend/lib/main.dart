import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'screens/admin_shell.dart';
import 'screens/entities_screen.dart';
import 'screens/entity_types_screen.dart';
import 'screens/axes_screen.dart';
import 'screens/questions_screen.dart';
import 'screens/documents_screen.dart';

import 'screens/system_screen.dart';

final ValueNotifier<String> appLanguageNotifier = ValueNotifier<String>('EN');

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
    return ValueListenableBuilder<String>(
      valueListenable: appLanguageNotifier,
      builder: (context, lang, _) {
        Color primaryColor;
        Color bodyColor;
        Color secondaryColor;
        Color backgroundColor;
        Color surfaceColor;

        if (lang == 'RU') {
          primaryColor = const Color(0xFF00FFB3); // Teal/Emerald bright
          bodyColor = const Color(0xFF00CC8F);    // Muted Emerald
          secondaryColor = const Color(0xFF005F43);
          backgroundColor = const Color(0xFF000502);
          surfaceColor = const Color(0xFF02100A);
        } else if (lang == 'HE') {
          primaryColor = const Color(0xFFADFF2F); // Lime/Green-Yellow bright
          bodyColor = const Color(0xFF99CC33);    // Muted Olive/Lime
          secondaryColor = const Color(0xFF4F7A28);
          backgroundColor = const Color(0xFF030500);
          surfaceColor = const Color(0xFF0A1002);
        } else { // 'EN'
          primaryColor = const Color(0xFF00FF41); // Classic bright Matrix
          bodyColor = const Color(0xFF33CC33);    // Less bright body green
          secondaryColor = const Color(0xFF005F0F);
          backgroundColor = const Color(0xFF000500);
          surfaceColor = const Color(0xFF021002);
        }

        return MaterialApp.router(
          title: 'WhereAmI Admin',
          theme: ThemeData.dark().copyWith(
            scaffoldBackgroundColor: Colors.transparent,
            colorScheme: ColorScheme.dark(
              primary: primaryColor,
              onPrimary: Colors.black,
              secondary: secondaryColor,
              onSecondary: Colors.white,
              background: backgroundColor,
              onBackground: primaryColor,
              surface: surfaceColor,
              onSurface: primaryColor,
              error: Colors.redAccent,
              onError: Colors.black,
            ),
            appBarTheme: AppBarTheme(
              backgroundColor: backgroundColor,
              foregroundColor: primaryColor,
              elevation: 0,
            ),
            navigationRailTheme: NavigationRailThemeData(
              backgroundColor: Colors.transparent,
              selectedIconTheme: IconThemeData(color: primaryColor),
              unselectedIconTheme: IconThemeData(color: secondaryColor),
              selectedLabelTextStyle: TextStyle(color: primaryColor, fontFamily: 'monospace'),
              unselectedLabelTextStyle: TextStyle(color: secondaryColor, fontFamily: 'monospace'),
            ),
            textTheme: TextTheme(
              displayLarge: TextStyle(color: primaryColor, fontFamily: 'monospace', fontWeight: FontWeight.bold),
              titleLarge: TextStyle(color: primaryColor, fontFamily: 'monospace', fontWeight: FontWeight.bold),
              bodyLarge: TextStyle(color: bodyColor, fontFamily: 'monospace'),
              bodyMedium: TextStyle(color: bodyColor, fontFamily: 'monospace'),
            ),
            inputDecorationTheme: InputDecorationTheme(
              labelStyle: TextStyle(color: primaryColor, fontFamily: 'monospace'),
              enabledBorder: OutlineInputBorder(
                borderSide: BorderSide(color: secondaryColor),
              ),
              focusedBorder: OutlineInputBorder(
                borderSide: BorderSide(color: primaryColor, width: 2),
              ),
            ),
            dividerTheme: DividerThemeData(
              color: secondaryColor,
              thickness: 1,
            ),
          ),
          routerConfig: _router,
        );
      },
    );
  }
}
