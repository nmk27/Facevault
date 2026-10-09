# Evaluating FaceVault's face pipeline

This folder measures how well FaceVault's pipeline (MTCNN detection, FaceNet embeddings, centroid
matching + DBSCAN clustering) recovers who is who, on a labelled dataset such as
[LFW](https://vis-www.cs.umass.edu/lfw/). It runs the **same functions the app runs**
(`ml/detect_faces.py`, `ml/generate_embeddings.py`, `ml/clustering.py`), so the numbers describe the app,
not a re-implementation. A test (`ml/tests.py`) checks that the incremental replay and the real
database-backed `cluster_faces()` produce the same people.

It answers three questions:

1. **Verification:** do embedding distances separate same-person from different-person pairs?
   (AUC, EER, and what `eps` accepts or wrongly accepts.)
2. **Batch clustering:** if every photo were uploaded at once, how good is DBSCAN, and which
   `eps` / `min_samples` should the app use?
3. **Incremental clustering:** the app clusters after every upload and never revisits a decision.
   How much does that cost compared with batch clustering, and does upload order matter?

## Run it

```bash
cd backend
pip install -r requirements-eval.txt        # main requirements + matplotlib for the plots
python -m evaluation.evaluate_lfw --download-to ~/datasets
```

`--download-to` fetches the original (unaligned) LFW with torchvision, which checks the archive's MD5
(needs access to vis-www.cs.umass.edu). If you already have LFW, or the download is blocked, extract
`lfw.tgz` yourself and pass the folder that contains one sub-folder per person:

```bash
python -m evaluation.evaluate_lfw --lfw-dir /path/to/lfw
```

Any dataset laid out as `root/<person>/<image>.jpg` works. Useful options:

| Option | Default | Meaning |
|---|---|---|
| `--max-identities N` | all | random subset of people; use `--max-identities 100 --orders 2` for a quick trial |
| `--max-per-identity N` | 20 | cap images per person (see caveats) |
| `--min-images N` | 2 | drop people with fewer images (no same-person pair possible) |
| `--tune-fraction F` | 0.5 | share of *people* used to pick `eps`; results are reported on the rest. `0` disables the split |
| `--eps START:STOP:STEP` | 0.20:0.70:0.05 | `eps` values to sweep |
| `--min-samples A,B,C` | 2,3,5 | `min_samples` values to sweep |
| `--orders N` | 5 | random upload orders to replay |
| `--batch-size N` | 1 | photos per simulated upload (the web UI uploads one at a time) |
| `--ablate-preprocessing` | off | also evaluate the other FaceNet input scaling (the one the app does not use: `pixels / 255` or `(pixels - 127.5) / 128`) |
| `--seed N` | 0 | seeds the subsampling, the tune/test split and the upload orders |
| `--no-cache`, `--skip-incremental`, `--no-plots` | | skip the feature cache / the replay / the figures |

Do not `pip install matplotlib` into the project environment on its own: the newest release pulls in
numpy 2, which breaks the pinned `torch==2.2.2`. `requirements-eval.txt` pins a compatible version.

### How long does it take?

Measured on 4 CPU cores (no GPU):

* **Detection + embedding: about 0.2 s per 250x250 image**, roughly 3 minutes per 1,000 images. This is
  the slow part, and its results are cached in `evaluation/cache/` (git-ignored). The cache is written every
  250 images, so an interrupted run resumes where it stopped, and re-running with different clustering
  options does not repeat it.
* **Evaluation stage on ~7,000 faces (1,680 people): about 3 minutes with 3 replay orders** and about 500 MB of
  memory (measured on synthetic embeddings of that size; the default 5 orders should take roughly 5 minutes).

## Protocol

* **Which face:** LFW photos are centred on the labelled person, so the detected face closest to the image
  centre is used (one face per image). The app itself stores every face it finds.
* **Detection gate:** only detections with confidence >= `MIN_FACE_CONFIDENCE` (0.95, the app's gate) count.
  Images with no such face are dropped and reported as the detection miss rate.
* **Embedding and crop:** the app's `generate_embedding` on the app's `crop_face` (tight box, no margin).
* **No tuning on the test set:** people are split into a *tune* and a *test* set (identity-disjoint).
  `eps` / `min_samples` are chosen on the tune people and every clustering number is reported on the test
  people. Two choices are reported next to the app's current config: *tuned* (best ARI) and
  *conservative* (highest recall that keeps pairwise precision >= 0.99). Verification scores use all faces,
  since nothing is fitted on them.
* **Incremental replay:** faces arrive in a random order, `--batch-size` at a time. After each batch the app's
  logic runs over every face that has no person yet (earlier leftovers plus new faces): attach to the nearest
  existing person if close enough, otherwise DBSCAN the rest into new people. People never change afterwards.
  The result is averaged over `--orders` random orders; the standard deviation shows order sensitivity.

## Metrics

| Metric | Meaning |
|---|---|
| **ARI** | Adjusted Rand index of the clustering against the true identities. 1 is perfect, 0 is chance. Unassigned faces count as one-face clusters. |
| **pair P / pair R / pair F1** | Over all pairs of faces: *precision* is the share of same-person-claimed pairs that really are the same person; *recall* is the share of real same-person pairs that were put together. |
| **in a person** | Share of faces that ended up in some person. The rest are left unassigned (the app shows people only). |
| **wrong person** | Of the faces filed under a person, the share that are not that person's most common true identity (a stranger in someone's folder). This is the error users notice most. Unassigned faces are not counted here but cost recall. |
| **people vs identities** | Number of people the app created against the number of real people. |
| **AUC / EER / TPR@FPR** | Threshold-free verification quality of the embeddings. |
| **same / different pairs accepted at eps** | What the rule "cosine distance <= eps" does, per `eps`. This is the table to read when choosing `eps`. |

## Results in this repository

* `results_eps_fine/`: the run the project README cites (`eps` swept 0.10 to 0.40, `min_samples` 2 and 3).
* `results/`: an earlier, coarser run (`eps` 0.20 to 0.70) kept for reference.

Both were produced before the defaults changed, with the app then using input scaling `pixels / 255` and `eps` 0.4. In their reports the variant called "app" is that old setting and "standardized" is what the app uses now. Newer runs label the two variants by the scaling itself ("app" is whatever the app currently uses, "ablation" is the other). The folder path of the dataset was replaced by `<LFW folder, original images>`.

## Outputs (in `evaluation/results/`)

* `report.md`: protocol, tables and figures, ready to read or paste into the project README.
* `results.json`: every number, plus the protocol text.
* `sweep_batch.csv`: the full `eps x min_samples` sweep on both splits.
* `incremental_runs.csv`: one row per replayed order.
* `roc.png`, `sweep_eps.png`, `incremental_curve.png`.

## Caveats to state when you quote the numbers

* LFW is mostly frontal, well-lit celebrity photos. Expect high scores that overstate performance on family
  photo libraries (side views, children, glasses, low light, bystanders). On an easy test set several variants
  can look identical; that says the data is easy, not that the variants are equal.
* A few people have hundreds of images (one has 530), so pairwise scores are dominated by them unless you cap
  images per person; hence `--max-per-identity`.
* The test split is half of the people. Change `--seed` and re-run to see how much the numbers move.
* Everything is one run of one model on one dataset. Report the settings (`report.md` records them).

## Tests

```bash
cd backend
DB_ENGINE=django.db.backends.sqlite3 python manage.py test evaluation ml
```

The tests use synthetic embeddings; they do not need LFW or the models. They cross-check the metrics against
brute force and scikit-learn, and check that the replay matches the real `cluster_faces()`.
