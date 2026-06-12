import 'package:flutter/material.dart';
import '../services/api_service.dart';

class EntitiesScreen extends StatefulWidget {
  const EntitiesScreen({super.key});

  @override
  State<EntitiesScreen> createState() => _EntitiesScreenState();
}

class _EntitiesScreenState extends State<EntitiesScreen> {
  List<dynamic> _entities = [];
  List<dynamic> _entityTypes = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final data = await ApiService.getEntities();
      final typesData = await ApiService.getEntityTypes();
      setState(() {
        _entities = data;
        _entityTypes = typesData;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _showAddDialog() async {
    final nameEnController = TextEditingController();
    final nameRuController = TextEditingController();
    final nameHeController = TextEditingController();
    String? selectedTypeId;
    
    if (_entityTypes.isNotEmpty) {
      selectedTypeId = _entityTypes.first['id'];
    }

    await showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) {
          return AlertDialog(
            title: const Text('Add Entity'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(controller: nameEnController, decoration: const InputDecoration(labelText: 'Name (EN)')),
                TextField(controller: nameRuController, decoration: const InputDecoration(labelText: 'Name (RU)')),
                TextField(controller: nameHeController, decoration: const InputDecoration(labelText: 'Name (HE)')),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  value: selectedTypeId,
                  decoration: const InputDecoration(labelText: 'Type'),
                  items: _entityTypes.map((type) {
                    return DropdownMenuItem<String>(
                      value: type['id'],
                      child: Text(type['name_en']),
                    );
                  }).toList(),
                  onChanged: (val) {
                    setDialogState(() => selectedTypeId = val);
                  },
                ),
              ],
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
              ElevatedButton(
                onPressed: () async {
                  try {
                    String generatedId = nameEnController.text.trim().toLowerCase().replaceAll(RegExp(r'[^a-z0-9]'), '_');
                    if (generatedId.isEmpty) {
                      generatedId = 'entity_${DateTime.now().millisecondsSinceEpoch}';
                    }
                    await ApiService.createEntity({
                      'id': generatedId,
                      'name_en': nameEnController.text,
                      'name_ru': nameRuController.text,
                      'name_he': nameHeController.text,
                      'entity_type_id': selectedTypeId
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
          );
        }
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
                  DataColumn(label: Text('Type')),
                  DataColumn(label: Text('Status')),
                  DataColumn(label: Text('Actions')),
                ],
                rows: _entities.map((e) => DataRow(
                  cells: [
                    DataCell(Text(e['id'])),
                    DataCell(Text(e['name_en'])),
                    DataCell(Text(e['entity_type_id'] ?? 'party')),
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
