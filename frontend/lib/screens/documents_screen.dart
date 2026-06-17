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
  Map<String, dynamic>? _selectedEntity;
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
          _selectedEntity = _entities[0];
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

  Widget _buildStatCard({
    required String title,
    required IconData icon,
    required Color iconColor,
    required List<Widget> details,
    Widget? trailing,
  }) {
    final screenWidth = MediaQuery.of(context).size.width;
    final cardWidth = screenWidth > 1400 ? 600.0 : (screenWidth > 1000 ? screenWidth * 0.42 : screenWidth * 0.9);
    final theme = Theme.of(context);

    return Container(
      width: cardWidth,
      margin: const EdgeInsets.only(right: 20, bottom: 20),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: theme.colorScheme.primary.withOpacity(0.3), width: 1.5),
        boxShadow: [
          BoxShadow(
            color: theme.colorScheme.primary.withOpacity(0.08),
            blurRadius: 10,
            spreadRadius: 1,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    fontFamily: 'monospace',
                    color: theme.colorScheme.primary,
                  ),
                ),
                if (trailing != null) trailing,
              ],
            ),
            const SizedBox(height: 20),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(icon, color: iconColor, size: 36),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: details,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Document Sources'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            DropdownButtonFormField<String>(
              decoration: const InputDecoration(
                labelText: 'Select Political Entity',
                border: OutlineInputBorder(),
                filled: true,
                fillColor: Colors.white,
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
                  setState(() {
                    _selectedEntityId = val;
                    _selectedEntity = _entities.firstWhere((e) => e['id'] == val);
                  });
                  _loadTree(val);
                }
              },
            ),
            const SizedBox(height: 24),
            
            if (_selectedEntity != null)
              Wrap(
                alignment: WrapAlignment.start,
                crossAxisAlignment: WrapCrossAlignment.start,
                children: [
                  _buildStatCard(
                    title: 'Entity Documents',
                    icon: Icons.article,
                    iconColor: Theme.of(context).colorScheme.primary,
                    trailing: TextButton.icon(
                      onPressed: () async {
                        final encodedName = Uri.encodeComponent(_selectedEntity!['name_en']);
                        final uri = Uri.parse('whereami-folder://$encodedName');
                        try {
                          await launchUrl(uri);
                        } catch (e) {
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Could not open folder: $e')));
                          }
                        }
                      },
                      icon: const Icon(Icons.folder_open, size: 18),
                      label: const Text('Open Folder'),
                      style: TextButton.styleFrom(
                        backgroundColor: Theme.of(context).colorScheme.primary.withOpacity(0.15),
                        foregroundColor: Theme.of(context).colorScheme.primary,
                      ),
                    ),
                    details: [
                      Text('Scraped Documents: ${_selectedEntity!['doc_count'] ?? 0}', style: const TextStyle(fontSize: 16)),
                      const SizedBox(height: 8),
                      Text('Last Updated: ${_selectedEntity!['last_updated_at'] != null ? _selectedEntity!['last_updated_at'].toString().split('.').first.replaceAll('T', ' ') : 'Never'}', style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withOpacity(0.7))),
                    ],
                  ),
                  
                  _buildStatCard(
                    title: 'Actions',
                    icon: Icons.settings,
                    iconColor: Theme.of(context).colorScheme.secondary,
                    details: [
                      Wrap(
                        spacing: 12,
                        runSpacing: 12,
                        children: [
                          ElevatedButton.icon(
                            icon: const Icon(Icons.download),
                            label: const Text('Start Web Scraping'),
                            onPressed: _triggerScrape,
                          ),
                          ElevatedButton.icon(
                            icon: const Icon(Icons.upload_file),
                            label: const Text('Upload Document'),
                            onPressed: _uploadFile,
                          ),
                          OutlinedButton.icon(
                            icon: const Icon(Icons.refresh),
                            label: const Text('Refresh Tree'),
                            onPressed: () => _loadTree(_selectedEntityId!),
                          ),
                        ],
                      )
                    ]
                  )
                ]
              ),
              
            const SizedBox(height: 16),
            const Divider(),
            const SizedBox(height: 16),
            
            Container(
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Theme.of(context).colorScheme.primary.withOpacity(0.3)),
              ),
              constraints: const BoxConstraints(minHeight: 300),
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : _tree != null && _tree!['children'] != null && (_tree!['children'] as List).isNotEmpty
                      ? ListView(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          children: [
                            _buildNode(_tree!),
                          ],
                        )
                      : Center(
                          child: Padding(
                            padding: const EdgeInsets.all(32.0),
                            child: Text(
                              'No documents found for this entity. Click "Start Web Scraping" to fetch from web.',
                              style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withOpacity(0.5)),
                            ),
                          ),
                        ),
            ),
          ],
        ),
      ),
    );
  }
}
