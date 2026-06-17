import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';

class ApiService {
  // Use localhost for local dev; this might need to change for docker or prod
  static const String baseUrl = 'http://localhost:8000/api';

  static Future<List<dynamic>> getEntities() async {
    final response = await http.get(Uri.parse('$baseUrl/entities/'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load entities');
  }

  static Future<void> createEntity(Map<String, dynamic> data) async {
    final response = await http.post(
      Uri.parse('$baseUrl/entities/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(data),
    );
    if (response.statusCode != 200) throw Exception('Failed to create entity');
  }

  static Future<void> createEntityAuto(Map<String, dynamic> data) async {
    final response = await http.post(
      Uri.parse('$baseUrl/entities/auto_translate'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(data),
    );
    if (response.statusCode != 200) throw Exception('Failed to auto-translate and create entity');
  }

  static Future<void> updateEntity(String id, Map<String, dynamic> data) async {
    final response = await http.put(
      Uri.parse('$baseUrl/entities/$id'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(data),
    );
    if (response.statusCode != 200) throw Exception('Failed to update entity');
  }

  static Future<void> deleteEntity(String id) async {
    final response = await http.delete(Uri.parse('$baseUrl/entities/$id'));
    if (response.statusCode != 200) throw Exception('Failed to delete entity');
  }

  static Future<Map<String, dynamic>> updateAxis(String id, Map<String, dynamic> axisData) async {
    final response = await http.put(
      Uri.parse('$baseUrl/axes/$id'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(axisData),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to update axis');
  }

  static Future<void> deleteAxis(String id) async {
    final response = await http.delete(Uri.parse('$baseUrl/axes/$id'));
    if (response.statusCode != 200) throw Exception('Failed to delete axis');
  }

  static Future<Map<String, dynamic>> discoverDiscourse(String id) async {
    final response = await http.post(Uri.parse('$baseUrl/discovery/discourse/$id'));
    if (response.statusCode != 200) {
      throw Exception('Failed to discover discourse: ${response.body}');
    }
    return jsonDecode(response.body);
  }

  static Future<String> getDiscoveryLog(String id) async {
    final response = await http.get(Uri.parse('$baseUrl/entities/$id/discovery_log'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body)['log'];
    }
    throw Exception('Failed to fetch discovery log');
  }

  static Future<String> getGlobalDiscoveryLog() async {
    final response = await http.get(Uri.parse('$baseUrl/discovery/global_log'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body)['log'];
    }
    throw Exception('Failed to fetch global discovery log');
  }

  static Future<Map<String, dynamic>> discoverDiscourseGlobal() async {
    final response = await http.post(Uri.parse('$baseUrl/discovery/discourse/all'));
    if (response.statusCode != 200) {
      throw Exception('Failed to start global discourse scoring: ${response.body}');
    }
    return jsonDecode(response.body);
  }

  static Future<String> getGlobalDiscourseLog() async {
    final response = await http.get(Uri.parse('$baseUrl/discovery/global_discourse_log'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body)['log'];
    }
    throw Exception('Failed to fetch global discourse log');
  }

  static Future<Map<String, dynamic>> deduplicateEntities() async {
    final response = await http.post(Uri.parse('$baseUrl/maintenance/deduplicate/entities'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to deduplicate entities');
  }

  static Future<List<dynamic>> getEntityScores(String id) async {
    // We actually need a route for this! Wait, does the discovery response contain scores?
    // Yes, but we need a standalone route to get scores. Let me just use discovery response for now, OR add the route.
    // Actually, I didn't add a /api/entities/{id}/scores route yet. Let's add it in backend later, or just add the api_service method now.
    final response = await http.get(Uri.parse('$baseUrl/entities/$id/scores'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to get scores');
  }

  static Future<List<dynamic>> getAxes() async {
    final response = await http.get(Uri.parse('$baseUrl/axes/'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load axes');
  }

  static Future<void> createAxis(Map<String, dynamic> data) async {
    final response = await http.post(
      Uri.parse('$baseUrl/axes/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(data),
    );
    if (response.statusCode != 200) throw Exception('Failed to create axis');
  }

  static Future<void> autoTranslateAxis(String name) async {
    final response = await http.post(
      Uri.parse('$baseUrl/axes/auto_translate?name=${Uri.encodeComponent(name)}'),
    );
    if (response.statusCode != 200) throw Exception('Failed to auto-translate axis');
  }

  static Future<void> approveAxis(String id) async {
    final response = await http.put(Uri.parse('$baseUrl/axes/$id/approve'));
    if (response.statusCode != 200) throw Exception('Failed to approve axis');
  }

  static Future<List<dynamic>> getQuestions() async {
    final response = await http.get(Uri.parse('$baseUrl/questions/'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load questions');
  }

  static Future<void> createQuestion(Map<String, dynamic> data) async {
    final response = await http.post(
      Uri.parse('$baseUrl/questions/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(data),
    );
    if (response.statusCode != 200) throw Exception('Failed to create question');
  }

  static Future<Map<String, dynamic>> getDocumentTree(String entityId) async {
    final response = await http.get(Uri.parse('$baseUrl/documents/tree/$entityId'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load document tree');
  }

  static Future<void> uploadDocument(PlatformFile file, String entityId) async {
    var request = http.MultipartRequest('POST', Uri.parse('$baseUrl/documents/upload/$entityId'));
    
    if (file.bytes != null) {
      request.files.add(http.MultipartFile.fromBytes(
        'file', 
        file.bytes!, 
        filename: file.name
      ));
    }
    
    var streamedResponse = await request.send();
    if (streamedResponse.statusCode != 200) {
      throw Exception('Failed to upload document');
    }
  }

  static Future<void> triggerScraping(String entityId) async {
    final response = await http.post(Uri.parse('$baseUrl/documents/scrape/$entityId'));
    if (response.statusCode != 200) {
      throw Exception('Failed to trigger scraping');
    }
  }

  static Future<List<dynamic>> getEntityTypes() async {
    final response = await http.get(Uri.parse('$baseUrl/entity_types/'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load entity types');
  }

  static Future<void> createEntityType(Map<String, dynamic> data) async {
    final response = await http.post(
      Uri.parse('$baseUrl/entity_types/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(data),
    );
    if (response.statusCode != 200) throw Exception('Failed to create entity type');
  }

  static Future<Map<String, dynamic>> discoverNewAxes() async {
    final response = await http.post(Uri.parse('$baseUrl/discovery/axes'));
    if (response.statusCode == 200) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    }
    throw Exception('Failed to discover new axes');
  }
}
