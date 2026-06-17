import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
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
  String _searchQuery = '';
  String _displayLang = 'en';

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
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _triggerScrape(String id) async {
    try {
      await ApiService.triggerScraping(id);
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Scraping started')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Scraping error: $e')));
      }
    }
  }

  Future<void> _triggerScrapeAll() async {
    if (mounted)
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Starting bulk scrape...')));
    for (var entity in _entities) {
      try {
        await ApiService.triggerScraping(entity['id']);
        await Future.delayed(const Duration(milliseconds: 500));
      } catch (e) {
        debugPrint('Error scraping ${entity['id']}: $e');
      }
    }
    if (mounted)
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Bulk scrape jobs queued.')));
  }

  Future<void> _deduplicateEntities() async {
    setState(() => _isLoading = true);
    try {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Starting deduplication analysis...')),
        );
      final result = await ApiService.deduplicateEntities();
      final merged = (result['merged'] as List).cast<String>();

      if (mounted) {
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Deduplication Complete'),
            content: SizedBox(
              width: 500,
              child: merged.isEmpty
                  ? const Text('No duplicates found.')
                  : ListView.builder(
                      shrinkWrap: true,
                      itemCount: merged.length,
                      itemBuilder: (ctx, i) => Text('• ${merged[i]}'),
                    ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('OK'),
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

  Future<void> _discoverDiscourse(String id) async {
    setState(() => _isLoading = true);
    try {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Starting automated discourse discovery (this may take a few minutes)...',
            ),
          ),
        );
      final result = await ApiService.discoverDiscourse(id);

      final logs = (result['logs'] as List?)?.cast<String>() ?? [];

      if (mounted) {
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Discovery Log'),
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

  Future<void> _showDiscoveryLog(String id) async {
    setState(() => _isLoading = true);
    try {
      final logContent = await ApiService.getDiscoveryLog(id);

      if (mounted) {
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Last Discovery Log'),
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

  Future<void> _showStances(String id) async {
    setState(() => _isLoading = true);
    try {
      final scores = await ApiService.getEntityScores(id);
      if (mounted) {
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('AI Extracted Stances'),
            content: SizedBox(
              width: 800,
              height: 500,
              child: scores.isEmpty
                  ? const Center(
                      child: Text(
                        'No stances discovered yet. Run Discover Discourse.',
                      ),
                    )
                  : ListView.builder(
                      itemCount: scores.length,
                      itemBuilder: (ctx, i) {
                        final score = scores[i];
                        return Card(
                          margin: const EdgeInsets.only(bottom: 12),
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Axis: ${score['axis_id']}',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 16,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 8,
                                        vertical: 4,
                                      ),
                                      decoration: BoxDecoration(
                                        color: Theme.of(context).colorScheme.primary.withOpacity(0.15),
                                        borderRadius: BorderRadius.circular(4),
                                        border: Border.all(color: Theme.of(context).colorScheme.primary.withOpacity(0.3)),
                                      ),
                                      child: Text(
                                        'Score: ${score['score']}',
                                        style: TextStyle(color: Theme.of(context).colorScheme.primary, fontSize: 12, fontWeight: FontWeight.bold),
                                      ),
                                    ),
                                    const SizedBox(width: 8),
                                    Container(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 8,
                                        vertical: 4,
                                      ),
                                      decoration: BoxDecoration(
                                        color: Theme.of(context).colorScheme.secondary.withOpacity(0.15),
                                        borderRadius: BorderRadius.circular(4),
                                        border: Border.all(color: Theme.of(context).colorScheme.secondary.withOpacity(0.3)),
                                      ),
                                      child: Text(
                                        'Confidence: ${score['confidence']}',
                                        style: TextStyle(color: Theme.of(context).colorScheme.secondary, fontSize: 12, fontWeight: FontWeight.bold),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  'EN: ${score['justification_en'] ?? ''}',
                                  style: const TextStyle(
                                    fontStyle: FontStyle.italic,
                                  ),
                                ),
                                if (score['justification_ru'] != null &&
                                    score['justification_ru'].isNotEmpty)
                                  Text(
                                    'RU: ${score['justification_ru']}',
                                    style: const TextStyle(
                                      fontStyle: FontStyle.italic,
                                    ),
                                  ),
                                if (score['justification_he'] != null &&
                                    score['justification_he'].isNotEmpty)
                                  Text(
                                    'HE: ${score['justification_he']}',
                                    style: const TextStyle(
                                      fontStyle: FontStyle.italic,
                                    ),
                                  ),
                              ],
                            ),
                          ),
                        );
                      },
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

  Future<void> _deleteEntity(String id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirm Delete'),
        content: const Text('Are you sure you want to remove this entity?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              foregroundColor: Colors.white,
            ),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirm == true) {
      setState(() => _isLoading = true);
      try {
        await ApiService.deleteEntity(id);
        await _loadData();
      } catch (e) {
        if (mounted)
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(SnackBar(content: Text('Error: $e')));
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _showAddOrEditDialog({
    Map<String, dynamic>? entityToEdit,
  }) async {
    final nameController = TextEditingController(
      text: entityToEdit != null ? entityToEdit['name_$_displayLang'] : '',
    );
    final nameEnController = TextEditingController(
      text: entityToEdit?['name_en'] ?? '',
    );
    final nameRuController = TextEditingController(
      text: entityToEdit?['name_ru'] ?? '',
    );
    final nameHeController = TextEditingController(
      text: entityToEdit?['name_he'] ?? '',
    );
    String? selectedTypeId = entityToEdit?['entity_type_id'];

    if (selectedTypeId == null && _entityTypes.isNotEmpty) {
      selectedTypeId = _entityTypes.first['id'];
    }

    final isNew = entityToEdit == null;

    await showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) {
          return AlertDialog(
            title: Text(isNew ? 'Add Entity' : 'Edit Entity'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (isNew)
                  TextField(
                    controller: nameController,
                    decoration: const InputDecoration(
                      labelText: 'Name (Will be translated)',
                    ),
                  )
                else ...[
                  TextField(
                    controller: nameEnController,
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
                ],
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  initialValue: selectedTypeId,
                  decoration: const InputDecoration(labelText: 'Type'),
                  items: _entityTypes.map((type) {
                    return DropdownMenuItem<String>(
                      value: type['id'],
                      child: Text(
                        type['name_$_displayLang'] ?? type['name_en'],
                      ),
                    );
                  }).toList(),
                  onChanged: (val) {
                    setDialogState(() => selectedTypeId = val);
                  },
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: () async {
                  setState(() => _isLoading = true);
                  if (mounted) Navigator.pop(context);

                  try {
                    if (isNew) {
                      await ApiService.createEntityAuto({
                        'name': nameController.text,
                        'entity_type_id': selectedTypeId,
                      });
                    } else {
                      String generatedId = entityToEdit['id'];
                      await ApiService.updateEntity(generatedId, {
                        'id': generatedId,
                        'name_en': nameEnController.text,
                        'name_ru': nameRuController.text,
                        'name_he': nameHeController.text,
                        'entity_type_id': selectedTypeId,
                      });
                    }
                    await _loadData();
                  } catch (e) {
                    if (mounted) {
                      ScaffoldMessenger.of(
                        context,
                      ).showSnackBar(SnackBar(content: Text('Error: $e')));
                    }
                    setState(() => _isLoading = false);
                  }
                },
                child: Text(isNew ? 'Add' : 'Save'),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildStatCard({
    required String title,
    required IconData icon,
    required Color iconColor,
    required List<Widget> details,
    Widget? trailing,
    double? customWidth,
  }) {
    final screenWidth = MediaQuery.of(context).size.width;
    final cardWidth =
        customWidth ??
        (screenWidth > 1400
            ? 500.0
            : (screenWidth > 1000 ? screenWidth * 0.42 : screenWidth * 0.9));
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
                Expanded(
                  child: Text(
                    title,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      fontFamily: 'monospace',
                      color: theme.colorScheme.primary,
                    ),
                  ),
                ),
                if (trailing != null) ...[
                  const SizedBox(width: 8),
                  trailing,
                ],
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

  String _formatDate(String? isoString) {
    if (isoString == null) return 'Never';
    return isoString.split('.').first.replaceAll('T', ' ');
  }

  @override
  Widget build(BuildContext context) {
    int totalParties = 0;
    int totalLists = 0;
    int totalDocs = 0;
    String? lastEntityDate;
    String? lastDocDate;

    for (var e in _entities) {
      if (e['entity_type_id'] == 'party') {
        totalParties++;
      } else if (e['entity_type_id'] == 'list')
        totalLists++;
      else
        totalParties++; // fallback

      totalDocs += (e['doc_count'] as int? ?? 0);

      if (e['created_at'] != null) {
        if (lastEntityDate == null ||
            e['created_at'].toString().compareTo(lastEntityDate) > 0) {
          lastEntityDate = e['created_at'];
        }
      }
      if (e['last_updated_at'] != null) {
        if (lastDocDate == null ||
            e['last_updated_at'].toString().compareTo(lastDocDate) > 0) {
          lastDocDate = e['last_updated_at'];
        }
      }
    }

    final filteredEntities = _entities.where((e) {
      if (_searchQuery.isEmpty) return true;
      final query = _searchQuery.toLowerCase();
      final nameEn = (e['name_en'] ?? '').toLowerCase();
      final nameRu = (e['name_ru'] ?? '').toLowerCase();
      final nameHe = (e['name_he'] ?? '').toLowerCase();
      return nameEn.contains(query) ||
          nameRu.contains(query) ||
          nameHe.contains(query);
    }).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Political Entities'),
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: ToggleButtons(
              isSelected: [
                'en',
                'ru',
                'he',
              ].map((l) => l == _displayLang).toList(),
              onPressed: (index) {
                setState(() {
                  _displayLang = ['en', 'ru', 'he'][index];
                });
              },
              children: const [
                Padding(
                  padding: EdgeInsets.symmetric(horizontal: 12),
                  child: Text('EN'),
                ),
                Padding(
                  padding: EdgeInsets.symmetric(horizontal: 12),
                  child: Text('RU'),
                ),
                Padding(
                  padding: EdgeInsets.symmetric(horizontal: 12),
                  child: Text('HE'),
                ),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: PopupMenuButton<String>(
        onSelected: (val) {
          if (val == 'add') {
            _showAddOrEditDialog();
          } else if (val == 'scrap')
            _triggerScrapeAll();
          else if (val == 'dedup')
            _deduplicateEntities();
        },
        itemBuilder: (context) => [
          const PopupMenuItem(value: 'add', child: Text('Add New Entity')),
          const PopupMenuItem(
            value: 'scrap',
            child: Text('Scrap All Entities'),
          ),
          const PopupMenuItem(
            value: 'dedup',
            child: Text('Maintenance: Deduplicate'),
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
          : SingleChildScrollView(
              padding: const EdgeInsets.all(32),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Wrap(
                    children: [
                      _buildStatCard(
                        title: 'Global Counters',
                        icon: Icons.pie_chart,
                        iconColor: Colors.blue,
                        customWidth: 400,
                        details: [
                          Text(
                            'Total Entities: ${_entities.length}',
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 4),
                          Text('Parties: $totalParties  |  Lists: $totalLists'),
                        ],
                      ),
                      _buildStatCard(
                        title: 'Scraping Activity',
                        icon: Icons.history,
                        iconColor: Colors.orange,
                        customWidth: 400,
                        details: [
                          Text(
                            'Total Scraped Docs: $totalDocs',
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Last Entity Discovered: ${_formatDate(lastEntityDate)}',
                            style: const TextStyle(fontSize: 12),
                          ),
                          Text(
                            'Last Docs Scraped: ${_formatDate(lastDocDate)}',
                            style: const TextStyle(fontSize: 12),
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  Row(
                    children: [
                      const Text(
                        'Registered Entities',
                        style: TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.w300,
                        ),
                      ),
                      const SizedBox(width: 32),
                      SizedBox(
                        width: 300,
                        child: TextField(
                          decoration: const InputDecoration(
                            hintText: 'Search entities...',
                            prefixIcon: Icon(Icons.search),
                            border: OutlineInputBorder(),
                            isDense: true,
                          ),
                          onChanged: (val) =>
                              setState(() => _searchQuery = val),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Wrap(
                    spacing: 20,
                    runSpacing: 20,
                    children: filteredEntities.map((e) {
                      final mainName = e['name_$_displayLang'] ?? e['name_en'];
                      return _buildStatCard(
                        title: mainName,
                        icon: Icons.account_balance,
                        iconColor: Theme.of(context).colorScheme.primary,
                        details: [
                          if (_displayLang != 'en')
                            Text(
                              'EN: ${e['name_en']}',
                              style: TextStyle(color: Theme.of(context).colorScheme.secondary),
                            ),
                          if (_displayLang != 'ru')
                            Text(
                              'RU: ${e['name_ru']}',
                              style: TextStyle(color: Theme.of(context).colorScheme.secondary),
                            ),
                          if (_displayLang != 'he')
                            Text(
                              'HE: ${e['name_he']}',
                              style: TextStyle(color: Theme.of(context).colorScheme.secondary),
                            ),
                          const SizedBox(height: 4),
                          Text(
                            'Type: ${e['entity_type_id'] ?? 'party'}  |  Docs: ${e['doc_count'] ?? 0}',
                            style: const TextStyle(fontWeight: FontWeight.w500),
                          ),
                          const SizedBox(height: 16),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: [
                              ElevatedButton.icon(
                                icon: const Icon(Icons.edit, size: 16),
                                label: const Text('Edit'),
                                onPressed: () =>
                                    _showAddOrEditDialog(entityToEdit: e),
                                style: ElevatedButton.styleFrom(
                                  visualDensity: VisualDensity.compact,
                                ),
                              ),
                              ElevatedButton.icon(
                                icon: const Icon(Icons.explore, size: 16),
                                label: const Text('Discover Discourse'),
                                onPressed: () => _discoverDiscourse(e['id']),
                                style: ElevatedButton.styleFrom(
                                  visualDensity: VisualDensity.compact,
                                ),
                              ),
                              ElevatedButton.icon(
                                icon: const Icon(
                                  Icons.remove_red_eye,
                                  size: 16,
                                ),
                                label: const Text('Show Stances'),
                                onPressed: () => _showStances(e['id']),
                                style: ElevatedButton.styleFrom(
                                  visualDensity: VisualDensity.compact,
                                ),
                              ),
                              ElevatedButton.icon(
                                icon: const Icon(Icons.article, size: 16),
                                label: const Text('Show Log'),
                                onPressed: () => _showDiscoveryLog(e['id']),
                                style: ElevatedButton.styleFrom(
                                  visualDensity: VisualDensity.compact,
                                ),
                              ),
                              ElevatedButton.icon(
                                icon: const Icon(Icons.download, size: 16),
                                label: const Text('Scrap'),
                                onPressed: () => _triggerScrape(e['id']),
                                style: ElevatedButton.styleFrom(
                                  visualDensity: VisualDensity.compact,
                                ),
                              ),
                              OutlinedButton.icon(
                                icon: const Icon(Icons.folder_open, size: 16),
                                label: const Text('Folder'),
                                onPressed: () => launchUrl(
                                  Uri.parse(
                                    'whereami-folder://${Uri.encodeComponent(e['name_en'])}',
                                  ),
                                ),
                                style: OutlinedButton.styleFrom(
                                  visualDensity: VisualDensity.compact,
                                ),
                              ),
                              TextButton.icon(
                                icon: const Icon(Icons.delete, size: 16),
                                label: const Text('Remove'),
                                onPressed: () => _deleteEntity(e['id']),
                                style: TextButton.styleFrom(
                                  foregroundColor: Colors.redAccent,
                                  visualDensity: VisualDensity.compact,
                                ),
                              ),
                            ],
                          ),
                        ],
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
    );
  }
}
