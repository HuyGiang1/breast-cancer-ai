# Git History Cleanup

Audit date: 2026-09-04

Target remote: `https://github.com/HuyGiang1/breast-cancer-ai.git`

## Backup

Created before rewriting history:

```text
branch: backup/pre-history-cleanup
bundle: ../breast-cancer-ai-before-history-cleanup.bundle
bundle size: 2.8G
bundle verification: OK
```

Extra uncommitted-state backups:

```text
/tmp/breast-cancer-ai-working-tree.patch
/tmp/breast-cancer-ai-index.patch
/tmp/breast-cancer-ai-untracked-files.tgz
```

## Before Cleanup

```text
git count-objects -vH
count: 5590
size: 2.83 GiB
in-pack: 127
size-pack: 5.81 MiB
historical blob payload: 2961.48 MB
```

Historical large blob groups:

| Size | Count | Group | Should remain? |
| ----: | ----: | ----- | -------------- |
| 2796.27 MB | 5106 | `data/cbis_ddsm` | No |
| 131.52 MB | 3 | `.keras` runtime model artifacts | No |
| 21.46 MB | 232 | source/docs/other | Yes, after review |
| 10.63 MB | 62 | research result figures/tables | Partially, keep small final outputs |
| 0.94 MB | 4 | `.pkl` artifacts | No |
| 0.40 MB | 26 | `__pycache__` / `.pyc` | No |

Largest historical blobs before cleanup:

| Size | Git object | Original path | Should remain? |
| ----: | ---------- | ------------- | -------------- |
| 96.70 MB | `27f98476ee5cdd8a8a71f78878ef07866b838d05` | `backend/resnet50_best.keras` | No |
| 18.19 MB | `74e15adf775e2446bdf926f1e61dd86c30763d0c` | `backend/efficientnetb0_best.keras` | No |
| 16.62 MB | `b108bdf1afe92c54cb2059a46fed1a0fe996fd2a` | `backend/custom_cnn_best.keras` | No |
| 8.97 MB | `61038d33256f0a2aa4e9db8bc757da3186787e40` | `data/cbis_ddsm/processed/images/train/malignant/...__1-251.png` | No |
| 8.72 MB | `03e9a258abf52c9277cb14b548ffb215f4679521` | `data/cbis_ddsm/processed/images/val/malignant/...__1-012.png` | No |
| 7.80 MB | `4bcd0c02921685430b738cbb42a767964d33968d` | `data/cbis_ddsm/processed/images/train/benign/...__1-124.png` | No |

Blob count above 20 MB before cleanup: 1.

Blob count above GitHub's 100 MB hard limit before cleanup: 0, but the 96.70 MB ResNet50 artifact is too close to the limit for a healthy repository.

## Cleanup Method

Used `git-filter-repo` version `a40bce548d2c`.

Removed from all reachable history:

```text
data/cbis_ddsm/
backend/data/
*.keras
*.h5
*.pkl
*.npy
*.pt
*.pth
*.onnx
*.db
*.sqlite
*.sqlite3
*.zip
*.pyc
*/__pycache__/*
```

The old GitHub remote and Codex internal refs were removed locally after the backup bundle was verified because they retained pre-cleanup objects.

## After Cleanup

```text
git count-objects -vH
count: 0
size: 0 bytes
in-pack: 301
packs: 1
size-pack: 20.86 MiB
blob count > 20 MB: 0
```

Largest remaining blob:

```text
4.02 MB notebooks/10_cbis_gradcam_explainability.ipynb
```

Estimated clean push size: about 21 MB before adding the current documentation/API/CI changes.

## Current Conclusion

The failed `git push` pack of about 2.82 GiB was caused by historical CBIS-DDSM image blobs plus model artifacts in local history. The cleaned repository no longer has reachable large dataset/model blobs.
