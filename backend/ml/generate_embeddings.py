from facenet_pytorch import InceptionResnetV1
from PIL import Image
import torch
import numpy as np

# Load pretrained FaceNet model
model = InceptionResnetV1(pretrained='vggface2').eval()

def generate_embedding(image):
    image = image.convert("RGB")
    image = image.resize((160, 160))


    img_tensor = torch.tensor(np.array(image)).permute(2,0,1).float()
    img_tensor = img_tensor.unsqueeze(0) / 255.0

    with torch.no_grad():
        embedding = model(img_tensor)

    return embedding.squeeze().tolist()