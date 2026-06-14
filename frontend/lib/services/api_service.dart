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
}
