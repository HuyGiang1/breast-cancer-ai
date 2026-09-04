# Data Card

## Datasets

### Wisconsin Diagnostic Breast Cancer (WDBC)

- Type: structured numeric clinical/cytology features.
- Samples: 569.
- Features: 30.
- Labels: benign/malignant.
- Source in code: `sklearn.datasets.load_breast_cancer()` and local CSV copies.
- Primary use: classical ML baseline and explainable structured prediction.

### CBIS-DDSM Processed Images

- Type: breast imaging files processed into image folders.
- Local path: `data/cbis_ddsm/processed/images`.
- Current local image count: 2559.
- Current class/split counts:

| Split | Benign | Malignant | Total |
| --- | ---: | ---: | ---: |
| Train | 1040 | 750 | 1790 |
| Validation | 223 | 160 | 383 |
| Test | 224 | 162 | 386 |

## Current Split Audit

Command:

```bash
python scripts/audit_cbis_splits.py --json
```

Current finding:

- Unique study-like filename prefixes: 2354.
- Prefixes appearing across more than one split: 90.
- Leakage risk: CRITICAL.

The prefix before `__` is used as a conservative study-level identifier. This does not prove exact patient identity, but it is enough to block final DL claims until a proper patient/study manifest is built.

## Required Split Methodology

Final experiments must:

- Split by patient ID when available.
- Otherwise split by study ID or conservative filename prefix.
- Keep train/validation/test mutually exclusive by patient/study.
- Apply augmentation only after splitting and only to training data.
- Record random seed and preprocessing version.
- Save a manifest, e.g. `data/manifests/cbis_split_manifest.csv`.

## Preprocessing

Current project references:

- ROI preprocessing: `src/data_processing/roi_preprocessing.py`.
- DL training uses `tf.keras.utils.image_dataset_from_directory`.
- Existing summaries mention ROI crop + thresholding + margin.

Required documentation for final report:

- original image source
- resizing
- color mode
- normalization/preprocessing function
- augmentation
- class imbalance handling
- excluded/corrupt image policy

## Missing Values and Duplicates

- WDBC: final scripts should explicitly check missing values even if sklearn dataset is clean.
- CBIS-DDSM: duplicate/study-prefix leakage must be checked before training.
- Exact duplicate image hash audit is recommended after study-level split is repaired.

## Privacy

Do not commit or publish real patient records. Demo records should be synthetic. Runtime SQLite DB and uploaded result images are local/server data and must stay out of Git.

## Licensing and Citation

Before public release, add exact dataset citations and license notes for:

- WDBC / UCI / sklearn breast cancer dataset.
- CBIS-DDSM source and download terms.

If redistribution of CBIS-DDSM images is not allowed or unclear, do not put images in the public repository.
