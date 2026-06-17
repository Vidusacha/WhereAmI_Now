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
  String _activeTab = 'Overview'; // Track active tab like in Figma design
  String _displayLang = 'EN'; // Selected language in header (EN, RU, HE)

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
        _error += 'Failed to load Docker stats\n';
      }

      if (dbRes.statusCode == 200) {
        _dbStats = jsonDecode(dbRes.body);
      } else {
        _error += 'Failed to load DB stats\n';
      }

      if (hostRes.statusCode == 200) {
        _hostStats = jsonDecode(hostRes.body);
      } else {
        _error += 'Failed to load Host stats\n';
      }

      if (ollamaRes.statusCode == 200) {
        _ollamaStats = jsonDecode(ollamaRes.body);
      } else {
        _error += 'Failed to load Ollama stats\n';
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
          backgroundColor: const Color(0xFF000500),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
            side: const BorderSide(color: Color(0xFF00FF41), width: 1.5),
          ),
          title: Text(
            'LOGS: $containerName',
            style: const TextStyle(
              fontFamily: 'monospace',
              color: Color(0xFF00FF41),
              fontWeight: FontWeight.bold,
            ),
          ),
          content: Container(
            width: 800,
            height: 500,
            color: Colors.black,
            padding: const EdgeInsets.all(16),
            child: SingleChildScrollView(
              child: Text(
                logs.isEmpty ? "No recent log entries found." : logs,
                style: const TextStyle(
                  fontFamily: 'monospace',
                  color: Color(0xFF33FF33),
                  fontSize: 13,
                ),
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text(
                'CLOSE',
                style: TextStyle(color: Color(0xFF00FF41), fontFamily: 'monospace'),
              ),
            ),
          ],
        );
      },
    );
  }

  Future<void> _showGlobalDiscourseLogDialog() async {
    try {
      String logContent = await ApiService.getGlobalDiscourseLog();
      if (mounted) {
        showDialog(
          context: context,
          builder: (context) {
            return StatefulBuilder(
              builder: (context, setStateDialog) {
                return AlertDialog(
                  backgroundColor: const Color(0xFF000500),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                    side: const BorderSide(color: Color(0xFF00FF41), width: 1.5),
                  ),
                  title: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'GLOBAL DISCOURSE LOG',
                        style: TextStyle(
                          fontFamily: 'monospace',
                          color: Color(0xFF00FF41),
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.refresh, color: Color(0xFF00FF41)),
                        onPressed: () async {
                          try {
                            final newLog = await ApiService.getGlobalDiscourseLog();
                            setStateDialog(() {
                              logContent = newLog;
                            });
                          } catch (_) {}
                        },
                      ),
                    ],
                  ),
                  content: Container(
                    width: 800,
                    height: 500,
                    color: Colors.black,
                    padding: const EdgeInsets.all(16),
                    child: SingleChildScrollView(
                      child: Text(
                        logContent.isEmpty ? "No global discourse log found." : logContent,
                        style: const TextStyle(
                          fontFamily: 'monospace',
                          color: Color(0xFF33FF33),
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: const Text(
                        'CLOSE',
                        style: TextStyle(color: Color(0xFF00FF41), fontFamily: 'monospace'),
                      ),
                    ),
                  ],
                );
              }
            );
          }
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error fetching global discourse log: $e')),
        );
      }
    }
  }

  BoxDecoration _matrixBoxDecoration({double opacity = 0.4}) {
    return BoxDecoration(
      color: const Color(0xFF071207),
      borderRadius: BorderRadius.circular(8),
      border: Border.all(color: const Color(0xFF00FF41).withOpacity(opacity), width: 1.5),
      boxShadow: [
        BoxShadow(
          color: const Color(0xFF00FF41).withOpacity(0.08),
          blurRadius: 8,
          spreadRadius: 1,
        )
      ],
    );
  }

  Widget _buildMetricCard(String label, String value, IconData icon) {
    return Container(
      width: 250,
      height: 110,
      margin: const EdgeInsets.only(right: 16, bottom: 16),
      decoration: _matrixBoxDecoration(opacity: 0.3),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                label.toUpperCase(),
                style: const TextStyle(
                  color: Color(0xFF008F11),
                  fontSize: 11,
                  fontFamily: 'monospace',
                  fontWeight: FontWeight.bold,
                ),
              ),
              Icon(icon, color: const Color(0xFF00FF41), size: 16),
            ],
          ),
          const Spacer(),
          Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: Color(0xFF00FF41),
              fontSize: 24,
              fontWeight: FontWeight.bold,
              fontFamily: 'monospace',
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHostProgress(String label, double percent, String details) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: const TextStyle(color: Color(0xFF00FF41), fontSize: 13, fontFamily: 'monospace'),
            ),
            Text(
              details,
              style: const TextStyle(color: Color(0xFF008F11), fontSize: 12, fontFamily: 'monospace'),
            ),
          ],
        ),
        const SizedBox(height: 6),
        LinearProgressIndicator(
          value: percent / 100,
          backgroundColor: Colors.black,
          valueColor: AlwaysStoppedAnimation<Color>(
            percent > 85 ? Colors.redAccent : (percent > 65 ? Colors.orangeAccent : const Color(0xFF00FF41)),
          ),
          minHeight: 6,
          borderRadius: BorderRadius.circular(3),
        ),
      ],
    );
  }

  List<dynamic> _extractActivityLogs() {
    List<dynamic> logsList = [];
    for (var c in _dockerStats) {
      final String rawLogs = c['logs'] ?? '';
      final lines = rawLogs.split('\n');
      for (var line in lines) {
        if (line.trim().length > 10) {
          logsList.add({
            "container": c['name'],
            "message": line.trim(),
            "time": "Recent"
          });
        }
      }
    }
    // Return top 6 log messages
    return logsList.reversed.take(6).toList();
  }

  IconData _getLogIcon(String msg) {
    msg = msg.toLowerCase();
    if (msg.contains('error') || msg.contains('fail') || msg.contains('exception')) {
      return Icons.warning_amber_outlined;
    }
    if (msg.contains('connect') || msg.contains('start') || msg.contains('listen')) {
      return Icons.terminal;
    }
    return Icons.check_circle_outline;
  }

  Color _getLogIconColor(String msg) {
    msg = msg.toLowerCase();
    if (msg.contains('error') || msg.contains('fail') || msg.contains('exception')) {
      return Colors.orangeAccent;
    }
    return const Color(0xFF00FF41);
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF00FF41)));
    }

    final screenWidth = MediaQuery.of(context).size.width;
    final isDesktop = screenWidth > 1200;

    // Calculate database totals
    int totalDbRows = 0;
    if (_dbStats?['tables'] != null) {
      for (var t in _dbStats!['tables']) {
        totalDbRows += (t['rows'] as int? ?? 0);
      }
    }

    // Calculate running containers
    int runningContainers = 0;
    for (var c in _dockerStats) {
      if (c['status'] == 'running') runningContainers++;
    }

    final activityLogs = _extractActivityLogs();

    return Scaffold(
      backgroundColor: Colors.transparent, // Background transparent to let matrix code show through
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 40.0, vertical: 32.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // --- HEADER ---
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'MATRIX CONTROL SYSTEM',
                      style: TextStyle(
                        color: Color(0xFF00FF41),
                        fontFamily: 'monospace',
                        fontSize: 26,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 2.0,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'System Status: ${runningContainers > 0 ? "ONLINE" : "OFFLINE"}',
                      style: TextStyle(
                        color: runningContainers > 0 ? const Color(0xFF00FF41) : Colors.redAccent,
                        fontFamily: 'monospace',
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                // Language buttons
                Row(
                  children: ['EN', 'RU', 'HE'].map((lang) {
                    final isActive = _displayLang == lang;
                    return GestureDetector(
                      onTap: () {
                        setState(() {
                          _displayLang = lang;
                        });
                      },
                      child: Container(
                        margin: const EdgeInsets.only(left: 10),
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: isActive ? const Color(0xFF00FF41) : Colors.transparent,
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(color: const Color(0xFF00FF41), width: 1),
                        ),
                        child: Text(
                          lang,
                          style: TextStyle(
                            color: isActive ? Colors.black : const Color(0xFF00FF41),
                            fontFamily: 'monospace',
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                          ),
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ],
            ),
            const SizedBox(height: 36),

            // --- METRICS ROW ---
            Wrap(
              alignment: WrapAlignment.start,
              children: [
                _buildMetricCard('Active Containers', '$runningContainers / ${_dockerStats.length}', Icons.grid_view),
                _buildMetricCard('Total Documents', totalDbRows.toString(), Icons.description),
                _buildMetricCard('PostgreSQL Size', _dbStats?['size']?.toString() ?? 'Unknown', Icons.storage),
                _buildMetricCard('Ollama Status', _ollamaStats?['status']?.toString().toUpperCase() ?? 'OFFLINE', Icons.smart_toy),
              ],
            ),
            const SizedBox(height: 28),

            // --- NAVIGATION TABS ---
            Row(
              children: ['Overview', 'Analytics', 'Settings'].map((tab) {
                final isActive = _activeTab == tab;
                return GestureDetector(
                  onTap: () {
                    setState(() {
                      _activeTab = tab;
                    });
                  },
                  child: Container(
                    margin: const EdgeInsets.only(right: 16),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    decoration: BoxDecoration(
                      color: isActive ? const Color(0xFF00FF41).withOpacity(0.12) : Colors.transparent,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(
                        color: isActive ? const Color(0xFF00FF41) : const Color(0xFF008F11).withOpacity(0.4),
                        width: 1,
                      ),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (tab == 'Overview') ...[
                          Icon(Icons.computer, color: isActive ? const Color(0xFF00FF41) : const Color(0xFF008F11), size: 16),
                          const SizedBox(width: 8),
                        ],
                        if (tab == 'Analytics') ...[
                          Icon(Icons.bar_chart, color: isActive ? const Color(0xFF00FF41) : const Color(0xFF008F11), size: 16),
                          const SizedBox(width: 8),
                        ],
                        if (tab == 'Settings') ...[
                          Icon(Icons.settings, color: isActive ? const Color(0xFF00FF41) : const Color(0xFF008F11), size: 16),
                          const SizedBox(width: 8),
                        ],
                        Text(
                          tab,
                          style: TextStyle(
                            color: isActive ? const Color(0xFF00FF41) : const Color(0xFF008F11),
                            fontFamily: 'monospace',
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 28),

            // --- MAIN GRID CONTENTS ---
            if (_activeTab == 'Overview')
              Flex(
                direction: isDesktop ? Axis.horizontal : Axis.vertical,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // --- LEFT PANEL: DOCKER CONTAINERS ---
                  Expanded(
                    flex: isDesktop ? 2 : 0,
                    child: Container(
                      margin: EdgeInsets.only(right: isDesktop ? 24 : 0, bottom: isDesktop ? 0 : 24),
                      decoration: _matrixBoxDecoration(),
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Text(
                                'DOCKER CONTAINERS',
                                style: TextStyle(
                                  color: Color(0xFF00FF41),
                                  fontFamily: 'monospace',
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Row(
                                children: [
                                  // Refresh Button
                                  IconButton(
                                    icon: const Icon(Icons.refresh, color: Color(0xFF00FF41), size: 18),
                                    onPressed: _fetchSystemStats,
                                    tooltip: 'Refresh Stats',
                                  ),
                                  const SizedBox(width: 8),
                                  // DBeaver Button
                                  ElevatedButton.icon(
                                    onPressed: _launchDBeaver,
                                    icon: const Icon(Icons.open_in_new, size: 14, color: Colors.black),
                                    label: const Text(
                                      'DBEAVER',
                                      style: TextStyle(
                                        color: Colors.black,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 11,
                                        fontFamily: 'monospace',
                                      ),
                                    ),
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: const Color(0xFF00FF41),
                                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                          const SizedBox(height: 20),
                          SingleChildScrollView(
                            scrollDirection: Axis.horizontal,
                            child: Theme(
                              data: Theme.of(context).copyWith(
                                dividerColor: const Color(0xFF008F11).withOpacity(0.3),
                              ),
                              child: DataTable(
                                columns: const [
                                  DataColumn(label: Text('Container Name', style: TextStyle(color: Color(0xFF008F11), fontFamily: 'monospace', fontWeight: FontWeight.bold))),
                                  DataColumn(label: Text('Status', style: TextStyle(color: Color(0xFF008F11), fontFamily: 'monospace', fontWeight: FontWeight.bold))),
                                  DataColumn(label: Text('CPU %', style: TextStyle(color: Color(0xFF008F11), fontFamily: 'monospace', fontWeight: FontWeight.bold))),
                                  DataColumn(label: Text('Memory', style: TextStyle(color: Color(0xFF008F11), fontFamily: 'monospace', fontWeight: FontWeight.bold))),
                                  DataColumn(label: Text('Actions', style: TextStyle(color: Color(0xFF008F11), fontFamily: 'monospace', fontWeight: FontWeight.bold))),
                                ],
                                rows: _dockerStats.map((c) {
                                  final isRunning = c['status'] == 'running';
                                  return DataRow(
                                    cells: [
                                      DataCell(Text(c['name'], style: const TextStyle(color: Color(0xFF00FF41), fontFamily: 'monospace', fontSize: 13))),
                                      DataCell(
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                          decoration: BoxDecoration(
                                            color: isRunning ? const Color(0x1A00FF41) : const Color(0x1AEE2222),
                                            borderRadius: BorderRadius.circular(4),
                                            border: Border.all(
                                              color: isRunning ? const Color(0xFF00FF41) : Colors.redAccent,
                                              width: 1,
                                            ),
                                          ),
                                          child: Text(
                                            c['status'].toString().toUpperCase(),
                                            style: TextStyle(
                                              color: isRunning ? const Color(0xFF00FF41) : Colors.redAccent,
                                              fontSize: 10,
                                              fontWeight: FontWeight.bold,
                                              fontFamily: 'monospace',
                                            ),
                                          ),
                                        ),
                                      ),
                                      DataCell(Text('${c['cpu_percent']}%', style: const TextStyle(color: Color(0xFF00FF41), fontFamily: 'monospace', fontSize: 13))),
                                      DataCell(Text('${c['mem_mb']} MB', style: const TextStyle(color: Color(0xFF00FF41), fontFamily: 'monospace', fontSize: 13))),
                                      DataCell(
                                        Row(
                                          children: [
                                            IconButton(
                                              icon: const Icon(Icons.terminal, color: Color(0xFF00FF41), size: 16),
                                              tooltip: 'SSH',
                                              onPressed: () => _launchSSH(c['name']),
                                            ),
                                            IconButton(
                                              icon: const Icon(Icons.list_alt, color: Color(0xFF008F11), size: 16),
                                              tooltip: 'Logs',
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
                        ],
                      ),
                    ),
                  ),

                  // --- RIGHT PANEL: HOST & LOGS ---
                  Expanded(
                    flex: isDesktop ? 1 : 0,
                    child: Column(
                      children: [
                        // Host Stats Panel
                        Container(
                          decoration: _matrixBoxDecoration(),
                          padding: const EdgeInsets.all(24),
                          margin: const EdgeInsets.only(bottom: 24),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'HOST TELEMETRY',
                                style: TextStyle(
                                  color: Color(0xFF00FF41),
                                  fontFamily: 'monospace',
                                  fontSize: 15,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const SizedBox(height: 20),
                              _buildHostProgress(
                                'CPU Usage',
                                _hostStats?['cpu_percent']?.toDouble() ?? 0.0,
                                '${_hostStats?['cpu_percent'] ?? "0"}%',
                              ),
                              const SizedBox(height: 18),
                              _buildHostProgress(
                                'RAM Allocation',
                                _hostStats?['mem_percent']?.toDouble() ?? 0.0,
                                '${_hostStats?['mem_used_mb'] ?? "0"} / ${_hostStats?['mem_total_mb'] ?? "0"} MB',
                              ),
                              const SizedBox(height: 18),
                              _buildHostProgress(
                                'Disk Capacity',
                                _hostStats?['disk_percent']?.toDouble() ?? 0.0,
                                '${_hostStats?['disk_used_gb'] ?? "0"} / ${_hostStats?['disk_total_gb'] ?? "0"} GB',
                              ),
                            ],
                          ),
                        ),

                        // Ollama Status Panel
                        Container(
                          decoration: _matrixBoxDecoration(),
                          padding: const EdgeInsets.all(24),
                          margin: const EdgeInsets.only(bottom: 24),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  const Text(
                                    'OLLAMA NODE',
                                    style: TextStyle(
                                      color: Color(0xFF00FF41),
                                      fontFamily: 'monospace',
                                      fontSize: 15,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  ElevatedButton.icon(
                                    onPressed: () => launchUrl(Uri.parse('whereami-ollamalog://')),
                                    icon: const Icon(Icons.description, size: 14, color: Colors.black),
                                    label: const Text(
                                      'LOGS',
                                      style: TextStyle(
                                        color: Colors.black,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 11,
                                        fontFamily: 'monospace',
                                      ),
                                    ),
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: const Color(0xFF00FF41),
                                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 16),
                              Row(
                                children: [
                                  const Icon(Icons.smart_toy, color: Color(0xFF00FF41), size: 24),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          'Host: ${_ollamaStats?['host'] ?? "Unknown"}',
                                          style: const TextStyle(color: Color(0xFF33FF33), fontFamily: 'monospace', fontSize: 13),
                                        ),
                                        const SizedBox(height: 4),
                                        if (_ollamaStats?['models'] != null && (_ollamaStats!['models'] as List).isNotEmpty)
                                          Text(
                                            'Models: ${(_ollamaStats!['models'] as List).map((m) => m['name']).join(', ')}',
                                            style: const TextStyle(color: Color(0xFF008F11), fontFamily: 'monospace', fontSize: 11),
                                          )
                                        else
                                          const Text(
                                            'No active models.',
                                            style: TextStyle(color: Colors.orangeAccent, fontFamily: 'monospace', fontSize: 11),
                                          ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),

                        // System Activity Panel (Figma style)
                        Container(
                          decoration: _matrixBoxDecoration(),
                          padding: const EdgeInsets.all(24),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  const Text(
                                    'SYSTEM ACTIVITY',
                                    style: TextStyle(
                                      color: Color(0xFF00FF41),
                                      fontFamily: 'monospace',
                                      fontSize: 15,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  ElevatedButton.icon(
                                    onPressed: _showGlobalDiscourseLogDialog,
                                    icon: const Icon(Icons.analytics, size: 14, color: Colors.black),
                                    label: const Text(
                                      'GLOBAL DISCOURSE LOG',
                                      style: TextStyle(
                                        color: Colors.black,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 11,
                                        fontFamily: 'monospace',
                                      ),
                                    ),
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: const Color(0xFF00FF41),
                                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 20),
                              if (activityLogs.isEmpty)
                                const Text(
                                  'No recent log entries detected.',
                                  style: TextStyle(color: Color(0xFF008F11), fontFamily: 'monospace', fontSize: 13),
                                )
                              else
                                ...activityLogs.map((log) {
                                  final String message = log['message'];
                                  // Clean up logs to look like short system events
                                  String cleanMsg = message;
                                  if (cleanMsg.length > 50) {
                                    cleanMsg = '${cleanMsg.substring(0, 47)}...';
                                  }
                                  
                                  return Padding(
                                    padding: const EdgeInsets.only(bottom: 14.0),
                                    child: Row(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Icon(
                                          _getLogIcon(message),
                                          color: _getLogIconColor(message),
                                          size: 16,
                                        ),
                                        const SizedBox(width: 12),
                                        Expanded(
                                          child: Column(
                                            crossAxisAlignment: CrossAxisAlignment.start,
                                            children: [
                                              Text(
                                                cleanMsg,
                                                style: const TextStyle(
                                                  color: Color(0xFF33FF33),
                                                  fontFamily: 'monospace',
                                                  fontSize: 12,
                                                ),
                                              ),
                                              const SizedBox(height: 2),
                                              Text(
                                                'Source: ${log['container']}',
                                                style: const TextStyle(
                                                  color: Color(0xFF008F11),
                                                  fontFamily: 'monospace',
                                                  fontSize: 10,
                                                ),
                                              ),
                                            ],
                                          ),
                                        ),
                                      ],
                                    ),
                                  );
                                }).toList(),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            
            if (_activeTab == 'Analytics')
              Container(
                decoration: _matrixBoxDecoration(),
                padding: const EdgeInsets.all(32),
                width: double.infinity,
                child: const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('SYSTEM ANALYTICS', style: TextStyle(color: Color(0xFF00FF41), fontFamily: 'monospace', fontSize: 16, fontWeight: FontWeight.bold)),
                    SizedBox(height: 20),
                    Text('Telemetry analysis and historical load graphs are initializing...', style: TextStyle(color: Color(0xFF008F11), fontFamily: 'monospace')),
                  ],
                ),
              ),

            if (_activeTab == 'Settings')
              Container(
                decoration: _matrixBoxDecoration(),
                padding: const EdgeInsets.all(32),
                width: double.infinity,
                child: const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('SYSTEM SETTINGS', style: TextStyle(color: Color(0xFF00FF41), fontFamily: 'monospace', fontSize: 16, fontWeight: FontWeight.bold)),
                    SizedBox(height: 20),
                    Text('Configuration parameters, port bindings, and LLM endpoints are locked by root.', style: TextStyle(color: Color(0xFF008F11), fontFamily: 'monospace')),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
