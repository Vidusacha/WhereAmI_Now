import 'package:flutter/material.dart';
import '../services/api_service.dart';

class AxesScreen extends StatefulWidget {
  const AxesScreen({super.key});

  @override
  State<AxesScreen> createState() => _AxesScreenState();
}

class _AxesScreenState extends State<AxesScreen> {
  List<dynamic> _axes = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final data = await ApiService.getAxes();
      setState(() => _axes = data);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _showAddOrEditDialog({Map<String, dynamic>? axisToEdit}) async {
    final isNew = axisToEdit == null;
    final nameController = TextEditingController(
      text: isNew ? '' : axisToEdit['name_en'],
    );
    final nameRuController = TextEditingController(
      text: isNew ? '' : axisToEdit['name_ru'],
    );
    final nameHeController = TextEditingController(
      text: isNew ? '' : axisToEdit['name_he'],
    );
    final descController = TextEditingController(
      text: isNew ? '' : axisToEdit['description'],
    );

    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(isNew ? 'Add Axis' : 'Edit Axis'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (isNew)
              const Text(
                'Enter a name for the political axis in any language. The AI will translate it into EN, RU, and HE and generate an ID.',
              )
            else
              const Text('Edit the axis details.'),
            const SizedBox(height: 16),
            if (isNew)
              TextField(
                controller: nameController,
                decoration: const InputDecoration(labelText: 'Axis Name/Topic'),
              )
            else ...[
              TextField(
                controller: nameController,
                decoration: const InputDecoration(labelText: 'Name (EN)'),
              ),
              TextField(
                controller: nameRuController,
                decoration: const InputDecoration(labelText: 'Name (RU)'),
              ),
              TextField(
                controller: nameHeController,
                decoration: const InputDecoration(labelText: 'Name (HE)'),
              ),
              TextField(
                controller: descController,
                decoration: const InputDecoration(labelText: 'Description'),
              ),
            ],
          ],
        ),
        actions: [
          if (!isNew)
            TextButton(
              onPressed: () async {
                setState(() => _isLoading = true);
                if (mounted) Navigator.pop(context);
                try {
                  await ApiService.deleteAxis(axisToEdit['id']);
                  if (mounted)
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Axis deleted successfully!'),
                      ),
                    );
                  await _loadData();
                } catch (e) {
                  if (mounted)
                    ScaffoldMessenger.of(
                      context,
                    ).showSnackBar(SnackBar(content: Text('Error: $e')));
                  if (mounted) setState(() => _isLoading = false);
                }
              },
              child: const Text('Delete', style: TextStyle(color: Colors.red)),
            ),
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              if (nameController.text.isEmpty) return;
              setState(() => _isLoading = true);
              if (mounted) Navigator.pop(context);

              try {
                if (isNew) {
                  await ApiService.autoTranslateAxis(nameController.text);
                  if (mounted)
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Axis created successfully!'),
                      ),
                    );
                } else {
                  await ApiService.updateAxis(axisToEdit['id'], {
                    'name_en': nameController.text,
                    'name_ru': nameRuController.text,
                    'name_he': nameHeController.text,
                    'description': descController.text,
                  });
                  if (mounted)
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Axis updated successfully!'),
                      ),
                    );
                }
                await _loadData();
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(
                    context,
                  ).showSnackBar(SnackBar(content: Text('Error: $e')));
                }
              } finally {
                if (mounted) setState(() => _isLoading = false);
              }
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }

  Future<void> _discoverNewAxes() async {
    setState(() => _isLoading = true);
    try {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Starting unsupervised axis discovery (this may take a few minutes)...',
            ),
          ),
        );
      final result = await ApiService.discoverNewAxes();

      final logs = (result['logs'] as List?)?.cast<String>() ?? [];
      final discoveredCount = (result['discovered_axes'] as List?)?.length ?? 0;

      if (mounted) {
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: Text('Discovery Complete ($discoveredCount found)'),
            content: SizedBox(
              width: 600,
              height: 400,
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: logs.length,
                itemBuilder: (ctx, i) => Padding(
                  padding: const EdgeInsets.only(bottom: 8.0),
                  child: Text(
                    logs[i],
                    style: const TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 12,
                    ),
                  ),
                ),
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Close'),
              ),
            ],
          ),
        );
      }
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error: $e')));
    } finally {
      await _loadData();
    }
  }

  Future<void> _discoverDiscourseGlobal() async {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'Global Discover Discourse not yet implemented. Please run per-entity from Entities screen.',
        ),
      ),
    );
  }

  Future<void> _showGlobalDiscoveryLog() async {
    setState(() => _isLoading = true);
    try {
      final logContent = await ApiService.getGlobalDiscoveryLog();
      if (mounted) {
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Unsupervised Axis Discovery Log'),
            content: SizedBox(
              width: 600,
              height: 400,
              child: SingleChildScrollView(
                child: Text(
                  logContent,
                  style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
                ),
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Close'),
              ),
            ],
          ),
        );
      }
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error: $e')));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      floatingActionButton: PopupMenuButton<String>(
        onSelected: (val) {
          if (val == 'add') {
            _showAddOrEditDialog();
          } else if (val == 'discover')
            _discoverNewAxes();
          else if (val == 'discover_discourse')
            _discoverDiscourseGlobal();
          else if (val == 'show_log')
            _showGlobalDiscoveryLog();
        },
        itemBuilder: (context) => [
          const PopupMenuItem(value: 'add', child: Text('Add New Axis')),
          const PopupMenuItem(
            value: 'discover',
            child: Text('Unsupervised Axis Discovery'),
          ),
          const PopupMenuItem(
            value: 'discover_discourse',
            child: Text('Discover Discourse (All Entities)'),
          ),
          const PopupMenuItem(
            value: 'show_log',
            child: Text('Show Discovery Discourse Log'),
          ),
        ],
        child: Container(
          width: 56,
          height: 56,
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.primary,
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: Theme.of(context).colorScheme.primary.withOpacity(0.4),
                blurRadius: 8,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Icon(Icons.add, color: Theme.of(context).colorScheme.onPrimary),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                DataTable(
                  columns: const [
                    DataColumn(label: Text('ID')),
                    DataColumn(label: Text('Name (EN)')),
                    DataColumn(label: Text('Status')),
                    DataColumn(label: Text('Actions')),
                  ],
                  rows: _axes
                      .map(
                        (e) => DataRow(
                          cells: [
                            DataCell(Text(e['id'])),
                            DataCell(Text(e['name_en'])),
                            DataCell(Text(e['status'])),
                            DataCell(
                              Row(
                                children: [
                                  IconButton(
                                    icon: const Icon(Icons.edit, size: 20),
                                    onPressed: () =>
                                        _showAddOrEditDialog(axisToEdit: e),
                                  ),
                                  if (e['status'] == 'pending_ai_proposal')
                                    TextButton.icon(
                                      icon: const Icon(Icons.check, size: 16),
                                      label: const Text('Approve'),
                                      onPressed: () async {
                                        setState(() => _isLoading = true);
                                        try {
                                          await ApiService.approveAxis(e['id']);
                                          await _loadData();
                                        } catch (err) {
                                          if (mounted)
                                            ScaffoldMessenger.of(
                                              context,
                                            ).showSnackBar(
                                              SnackBar(
                                                content: Text('Error: $err'),
                                              ),
                                            );
                                          setState(() => _isLoading = false);
                                        }
                                      },
                                    ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      )
                      .toList(),
                ),
              ],
            ),
    );
  }
}
