import 'dart:math' show min;
import 'package:flutter/material.dart';
import '../models/photo.dart';
import '../models/face.dart';
import '../services/api_service.dart';

class PhotoViewScreen extends StatefulWidget {
  final Photo photo;

  const PhotoViewScreen({super.key, required this.photo});

  @override
  State<PhotoViewScreen> createState() => _PhotoViewScreenState();
}

class _PhotoViewScreenState extends State<PhotoViewScreen> {
  late Future<List<Face>> _faces;
  int? _naturalWidth;
  int? _naturalHeight;

  @override
  void initState() {
    super.initState();
    _faces = ApiService.fetchFaces(widget.photo.id);
    _loadNaturalDimensions();
  }

  void _loadNaturalDimensions() {
    final stream = NetworkImage(widget.photo.image)
        .resolve(ImageConfiguration.empty);
    stream.addListener(ImageStreamListener((info, _) {
      if (mounted) {
        setState(() {
          _naturalWidth = info.image.width;
          _naturalHeight = info.image.height;
        });
      }
    }));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Photo")),
      body: FutureBuilder<List<Face>>(
        future: _faces,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          }
          if (!snapshot.hasData || _naturalWidth == null || _naturalHeight == null) {
            return const Center(child: CircularProgressIndicator());
          }

          final facesList = snapshot.data!;

          return LayoutBuilder(builder: (context, constraints) {
            final containerWidth = constraints.maxWidth;
            final containerHeight = constraints.maxHeight;

            // Scale down to fit the screen, but never enlarge beyond natural size
            final scaleX = containerWidth / _naturalWidth!;
            final scaleY = containerHeight.isFinite
                ? containerHeight / _naturalHeight!
                : double.infinity;
            final scale = min(min(scaleX, scaleY), 1.0);

            final renderedWidth = _naturalWidth! * scale;
            final renderedHeight = _naturalHeight! * scale;

            // Center the image+overlay in the available space
            final offsetX = (containerWidth - renderedWidth) / 2;
            final offsetY = containerHeight.isFinite
                ? (containerHeight - renderedHeight) / 2
                : 0.0;

            return Stack(
              children: [
                Positioned(
                  left: offsetX,
                  top: offsetY,
                  child: SizedBox(
                    width: renderedWidth,
                    height: renderedHeight,
                    child: Stack(
                      children: [
                        Image.network(
                          widget.photo.image,
                          width: renderedWidth,
                          height: renderedHeight,
                          fit: BoxFit.fill,
                        ),
                        ...facesList.map((face) {
                          return Positioned(
                            left: face.x * scale,
                            top: face.y * scale,
                            child: Container(
                              width: face.width * scale,
                              height: face.height * scale,
                              decoration: BoxDecoration(
                                border: Border.all(color: Colors.red, width: 2),
                              ),
                            ),
                          );
                        }),
                      ],
                    ),
                  ),
                ),
              ],
            );
          });
        },
      ),
    );
  }
}
