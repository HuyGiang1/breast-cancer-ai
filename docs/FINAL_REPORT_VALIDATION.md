# Final Report Validation

Validation date: 2026-09-07  
Branch: `docs/final-documentation`  
Result: **PASS**

## Deliverables

- Source: `docs/report/FINAL_RESEARCH_REPORT_VI.md`
- DOCX: `docs/report/NGHIEN_CUU_CAC_MO_HINH_NHAN_DANG_PHAN_LOAI_KHOI_U_VU_AC_TINH.docx`
- PDF: `docs/report/NGHIEN_CUU_CAC_MO_HINH_NHAN_DANG_PHAN_LOAI_KHOI_U_VU_AC_TINH.pdf`
- Generator: `scripts/build_final_report.py`
- Validator: `scripts/validate_final_report.py`

The prior official Markdown source was located in Git history at the parent of `612dc6f`, where it had been removed during public-repository pruning. It contained preliminary split/model/runtime claims and missing identity fields, so the final source was rewritten from frozen evidence rather than restored as final evidence. The obsolete template-dependent DOCX exporter was retired; the new generator builds both output formats from one source.

## Scientific checklist

- [x] Official Vietnamese and English titles are correct.
- [x] Students: Nguyễn Bá Duy, Trần Mỹ Anh, Hoàng Nhật Anh, Nguyễn Huy Giang, Ngô Tiến Đạt.
- [x] Supervisor: Đoàn Thị Thanh Hằng.
- [x] Actual task is benign versus malignant classification.
- [x] WDBC: 569 samples, 30 FNA-derived features, 212 malignant, 357 benign, 455 development, 114 held-out test, seed 42.
- [x] ML selection is development five-fold OOF; Logistic Regression is primary.
- [x] LR test metrics and TN/FP/FN/TP match frozen snapshot.
- [x] ML classification uses raw malignant probability `>= 0.36`.
- [x] CBIS: 2,559 source images, 2,559 ROI representations, and 5,118 manifest rows.
- [x] Report does not call 5,118 rows independent mammograms or patients.
- [x] CBIS has 2,354 inferred study-like groups and group split 1,648/353/353.
- [x] Full-image counts are 1,777/390/392 with zero measured group overlap.
- [x] CBIS grouping is not described as verified patient-level.
- [x] EfficientNet-B0 full processed image is the retained DL candidate.
- [x] DL metrics and TN/FP/FN/TP match frozen snapshot.
- [x] DL classification uses raw probability `>= 0.515`.
- [x] Platt probability is display/reliability only and is not thresholded at 0.515.
- [x] Validation Brier/ECE calibration values match frozen evidence.
- [x] ROI-C decision is validation-first and retains full images.
- [x] SHAP is contribution to malignant log-odds, not causal biology/clinical importance.
- [x] Grad-CAM is coarse attention, not segmentation/localization/pathology truth.
- [x] WDBC and CBIS-DDSM remain separate; there is no ML-versus-DL ranking.
- [x] 40/60 multimodal output is an unpaired `experimental_only` demo with no final accuracy claim.
- [x] `clinical_use=false`; report does not promote diagnosis or clinical-grade use.
- [x] Frontend is static HTML/CSS plus vanilla JavaScript ES Modules with 21 canonical routes.

## Structure and formatting

- [x] A4 page size with consistent 3 cm left, 2 cm right, 2.2 cm top, and 2 cm bottom margins.
- [x] Times New Roman with a consistent heading hierarchy and justified body text.
- [x] Cover, bilingual summary, contents, 13 main sections, references, and appendices.
- [x] Footer page numbering on every PDF/DOCX section.
- [x] Seven tables use grid/header styling, repeating headers, and no row splitting in DOCX.
- [x] Nineteen embedded figures/screenshots have centered captions and preserved aspect ratio.
- [x] Scientific figures come from `paper_artifacts/`; software figures come from the optimized final screenshot set.
- [x] No patient-identifying data, password, bearer token, private email, or local path appears in screenshots.

## PDF visual QA

All 29 PDF pages were rendered and inspected in four contact sheets. Result:

- [x] No missing Vietnamese characters.
- [x] No clipped table, chart, caption, or body text.
- [x] No stretched image.
- [x] No accidental blank page.
- [x] No orphaned caption separated from its figure.
- [x] Page numbers are present and continuous.
- [x] Contents list and section order are coherent.

## DOCX/PDF consistency

Both files are generated in one command from the same Markdown block tree. Automated validation extracts text from both formats and requires the official identity, frozen candidate names, raw DL threshold contract, `clinical_use=false`, and `experimental_only` language in each. DOCX has 19 inline figures and seven tables; PDF has 29 nonblank pages. Validation reports snapshot/source/DOCX/PDF consistency.

The generator fixes document metadata and normalizes the DOCX archive. Two consecutive builds produced identical checksums:

- DOCX: `5af54c61f49b6152f64e6b4e2fc6eb961b6b7ac51577d9d3eab0268411e42c3d`
- PDF: `f8935e2e62c096c8540c227613e4e98c1ceaad5e704c175de82101479dae27a7`

## Legacy/preliminary audit

Final-facing files were searched for old folder-split claims, patient-level claims, 5,118-image/patient claims, Custom CNN final/deployed claims, ML threshold 0.50, calibrated-threshold 0.515, cross-dataset ML-versus-DL ranking, clinical-grade/validated use, validated multimodal claims, React/Next.js architecture claims, legacy monolith claims, and missing-server wording.

Historical research documents were not globally deleted. Final conclusions use only frozen evidence. Server wording now states that a server is available, production deployment has not yet been executed, access/configuration is pending, and domain/DNS/HTTPS/public smoke are pending unless configured in the deployment phase.

## Automated command

```bash
venv/bin/python scripts/build_final_report.py
venv/bin/python scripts/validate_final_report.py
```

Expected result:

```text
FINAL REPORT VALIDATION: PASS
PDF pages: 29
DOCX figures: 19
DOCX tables: 7
Scientific contract: snapshot/source/DOCX/PDF consistent
```
