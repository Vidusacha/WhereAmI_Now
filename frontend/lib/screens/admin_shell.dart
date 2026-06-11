import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class AdminShell extends StatelessWidget {
  final Widget child;

  const AdminShell({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Admin Dashboard'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Row(
        children: [
          NavigationRail(
            selectedIndex: _calculateSelectedIndex(context),
            onDestinationSelected: (int index) {
              switch (index) {
                case 0:
                  context.go('/entities');
                  break;
                case 1:
                  context.go('/axes');
                  break;
                case 2:
                  context.go('/questions');
                  break;
                case 3:
                  context.go('/documents');
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
            ],
          ),
          const VerticalDivider(thickness: 1, width: 1),
          Expanded(child: child),
        ],
      ),
    );
  }

  int _calculateSelectedIndex(BuildContext context) {
    final String location = GoRouterState.of(context).uri.path;
    if (location.startsWith('/entities')) {
      return 0;
    }
    if (location.startsWith('/axes')) {
      return 1;
    }
    if (location.startsWith('/questions')) {
      return 2;
    }
    if (location.startsWith('/documents')) {
      return 3;
    }
    return 0;
  }
}
