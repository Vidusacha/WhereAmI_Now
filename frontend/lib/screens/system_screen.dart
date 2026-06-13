import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:url_launcher/url_launcher.dart';
import '../services/api_service.dart';

class SystemScreen extends StatefulWidget {
  const SystemScreen({super.key});

  @override
  State<SystemScreen> createState() => _SystemScreenState();
}

class _SystemScreenState extends State<SystemScreen> {
  bool _isLoading = true;
  List<dynamic> _dockerStats = [];
  Map<String, dynamic>? _dbStats;
  Map<String, dynamic>? _hostStats;
  Map<String, dynamic>? _ollamaStats;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _fetchSystemStats();
  }

  Future<void> _fetchSystemStats() async {
    setState(() => _isLoading = true);
    try {
      final baseUrl = ApiService.baseUrl;
      final dockerRes = await http.get(Uri.parse('$baseUrl/system/docker'));
      final dbRes = await http.get(Uri.parse('$baseUrl/system/db'));
      final hostRes = await http.get(Uri.parse('$baseUrl/system/host'));
      final ollamaRes = await http.get(Uri.parse('$baseUrl/system/ollama'));

      if (dockerRes.statusCode == 200) {
        _dockerStats = jsonDecode(dockerRes.body);
      } else {
        _error += 'Failed to load Docker stats: ${dockerRes.body}\n';
      }

      if (dbRes.statusCode == 200) {
        _dbStats = jsonDecode(dbRes.body);
      } else {
        _error += 'Failed to load DB stats: ${dbRes.body}\n';
      }

      if (hostRes.statusCode == 200) {
        _hostStats = jsonDecode(hostRes.body);
      } else {
        _error += 'Failed to load Host stats: ${hostRes.body}\n';
      }

      if (ollamaRes.statusCode == 200) {
        _ollamaStats = jsonDecode(ollamaRes.body);
      } else {
        _error += 'Failed to load Ollama stats: ${ollamaRes.body}\n';
      }
    } catch (e) {
      _error = 'Network error: $e';
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _launchDBeaver() async {
    final Uri url = Uri.parse('whereami-dbeaver://');
    try {
      await launchUrl(url, webOnlyWindowName: '_self');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to launch DBeaver: $e')),
        );
      }
    }
  }

  Future<void> _launchSSH(String containerName) async {
    final Uri url = Uri.parse('whereami-ssh://$containerName/');
    try {
      await launchUrl(url, webOnlyWindowName: '_self');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to launch SSH: $e')),
        );
      }
    }
  }

  void _showLogsDialog(String containerName, List<dynamic> logs) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Logs: $containerName'),
        content: Container(
          width: 800,
          height: 400,
          color: Colors.black87,
          padding: const EdgeInsets.all(8.0),
          child: SingleChildScrollView(
            child: Text(
              logs.join('\n'),
              style: const TextStyle(fontFamily: 'monospace', color: Colors.greenAccent, fontSize: 12),
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

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('System Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _fetchSystemStats,
            tooltip: 'Refresh Stats',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (_error.isNotEmpty)
              Container(
                padding: const EdgeInsets.all(8),
                color: Colors.red.shade100,
                child: Text(_error, style: const TextStyle(color: Colors.red)),
              ),
            
            Wrap(
              spacing: 24,
              runSpacing: 24,
              children: [
                // Ollama Card
                SizedBox(
                  width: 450,
                  child: Card(
              elevation: 4,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Local Model Status', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                        ElevatedButton.icon(
                          onPressed: () => launchUrl(Uri.parse('whereami-ollamalog://')),
                          icon: const Icon(Icons.description),
                          label: const Text('Show Log'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Icon(Icons.smart_toy, color: _ollamaStats?['status'] == 'online' ? Colors.green : Colors.red, size: 32),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Status: ${_ollamaStats?['status'] ?? 'Unknown'}', style: const TextStyle(fontSize: 16)),
                              Text('Host: ${_ollamaStats?['host'] ?? '?'}', style: const TextStyle(fontSize: 14, color: Colors.grey)),
                              if (_ollamaStats?['error'] != null)
                                Text('Error: ${_ollamaStats?['error']}', style: const TextStyle(fontSize: 14, color: Colors.red)),
                              if (_ollamaStats?['models'] != null)
                                Text('Models: ${(_ollamaStats!['models'] as List).map((m) => m['name']).join(', ')}', style: const TextStyle(fontSize: 14)),
                            ],
                          ),
                    elevation: 4,
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Text('Local Model Status', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                              ElevatedButton.icon(
                                onPressed: () => launchUrl(Uri.parse('whereami-ollamalog://')),
                                icon: const Icon(Icons.description),
                                label: const Text('Show Log'),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              Icon(Icons.smart_toy, color: _ollamaStats?['status'] == 'online' ? Colors.green : Colors.red, size: 32),
                              const SizedBox(width: 16),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('Status: ${_ollamaStats?['status'] ?? 'Unknown'}', style: const TextStyle(fontSize: 16)),
                                    Text('Host: ${_ollamaStats?['host'] ?? '?'}', style: const TextStyle(fontSize: 14, color: Colors.grey)),
                                    if (_ollamaStats?['error'] != null)
                                      Text('Error: ${_ollamaStats?['error']}', style: const TextStyle(fontSize: 14, color: Colors.red)),
                                    if (_ollamaStats?['models'] != null)
                                      Text('Models: ${(_ollamaStats!['models'] as List).map((m) => m['name']).join(', ')}', style: const TextStyle(fontSize: 14)),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
            
                // Host Card
                SizedBox(
                  width: 450,
                  child: Card(
                    elevation: 4,
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Host Computer Parameters', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              const Icon(Icons.computer, color: Colors.blueGrey, size: 32),
                              const SizedBox(width: 16),
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('CPU Usage: ${_hostStats?['cpu_percent'] ?? '?'} %', style: const TextStyle(fontSize: 16)),
                                  Text('RAM: ${_hostStats?['mem_used_mb'] ?? '?'} MB / ${_hostStats?['mem_total_mb'] ?? '?'} MB (${_hostStats?['mem_percent'] ?? '?'}%)', style: const TextStyle(fontSize: 16)),
                                  Text('Disk: ${_hostStats?['disk_used_gb'] ?? '?'} GB / ${_hostStats?['disk_total_gb'] ?? '?'} GB (${_hostStats?['disk_percent'] ?? '?'}%)', style: const TextStyle(fontSize: 16)),
                                ],
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
            
                // Database Card
                SizedBox(
                  width: 450,
                  child: Card(
                    elevation: 4,
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('PostgreSQL Database', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              Icon(
                                _dbStats?['status']?.toString().toLowerCase() == 'online' ? Icons.check_circle : Icons.error,
                                color: _dbStats?['status']?.toString().toLowerCase() == 'online' ? Colors.green : Colors.red,
                                size: 32,
                              ),
                              const SizedBox(width: 16),
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('Status: ${_dbStats?['status'] ?? 'Unknown'}', style: const TextStyle(fontSize: 16)),
                                  Text('Data Size: ${_dbStats?['size'] ?? '?'}', style: const TextStyle(fontSize: 16)),
                                ],
                              ),
                              const Spacer(),
                              ElevatedButton.icon(
                                onPressed: _launchDBeaver,
                                icon: const Icon(Icons.storage),
                                label: const Text('Launch DBeaver'),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.blue.shade800,
                                  foregroundColor: Colors.white,
                                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
            
            const SizedBox(height: 32),
            
            // Docker Containers Card
            Card(
              elevation: 4,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Docker Containers', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 16),
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: DataTable(
                        headingRowColor: MaterialStateProperty.all(Colors.grey.shade200),
                        columns: const [
                          DataColumn(label: Text('Container Name')),
                          DataColumn(label: Text('Status')),
                          DataColumn(label: Text('CPU %')),
                          DataColumn(label: Text('Memory (MB)')),
                          DataColumn(label: Text('Mem %')),
                          DataColumn(label: Text('Actions')),
                        ],
                        rows: _dockerStats.map((c) {
                          final isRunning = c['status'] == 'running';
                          return DataRow(
                            cells: [
                              DataCell(Text(c['name'], style: const TextStyle(fontWeight: FontWeight.bold))),
                              DataCell(
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: isRunning ? Colors.green.shade100 : Colors.red.shade100,
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Text(
                                    c['status'],
                                    style: TextStyle(
                                      color: isRunning ? Colors.green.shade800 : Colors.red.shade800,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                              ),
                              DataCell(Text('${c['cpu_percent']}%')),
                              DataCell(Text('${c['mem_mb']} MB')),
                              DataCell(Text('${c['mem_percent']}%')),
                              DataCell(
                                Row(
                                  children: [
                                    IconButton(
                                      icon: const Icon(Icons.terminal, color: Colors.blue),
                                      tooltip: 'SSH Terminal',
                                      onPressed: () => _launchSSH(c['name']),
                                    ),
                                    IconButton(
                                      icon: const Icon(Icons.list_alt, color: Colors.grey),
                                      tooltip: 'View Logs',
                                      onPressed: () => _showLogsDialog(c['name'], c['logs']),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          );
                        }).toList(),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
