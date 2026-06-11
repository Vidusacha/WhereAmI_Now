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
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _showAddDialog() async {
    final idController = TextEditingController();
    final nameEnController = TextEditingController();
    final nameRuController = TextEditingController();
    final nameHeController = TextEditingController();

    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Axis'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: idController, decoration: const InputDecoration(labelText: 'ID (e.g. economy)')),
            TextField(controller: nameEnController, decoration: const InputDecoration(labelText: 'Name (EN)')),
            TextField(controller: nameRuController, decoration: const InputDecoration(labelText: 'Name (RU)')),
            TextField(controller: nameHeController, decoration: const InputDecoration(labelText: 'Name (HE)')),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () async {
              try {
                await ApiService.createAxis({
                  'id': idController.text,
                  'name_en': nameEnController.text,
                  'name_ru': nameRuController.text,
                  'name_he': nameHeController.text,
                });
                if (mounted) Navigator.pop(context);
                _loadData();
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
                }
              }
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddDialog,
        child: const Icon(Icons.add),
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
                rows: _axes.map((e) => DataRow(
                  cells: [
                    DataCell(Text(e['id'])),
                    DataCell(Text(e['name_en'])),
                    DataCell(Text(e['status'])),
                    DataCell(Row(
                      children: [
                        IconButton(icon: const Icon(Icons.edit, size: 20), onPressed: () {}),
                      ],
                    )),
                  ],
                )).toList(),
              ),
            ],
          ),
    );
  }
}
