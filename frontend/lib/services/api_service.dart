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

  static Future<Map<String, dynamic>> getDocumentTree() async {
    final response = await http.get(Uri.parse('$baseUrl/documents/tree'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load document tree');
  }

  static Future<void> uploadDocument(PlatformFile file, String? entityId) async {
    var request = http.MultipartRequest('POST', Uri.parse('$baseUrl/documents/upload'));
    
    // Add file
    if (file.bytes != null) {
      request.files.add(http.MultipartFile.fromBytes(
        'file', 
        file.bytes!, 
        filename: file.name
      ));
    }
    
    if (entityId != null) {
      request.fields['entity_id'] = entityId;
    }

    var streamedResponse = await request.send();
    if (streamedResponse.statusCode != 200) {
      throw Exception('Failed to upload document');
    }
  }
}
