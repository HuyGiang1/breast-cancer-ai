# Dataset Setup

Audit date: 2026-09-04

Large datasets are intentionally excluded from Git. This repository should contain code, documentation, small reference tables, and reproducible metadata only.

## Wisconsin Diagnostic Breast Cancer

The tabular baseline uses the Wisconsin Diagnostic Breast Cancer dataset from scikit-learn:

```python
from sklearn.datasets import load_breast_cancer
```

Local CSV copies may exist under:

```text
data/raw/wisconsin_breast_cancer.csv
src/data/raw/wisconsin_breast_cancer.csv
```

These small CSVs are acceptable to keep if licensing/source attribution is documented. Binary processed copies such as `.pkl` are ignored.

## CBIS-DDSM

CBIS-DDSM is not committed because of size and dataset distribution/licensing constraints. Keep it local or provision it separately on the training machine.

Expected local structure:

```text
data/cbis_ddsm/
  raw/
  processed/
    images/
      train/
        benign/
        malignant/
      val/
        benign/
        malignant/
      test/
        benign/
        malignant/
    images_roi/
      train/
      val/
      test/
```

Current local processed snapshot:

```text
data/cbis_ddsm files: 5120
processed/images total images audited: 2559
train/benign: 1040
train/malignant: 750
val/benign: 223
val/malignant: 160
test/benign: 224
test/malignant: 162
```

## Preprocessing

The current repository has processed PNG images, but the preprocessing lineage is not yet fully documented. Before final research claims, add:

- raw dataset source and access date
- preprocessing script entrypoint
- image resizing/cropping policy
- ROI/full-image distinction
- label mapping rules
- excluded/corrupt image handling
- deterministic split manifest

## Split Requirement

Current audit reports a critical leakage risk:

```text
cross-split duplicate study-prefix count: 90
leakage risk: CRITICAL
```

Do not train or report final DL/multimodal metrics on the current split. Build a deterministic group split using the strongest available independent identifier, preferably patient/case/study ID. The final split must satisfy:

```text
patient overlap train/val = 0
patient overlap train/test = 0
patient overlap val/test = 0
study overlap train/val = 0
study overlap train/test = 0
study overlap val/test = 0
```

If true patient IDs are not available in the processed filenames, document the fallback identifier and its limitation.

## Current Clean Manifest

The local `data/cbis_ddsm/raw/` snapshot does not currently expose patient/case metadata files. The first leakage-control implementation therefore uses the strongest available fallback:

```text
group_id = filename prefix before "__"
```

Generate the manifest:

```bash
python scripts/generate_cbis_group_split.py
```

Audit the generated manifest:

```bash
python scripts/audit_cbis_splits.py --manifest data/cbis_ddsm/processed/splits/cbis_group_split_seed42.csv --json
```

Current local manifest summary:

```text
seed: 42
rows: 5118
groups: 2354
train/val group overlap: 0
train/test group overlap: 0
val/test group overlap: 0
mixed-label groups: 0
original cross-split group count: 90
```

This manifest improves leakage control over the current folder split, but final reporting must state that true patient-level independence could not be verified from the PNG-only local snapshot.

## Version Control Policy

Do not commit:

- `data/cbis_ddsm/`
- raw mammography datasets
- processed binary arrays
- model weights
- local SQLite databases
- generated caches

Commit:

- dataset setup docs
- split generator scripts
- split metadata CSV/JSON manifests if they contain no restricted data
- small final metric JSON/CSV tables
- selected final figures needed by README/docs
