"""Pipeline settings that the app and the evaluation must agree on (no heavy imports)."""

# Input scaling for FaceNet. True applies facenet-pytorch's own contract, (pixels - 127.5) / 128;
# False is the original pixels / 255. On LFW the first gave a better embedding (AUC 0.9987 vs
# 0.9979) and a better clustering curve; see evaluation/README.md. Changing this makes every
# stored embedding stale: run `python manage.py reembed_faces` afterwards.
STANDARDIZE_EMBEDDINGS = True
