from facenet_pytorch import MTCNN
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from PIL import Image
import numpy as np

detector = MTCNN()

def detect_faces(image_path):
    image = Image.open(image_path).convert("RGB")
    image_array = np.array(image)

    faces = detector.detect_faces(image_array)
    
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