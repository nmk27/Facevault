"""Load a labelled face dataset laid out as one folder per person (LFW's layout)."""
import os

import numpy as np

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def load_folder_dataset(root, min_images=2, max_per_identity=None, max_identities=None, seed=0):
    """Return [(image_path, identity)] sorted by identity then file name.

    root/<identity>/<image files>. Identities with fewer than `min_images` images are
    dropped (they cannot form a same-person pair). `max_per_identity` and
    `max_identities` subsample with a seeded RNG: LFW has people with hundreds of
    images (one has 530) who would otherwise dominate every pairwise score.
    """
    people = {}
    for name in sorted(os.listdir(root)):
        folder = os.path.join(root, name)
        if name.startswith(".") or not os.path.isdir(folder):
            continue
        files = sorted(
            os.path.join(folder, f) for f in os.listdir(folder)
            if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
        )
        if len(files) >= min_images:
            people[name] = files
    if not people:
        raise SystemExit(f"No identity folders with >= {min_images} images found in {root}")

    rng = np.random.default_rng(seed)
    names = sorted(people)
    if max_identities and len(names) > max_identities:
        names = sorted(rng.choice(names, size=max_identities, replace=False).tolist())

    samples = []
    for name in names:
        files = people[name]
        if max_per_identity and len(files) > max_per_identity:
            files = sorted(rng.choice(files, size=max_per_identity, replace=False).tolist())
        samples.extend((path, name) for path in files)
    return samples


def download_lfw(root):
    """Download the original (unaligned) LFW with torchvision and return its image folder.

    Original images are the honest input for a photo app: no face alignment helps
    the detector. torchvision checks the archive's MD5. Needs network access to
    vis-www.cs.umass.edu; if that fails, download LFW by hand and pass --lfw-dir.
    """
    from torchvision.datasets import LFWPeople

    dataset = LFWPeople(root=root, split="10fold", image_set="original", download=True)
    return dataset.images_dir
