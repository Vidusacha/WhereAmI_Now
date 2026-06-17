import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'system_screen.dart';
import '../widgets/matrix_rain.dart';

class AdminShell extends StatelessWidget {
  final Widget child;

  const AdminShell({super.key, required this.child});

  String _getDynamicTitle(BuildContext context) {
    final String location = GoRouterState.of(context).uri.path;
    if (location.startsWith('/entities')) {
      return '* Where Am I * Entities *';
    }
    if (location.startsWith('/entity-types')) {
      return '* Where Am I * Entity Types *';
    }
    if (location.startsWith('/axes')) {
      return '* Where Am I * Axes *';
    }
    if (location.startsWith('/questions')) {
      return '* Where Am I * Questions *';
    }
    if (location.startsWith('/documents')) {
      return '* Where Am I * Documents *';
    }
    if (location.startsWith('/system')) {
      return '* Where Am I * System *';
    }
    return '* Where Am I *';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF000500),
      appBar: AppBar(
        title: Text(_getDynamicTitle(context), style: const TextStyle(fontFamily: 'monospace', fontWeight: FontWeight.bold, letterSpacing: 2)),
      ),
      body: Stack(
        children: [
          // Subtle background matrix digital rain
          const Positioned.fill(
            child: MatrixRainBackground(opacity: 0.12),
          ),
          // Main layout content
          Positioned.fill(
            child: Row(
              children: [
          NavigationRail(
            selectedIndex: _calculateSelectedIndex(context),
            onDestinationSelected: (int index) {
              switch (index) {
                case 0:
                  context.go('/entities');
                  break;
                case 1:
                  context.go('/entity-types');
                  break;
                case 2:
                  context.go('/axes');
                  break;
                case 3:
                  context.go('/questions');
                  break;
                case 4:
                  context.go('/documents');
                  break;
                case 5:
                  context.go('/system');
                  break;
              }
            },
            labelType: NavigationRailLabelType.all,
            destinations: const [
              NavigationRailDestination(
                icon: Icon(Icons.group),
                label: Text('Entities'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.category),
                label: Text('Entity Types'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.explore),
                label: Text('Axes'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.question_answer),
                label: Text('Questions'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.folder),
                label: Text('Documents'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.computer),
                label: Text('System'),
              ),
            ],
          ),
          const VerticalDivider(thickness: 1, width: 1),
          Expanded(child: child),
        ],
            ),
          ),
        ],
      ),
    );
  }

  int _calculateSelectedIndex(BuildContext context) {
    final String location = GoRouterState.of(context).uri.path;
    if (location.startsWith('/entities')) {
      return 0;
    }
    if (location.startsWith('/entity-types')) {
      return 1;
    }
    if (location.startsWith('/axes')) {
      return 2;
    }
    if (location.startsWith('/questions')) {
      return 3;
    }
    if (location.startsWith('/documents')) {
      return 4;
    }
    if (location.startsWith('/system')) {
      return 5;
    }
    return 0;
  }
}
