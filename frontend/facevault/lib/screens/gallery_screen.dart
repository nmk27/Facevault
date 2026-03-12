import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/photo.dart';
import 'package:file_picker/file_picker.dart';
import 'photo_view_screen.dart';

class GalleryScreen extends StatefulWidget {
  const GalleryScreen({super.key});

  @override
  State<GalleryScreen> createState() => _GalleryScreenState();
}

class _GalleryScreenState extends State<GalleryScreen> {
  final List<Photo> _photos = [];
  final ScrollController _scrollController = ScrollController();
  int _currentPage = 1;
  bool _isLoading = false;
  bool _hasMore = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadPhotos();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
            _scrollController.position.maxScrollExtent - 300 &&
        !_isLoading &&
        _hasMore) {
      _loadPhotos();
    }
  }

  Future<void> _loadPhotos({bool reset = false}) async {
    if (_isLoading) return;
    setState(() {
      _isLoading = true;
      _error = null;
      if (reset) {
        _currentPage = 1;
        _photos.clear();
        _hasMore = true;
      }
    });
    try {
      final page = await ApiService.fetchPhotos(page: _currentPage);
      setState(() {
        _photos.addAll(page.photos);
        _hasMore = page.hasNext;
        if (_hasMore) _currentPage++;
        _isLoading = false;
      });
    } catch (e) {
      // ignore: avoid_print
      print('fetchPhotos error: $e');
      setState(() {
        _error = 'Error loading photos: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> pickAndUploadImage() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      withData: true,
    );

    if (result != null) {
      final file = result.files.single;
      await ApiService.uploadPhoto(file.bytes!, file.name);
      _loadPhotos(reset: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("FaceVault")),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton(
        onPressed: pickAndUploadImage,
        child: const Icon(Icons.upload),
      ),
    );
  }

  Widget _buildBody() {
    if (_photos.isEmpty && _isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_photos.isEmpty && _error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_error!),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: () => _loadPhotos(reset: true),
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }
    if (_photos.isEmpty) {
      return const Center(child: Text('No photos yet'));
    }

    return GridView.builder(
      controller: _scrollController,
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
      ),
      // Extra slot at the end for the loading indicator
      itemCount: _photos.length + (_hasMore ? 1 : 0),
      itemBuilder: (context, index) {
        if (index == _photos.length) {
          // Spinner is visible — load next page even if there's no scroll
          WidgetsBinding.instance.addPostFrameCallback((_) => _loadPhotos());
          return const Center(child: CircularProgressIndicator());
        }
        final photo = _photos[index];
        return GestureDetector(
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => PhotoViewScreen(photo: photo)),
            );
          },
          child: Image.network(
            photo.thumbnail,
            fit: BoxFit.cover,
            errorBuilder: (context, error, stackTrace) {
              return const Center(child: Icon(Icons.broken_image));
            },
          ),
        );
      },
    );
  }
}
