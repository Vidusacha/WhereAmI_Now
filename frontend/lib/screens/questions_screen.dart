import 'package:flutter/material.dart';
import '../services/api_service.dart';

class QuestionsScreen extends StatefulWidget {
  const QuestionsScreen({super.key});

  @override
  State<QuestionsScreen> createState() => _QuestionsScreenState();
}

class _QuestionsScreenState extends State<QuestionsScreen> {
  List<dynamic> _questions = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final data = await ApiService.getQuestions();
      setState(() => _questions = data);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _showAddDialog() async {
    final axisIdController = TextEditingController();
    final textEnController = TextEditingController();
    final textRuController = TextEditingController();
    final textHeController = TextEditingController();

    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Question'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: axisIdController, decoration: const InputDecoration(labelText: 'Axis ID (e.g. economy)')),
            TextField(controller: textEnController, decoration: const InputDecoration(labelText: 'Question (EN)')),
            TextField(controller: textRuController, decoration: const InputDecoration(labelText: 'Question (RU)')),
            TextField(controller: textHeController, decoration: const InputDecoration(labelText: 'Question (HE)')),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () async {
              try {
                await ApiService.createQuestion({
                  'axis_id': axisIdController.text,
                  'text_en': textEnController.text,
                  'text_ru': textRuController.text,
                  'text_he': textHeController.text,
                  'questionnaire_version': 'v2.0'
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
                  DataColumn(label: Text('Axis')),
                  DataColumn(label: Text('Text (EN)')),
                  DataColumn(label: Text('Status')),
                  DataColumn(label: Text('Actions')),
                ],
                rows: _questions.map((e) => DataRow(
                  cells: [
                    DataCell(Text(e['id'].toString())),
                    DataCell(Text(e['axis_id'])),
                    DataCell(Text(e['text_en'])),
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
