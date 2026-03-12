import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/photo.dart';
import '../models/face.dart';

class PhotoPage {
  final List<Photo> photos;
  final bool hasNext;

  PhotoPage({required this.photos, required this.hasNext});
}

class ApiService {
  static const String _baseUrl = "http://127.0.0.1:8000";

  static Future<PhotoPage> fetchPhotos({int page = 1}) async {
    final response = await http.get(Uri.parse("$_baseUrl/photos/?page=$page"));

    if (response.statusCode == 200) {
      final body = jsonDecode(response.body);
      final List<dynamic> results = body['results'];
      return PhotoPage(
        photos: results.map((photo) => Photo.fromJson(photo)).toList(),
        hasNext: body['next'] != null,
      );
    } else {
      throw Exception('Failed to load photos');
    }
  }

  static Future<void> uploadPhoto(List<int> bytes, String filename) async {
    var request = http.MultipartRequest(
      'POST',
      Uri.parse("$_baseUrl/photos/upload/"),
    );

    request.files.add(
      http.MultipartFile.fromBytes('image', bytes, filename: filename),
    );

    var response = await request.send();

    if (response.statusCode != 201) {
      throw Exception("Upload failed");
    }
  }

  static Future<List<Face>> fetchFaces(int photoId) async {
    final response = await http.get(Uri.parse("$_baseUrl/faces/$photoId/"));

    if (response.statusCode == 200) {
      List<dynamic> faces = jsonDecode(response.body);
      return faces.map((face) => Face.fromJson(face)).toList();
    } else {
      throw Exception('Failed to load faces');
    }
  }
}
