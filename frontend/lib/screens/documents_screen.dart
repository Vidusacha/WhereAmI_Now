import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:html' as html;
import '../services/api_service.dart';

class DocumentsScreen extends StatefulWidget {
  const DocumentsScreen({super.key});

  @override
  State<DocumentsScreen> createState() => _DocumentsScreenState();
}

class _DocumentsScreenState extends State<DocumentsScreen> {
  Map<String, dynamic> _tree = {};
  List<dynamic> _entities = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final treeData = await ApiService.getDocumentTree();
      final entityData = await ApiService.getEntities();
      setState(() {
        _tree = treeData;
        _entities = entityData;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _uploadFile(String? entityId) async {
    FilePickerResult? result = await FilePicker.platform.pickFiles();
    
    if (result != null) {
      setState(() => _isLoading = true);
      try {
        await ApiService.uploadDocument(result.files.first, entityId);
        await _loadData();
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
        }
        setState(() => _isLoading = false);
      }
    }
  }

  void _openFile(String filePath) {
    // Convert local file_path to API url if needed
    // Assuming backend returns something like 'data/entities/likud/file.pdf'
    // We should hit http://localhost:8000/api/documents/files/{path}
    // Note: The backend route is /api/documents/files/{path:path}
    // We need to clean the path depending on how it's stored.
    String cleanPath = filePath.replaceAll('\\', '/');
    if (cleanPath.startsWith('data/entities/')) {
      cleanPath = cleanPath.replaceFirst('data/entities/', '');
    }
    
    final url = '${ApiService.baseUrl}/documents/files/$cleanPath';
    html.window.open(url, '_blank');
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    final keys = _tree.keys.toList()..sort();

    return Scaffold(
      floatingActionButton: FloatingActionButton(
        onPressed: () => _uploadFile(null), // Upload to Unassigned by default
        tooltip: 'Upload Unassigned Document',
        child: const Icon(Icons.upload_file),
      ),
      body: ListView.builder(
        itemCount: keys.length,
        itemBuilder: (context, index) {
          final folderName = keys[index];
          final List<dynamic> documents = _tree[folderName];

          // Find entity ID for this folder to pass to upload
          String? entityId;
          if (folderName != 'Unassigned') {
            try {
              entityId = _entities.firstWhere((e) => e['name_en'] == folderName)['id'];
            } catch (_) {}
          }

          return ExpansionTile(
            leading: const Icon(Icons.folder),
            title: Text('$folderName (${documents.length})'),
            trailing: IconButton(
              icon: const Icon(Icons.upload),
              tooltip: 'Upload to this entity',
              onPressed: () => _uploadFile(entityId),
            ),
            children: documents.map((doc) {
              return ListTile(
                leading: const Icon(Icons.insert_drive_file),
                title: Text(doc['source_url'].toString().split('/').last), // Simple filename display
                subtitle: Text(doc['scraped_at']),
                onTap: () => _openFile(doc['file_path']),
              );
            }).toList(),
          );
        },
      ),
    );
  }
}
