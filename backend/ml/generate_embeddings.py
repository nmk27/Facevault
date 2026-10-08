from functools import lru_cache

from facenet_pytorch import InceptionResnetV1
from PIL import Image
import torch
import numpy as np

from ml.defaults import STANDARDIZE_EMBEDDINGS


@lru_cache(maxsize=1)
def _model():
    # Pretrained FaceNet, loaded on first use so importing this module (e.g. in tests)
    # does not trigger a weights download.
    return InceptionResnetV1(pretrained='vggface2').eval()

def generate_embedding(image, standardize=STANDARDIZE_EMBEDDINGS):
    """512-d FaceNet embedding of a face crop.

    standardize=True applies facenet-pytorch's own input contract, (x - 127.5) / 128;
    False scales pixels to [0, 1] (the original behaviour). The default comes from
    ml.defaults; evaluation/ passes the flag explicitly to compare the two.
    """
    image = image.convert("RGB")
    image = image.resize((160, 160))


    img_tensor = torch.tensor(np.array(image)).permute(2,0,1).float()
    img_tensor = img_tensor.unsqueeze(0)
    img_tensor = (img_tensor - 127.5) / 128.0 if standardize else img_tensor / 255.0

    with torch.no_grad():
        embedding = _model()(img_tensor)

    return embedding.squeeze().tolist()
