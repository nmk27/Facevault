from PIL import Image
from facenet_pytorch import MTCNN
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


detector = MTCNN()

def detect_faces(image_path):
    image = Image.open(image_path).convert("RGB")

    boxes, probs = detector.detect(image)
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