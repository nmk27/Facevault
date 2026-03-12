class Face {
  final int x;
  final int y;
  final int width;
  final int height;

  Face({
    required this.x,
    required this.y,
    required this.width,
    required this.height,
  });

  factory Face.fromJson(Map<String, dynamic> json) {
    return Face(
      x: json['x'] ?? 0,
      y: json['y'] ?? 0,
      width: json['width'] ?? 0,
      height: json['height'] ?? 0,
    );
  }
}
