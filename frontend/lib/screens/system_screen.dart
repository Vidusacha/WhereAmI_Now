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

  Future<void> _launchSSH(String containerName) async {
    final uri = Uri.parse('whereami-ssh://$containerName/');
    try {
      await launchUrl(uri);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not launch SSH terminal: $e')),
        );
      }
    }
  }

  Future<void> _launchDBeaver() async {
    final uri = Uri.parse('whereami-dbeaver://');
    try {
      await launchUrl(uri);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not launch DBeaver: $e')),
        );
      }
    }
  }

  void _showLogsDialog(String containerName, String logs) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text('Logs: $containerName'),
          content: Container(
            width: 800,
            height: 600,
            color: Colors.black,
            padding: const EdgeInsets.all(16),
            child: SingleChildScrollView(
              child: Text(
                logs,
                style: const TextStyle(
                  fontFamily: 'monospace',
                  color: Colors.lightGreenAccent,
                  fontSize: 14,
                ),
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Close'),
            ),
          ],
        );
      },
    );
  }

  Widget _buildProgressIndicator(String label, double percent) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontSize: 14)),
        const SizedBox(height: 6),
        LinearProgressIndicator(
          value: percent / 100,
          backgroundColor: Colors.grey.shade200,
          valueColor: AlwaysStoppedAnimation<Color>(
            percent > 85 ? Colors.red : (percent > 60 ? Colors.orange : Colors.green),
          ),
          minHeight: 8,
          borderRadius: BorderRadius.circular(4),
        ),
      ],
    );
  }

  Widget _buildStatCard({
    required String title,
    required IconData icon,
    required Color iconColor,
    required List<Widget> details,
    Widget? trailing,
  }) {
    return Container(
      width: 400,
      margin: const EdgeInsets.only(right: 20, bottom: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.blueGrey.withOpacity(0.08),
            blurRadius: 15,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: iconColor.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(icon, color: iconColor, size: 28),
                    ),
                    const SizedBox(width: 16),
                    Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.black87)),
                  ],
                ),
                if (trailing != null) trailing,
              ],
            ),
            const SizedBox(height: 24),
            ...details,
          ],
        ),
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
        padding: const EdgeInsets.all(32.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (_error.isNotEmpty)
              Container(
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 24),
                decoration: BoxDecoration(
                  color: Colors.red.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.red.shade200),
                ),
                child: Text(_error, style: TextStyle(color: Colors.red.shade700)),
              ),
            
            Wrap(
              alignment: WrapAlignment.start,
              crossAxisAlignment: WrapCrossAlignment.start,
              children: [
                // Local Model Card
                _buildStatCard(
                  title: 'Local Model Status',
                  icon: Icons.smart_toy,
                  iconColor: _ollamaStats?['status'] == 'online' ? Colors.green : Colors.red,
                  trailing: TextButton.icon(
                    onPressed: () => launchUrl(Uri.parse('whereami-ollamalog://')),
                    icon: const Icon(Icons.description, size: 18),
                    label: const Text('Logs'),
                    style: TextButton.styleFrom(
                      backgroundColor: Colors.blue.shade50,
                      foregroundColor: Colors.blue.shade700,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                  ),
                  details: [
                    Text('Status: ${_ollamaStats?['status'] ?? 'Unknown'}', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500)),
                    const SizedBox(height: 6),
                    Text('Host: ${_ollamaStats?['host'] ?? '?'}', style: const TextStyle(fontSize: 14, color: Colors.grey)),
                    const SizedBox(height: 12),
                    if (_ollamaStats?['error'] != null)
                      Text('Error: ${_ollamaStats?['error']}', style: const TextStyle(fontSize: 14, color: Colors.red)),
                    if (_ollamaStats?['models'] != null && (_ollamaStats!['models'] as List).isNotEmpty)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        decoration: BoxDecoration(color: Colors.blueGrey.shade50, borderRadius: BorderRadius.circular(6)),
                        child: Text('Models: ${(_ollamaStats!['models'] as List).map((m) => m['name']).join(', ')}', style: const TextStyle(fontSize: 13, color: Colors.blueGrey)),
                      )
                    else if (_ollamaStats?['status'] == 'online')
                      const Text('No models downloaded.', style: TextStyle(fontSize: 14, color: Colors.orange)),
                  ],
                ),

                // Host Card
                _buildStatCard(
                  title: 'Host Node',
                  icon: Icons.computer,
                  iconColor: Colors.indigo,
                  details: [
                    _buildProgressIndicator('CPU Usage', _hostStats?['cpu_percent']?.toDouble() ?? 0.0),
                    const SizedBox(height: 16),
                    _buildProgressIndicator('RAM (${_hostStats?['mem_used_mb'] ?? '?'} / ${_hostStats?['mem_total_mb'] ?? '?'} MB)', _hostStats?['mem_percent']?.toDouble() ?? 0.0),
                    const SizedBox(height: 16),
                    _buildProgressIndicator('Disk (${_hostStats?['disk_used_gb'] ?? '?'} / ${_hostStats?['disk_total_gb'] ?? '?'} GB)', _hostStats?['disk_percent']?.toDouble() ?? 0.0),
                  ],
                ),

                // DB Card
                _buildStatCard(
                  title: 'PostgreSQL',
                  icon: Icons.storage,
                  iconColor: _dbStats?['status']?.toString().toLowerCase() == 'online' ? Colors.blue : Colors.red,
                  trailing: ElevatedButton.icon(
                    onPressed: _launchDBeaver,
                    icon: const Icon(Icons.open_in_new, size: 16),
                    label: const Text('DBeaver'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue.shade600,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                  ),
                  details: [
                    Text('Status: ${_dbStats?['status'] ?? 'Unknown'}', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500)),
                    const SizedBox(height: 6),
                    Text('Data Size: ${_dbStats?['size'] ?? '?'}', style: const TextStyle(fontSize: 14)),
                    const SizedBox(height: 12),
                    if (_dbStats?['tables'] != null)
                      Text('${(_dbStats!['tables'] as List).length} Tables Total', style: const TextStyle(fontSize: 14, color: Colors.grey)),
                  ],
                ),
              ],
            ),
            
            const SizedBox(height: 32),
            const Text('Docker Containers', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.black87)),
            const SizedBox(height: 20),
            
            Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(color: Colors.blueGrey.withOpacity(0.08), blurRadius: 15, offset: const Offset(0, 5)),
                ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: DataTable(
                    headingRowColor: MaterialStateProperty.all(Colors.grey.shade50),
                    dataRowMinHeight: 60,
                    dataRowMaxHeight: 60,
                    columns: const [
                      DataColumn(label: Text('Container Name', style: TextStyle(fontWeight: FontWeight.bold))),
                      DataColumn(label: Text('Status', style: TextStyle(fontWeight: FontWeight.bold))),
                      DataColumn(label: Text('CPU %', style: TextStyle(fontWeight: FontWeight.bold))),
                      DataColumn(label: Text('Memory (MB)', style: TextStyle(fontWeight: FontWeight.bold))),
                      DataColumn(label: Text('Mem %', style: TextStyle(fontWeight: FontWeight.bold))),
                      DataColumn(label: Text('Actions', style: TextStyle(fontWeight: FontWeight.bold))),
                    ],
                    rows: _dockerStats.map((c) {
                      final isRunning = c['status'] == 'running';
                      return DataRow(
                        cells: [
                          DataCell(Text(c['name'], style: const TextStyle(fontWeight: FontWeight.w600))),
                          DataCell(
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                              decoration: BoxDecoration(
                                color: isRunning ? Colors.green.shade50 : Colors.red.shade50,
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(color: isRunning ? Colors.green.shade200 : Colors.red.shade200),
                              ),
                              child: Text(
                                c['status'],
                                style: TextStyle(
                                  color: isRunning ? Colors.green.shade700 : Colors.red.shade700,
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
                                  icon: const Icon(Icons.list_alt, color: Colors.blueGrey),
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
              ),
            ),
          ],
        ),
      ),
    );
  }
}
