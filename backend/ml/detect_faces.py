from functools import lru_cache

from PIL import Image
from facenet_pytorch import MTCNN
import os

from ml.image_utils import open_oriented

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Detections below this confidence are ignored by the upload view and the evaluation.
MIN_FACE_CONFIDENCE = 0.95


@lru_cache(maxsize=1)
def _detector():
    # Loaded on first use so importing this module (e.g. in tests) stays cheap.
    return MTCNN()


def detect_faces(image):
    """Detect faces in a PIL image, or in an image path (opened with EXIF orientation applied).

    Boxes are in the pixel space of the image as displayed to the user.
    """
    if not isinstance(image, Image.Image):
        image = open_oriented(image)

    boxes, probs = _detector().detect(image.convert("RGB"))
    if boxes is None or probs is None:
        return []

    faces = []
    for box, confidence in zip(boxes, probs):
        x1, y1, x2, y2 = box
        faces.append({
            "box": [
                int(round(x1)),
                int(round(y1)),
                int(round(x2 - x1)),
                int(round(y2 - y1)),
            ],
            "confidence": float(confidence),
        })

    return faces


if __name__ == "__main__":
    faces = detect_faces("media/photos/test.jpeg")

    for face in faces:
        x, y, width, height = face["box"]
        confidence = face["confidence"]

        print(f"Face detected:")
        print(f"x={x}, y={y}, width={width}, height={height}")
        print(f"confidence={confidence}")
        print()
