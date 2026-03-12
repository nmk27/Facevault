import 'package:flutter/material.dart';
import 'screens/gallery_screen.dart';

void main() {
  runApp(const FaceVaultApp());
}

class FaceVaultApp extends StatelessWidget {
  const FaceVaultApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(home: GalleryScreen());
  }
}
