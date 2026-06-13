import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/api_service.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class DocumentsScreen extends StatefulWidget {
  const DocumentsScreen({super.key});

  @override
  State<DocumentsScreen> createState() => _DocumentsScreenState();
}

class _DocumentsScreenState extends State<DocumentsScreen> {
  List<dynamic> _entities = [];
  String? _selectedEntityId;
  Map<String, dynamic>? _tree;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadEntities();
  }

  Future<void> _loadEntities() async {
    setState(() => _isLoading = true);
    try {
      final entityData = await ApiService.getEntities();
      setState(() {
        _entities = entityData;
        if (_entities.isNotEmpty) {
          _selectedEntityId = _entities[0]['id'];
          _loadTree(_selectedEntityId!);
        }
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _loadTree(String entityId) async {
    setState(() => _isLoading = true);
    try {
      final treeData = await ApiService.getDocumentTree(entityId);
      setState(() {
        _tree = treeData;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error loading tree: $e')));
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _uploadFile() async {
    if (_selectedEntityId == null) return;
    
    FilePickerResult? result = await FilePicker.platform.pickFiles();
    if (result != null) {
      setState(() => _isLoading = true);
      try {
        await ApiService.uploadDocument(result.files.first, _selectedEntityId!);
        await _loadTree(_selectedEntityId!);
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
        }
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _triggerScrape() async {
    if (_selectedEntityId == null) return;
    try {
      await ApiService.triggerScraping(_selectedEntityId!);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Scraping job started! Refresh in a minute.')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    }
  }

  Future<void> _openFile(String path) async {
    try {
      final response = await http.get(Uri.parse('${ApiService.baseUrl}/documents/content?filepath=$path'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _showContentDialog(path, data['content']);
      } else {
        throw Exception('Failed to load file content');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error reading file: $e')));
      }
    }
  }

  void _showContentDialog(String title, String content) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: SizedBox(
          width: double.maxFinite,
          height: 500,
          child: SingleChildScrollView(
            child: Text(content),
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

  Widget _buildNode(Map<String, dynamic> node) {
    if (node['type'] == 'directory') {
      List<dynamic> children = node['children'] ?? [];
      return ExpansionTile(
        leading: const Icon(Icons.folder, color: Colors.amber),
        title: Text(node['name']),
        initiallyExpanded: true,
        children: children.map((c) => _buildNode(c as Map<String, dynamic>)).toList(),
      );
    } else {
      return ListTile(
        leading: const Icon(Icons.insert_drive_file, color: Colors.blue),
        title: Text(node['name']),
        subtitle: Text('${(node['size'] / 1024).toStringAsFixed(1)} KB'),
        onTap: () => _openFile(node['path']),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Document Sources'),
        actions: [
          IconButton(
            icon: const Icon(Icons.folder_open),
            tooltip: 'Open Downloaded Docs Folder',
            onPressed: () async {
              final uri = Uri.parse('whereami-folder://backend');
              try {
                await launchUrl(uri);
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Could not open folder: $e')),
                  );
                }
              }
            },
          )
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                DropdownButtonFormField<String>(
                  decoration: const InputDecoration(
                    labelText: 'Select Political Entity',
                    border: OutlineInputBorder(),
                  ),
                  value: _selectedEntityId,
                  items: _entities.map((e) {
                    return DropdownMenuItem<String>(
                      value: e['id'],
                      child: Text('${e['name_en']} (${e['name_he']})'),
                    );
                  }).toList(),
                  onChanged: (val) {
                    if (val != null) {
                      setState(() => _selectedEntityId = val);
                      _loadTree(val);
                    }
                  },
                ),
                const SizedBox(height: 16),
                if (_selectedEntityId != null)
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      ElevatedButton.icon(
                        icon: const Icon(Icons.download),
                        label: const Text('Start Web Scraping'),
                        onPressed: _triggerScrape,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.blue,
                          foregroundColor: Colors.white,
                        ),
                      ),
                      const SizedBox(width: 16),
                      ElevatedButton.icon(
                        icon: const Icon(Icons.upload_file),
                        label: const Text('Upload Document'),
                        onPressed: _uploadFile,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.green,
                          foregroundColor: Colors.white,
                        ),
                      ),
                      const SizedBox(width: 16),
                      OutlinedButton.icon(
                        icon: const Icon(Icons.refresh),
                        label: const Text('Refresh Tree'),
                        onPressed: () => _loadTree(_selectedEntityId!),
                      ),
                    ],
                  ),
              ],
            ),
          ),
          const Divider(),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _tree != null && _tree!['children'] != null && (_tree!['children'] as List).isNotEmpty
                    ? ListView(
                        children: [
                          _buildNode(_tree!),
                        ],
                      )
                    : const Center(child: Text('No documents found for this entity. Click "Start Web Scraping" to fetch from web.')),
          ),
        ],
      ),
    );
  }
}
