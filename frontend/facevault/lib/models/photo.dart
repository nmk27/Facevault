class Photo {
  final int id;
  final String image;
  final String thumbnail;
  final String uploadedAt;
  final int width;
  final int height;

  Photo({
    required this.id,
    required this.image,
    required this.thumbnail,
    required this.uploadedAt,
    required this.width,
    required this.height,
  });

  factory Photo.fromJson(Map<String, dynamic> json) {
    return Photo(
      id: json['id'],
      image: json['image'],
      thumbnail: json['thumbnail'],
      uploadedAt: json['uploaded_at'],
      width: json['width'] ?? 0,
      height: json['height'] ?? 0,
    );
  }
}
