# TCIA / CBIS-DDSM Data and Demo Asset Attribution

**Document Version**: 1.0.0  
**Date**: 2026-09-12  
**Status**: **PROVENANCE VERIFIED**  
**Collection**: Curated Breast Imaging Subset of Digital Database for Screening Mammography (CBIS-DDSM)  
**Host Archive**: The Cancer Imaging Archive (TCIA)  
**License**: Creative Commons Attribution 3.0 Unported (CC BY 3.0)  

---

## 1. Executive Summary

This document establishes the verified scientific and legal provenance for the two demonstration mammography images committed in `frontend/assets/demo-images/` of the Breast Cancer AI Studio repository.

Prior to Phase G1, these assets were cataloged under a Pre-Deploy Blocker (P0) to ensure compliance with The Cancer Imaging Archive (TCIA) Data Usage Policy. A comprehensive byte-level cryptographic audit of dataset archives and processing manifests has traced both files to exact source instances within the CBIS-DDSM collection.

Both demo assets are confirmed as derived research artifacts under the **Creative Commons Attribution 3.0 Unported License (CC BY 3.0)**. The P0 blocker is formally **RESOLVED**.

---

## 2. Asset Provenance & Cryptographic Census

| Property | Benign Demo Asset | Malignant Demo Asset |
| :--- | :--- | :--- |
| **Local File Path** | `frontend/assets/demo-images/demo-benign-mammogram.png` | `frontend/assets/demo-images/demo-malignant-mammogram.png` |
| **SHA-256 Checksum** | `3876586b8d712a4782c790bdc184bd602ec6432be2a228fe1b3cabc7252c3dbe` | `966a7860655798e6f061392d3cedbd9e8ca57db8c37a5776ca16735d7837e8ac` |
| **Byte Size** | 82,345 bytes (80.4 KB) | 75,533 bytes (73.8 KB) |
| **Resolution** | $224 \times 224$ pixels, 8-bit RGB PNG | $224 \times 224$ pixels, 8-bit RGB PNG |
| **Matched Preprocessed Path** | `data/cbis_ddsm/processed/images_roi/test/benign/1.3.6.1.4.1.9590.100.1.2.16525291111973690409014716492507936377__1-247.png` | `data/cbis_ddsm/processed/images_roi/test/malignant/1.3.6.1.4.1.9590.100.1.2.404758686111730252108640081234072137432__1-076.png` |
| **TCIA SOP / Series UID** | `1.3.6.1.4.1.9590.100.1.2.16525291111973690409014716492507936377` | `1.3.6.1.4.1.9590.100.1.2.404758686111730252108640081234072137432` |
| **CBIS Manifest Split** | Test Partition (`manifests/cbis_group_split_seed42.csv`) | Test Partition (`manifests/cbis_group_split_seed42.csv`) |
| **Histological Ground Truth** | Benign lesion | Malignant lesion |
| **Frozen EfficientNet Raw Prob** | $0.4245 < 0.515$ (Classified: Benign) | $0.6136 \ge 0.515$ (Classified: Malignant) |
| **Initial Git Introduction** | Commit `ad94c7a` (2026-09-04) | Commit `ad94c7a` (2026-09-04) |
| **Provenance Status** | **PROVENANCE VERIFIED** | **PROVENANCE VERIFIED** |

---

## 3. Mandatory Citations & Attribution

Per the TCIA Data Usage Policy and the authors' publication terms, users and redistributors of CBIS-DDSM data must provide the following citations in academic and public distributions:

### 3.1 Data Collection Citation
> Sawyer-Lee, R., Gimenez, F., Hoogi, A., & Rubin, D. (2016).  
> **Curated Breast Imaging Subset of Digital Database for Screening Mammography (CBIS-DDSM)** [Data set].  
> The Cancer Imaging Archive.  
> DOI: [10.7937/K9/TCIA.2016.7O02S9CY](https://doi.org/10.7937/K9/TCIA.2016.7O02S9CY)

### 3.2 Primary Publication Citation
> Lee, R. S., Gimenez, F., Hoogi, A., Miyake, K. K., Gorovoy, M., & Rubin, D. L. (2017).  
> **A curated mammography data set for use in computer-aided detection and diagnosis research.**  
> *Scientific Data*, 4, 170177.  
> DOI: [10.1038/sdata.2017.177](https://doi.org/10.1038/sdata.2017.177)

### 3.3 TCIA Archive Citation
> Clark, K., Vendt, B., Smith, K., Freymann, J., Kirby, J., Koppel, P., Phillips, S., Eberle, D., Rubin, D., & Saltz, J. (2013).  
> **The Cancer Imaging Archive (TCIA): Maintaining and Operating a Public Information Repository.**  
> *Journal of Digital Imaging*, 26(6), 1045–1057.  
> DOI: [10.1007/s10278-013-9622-7](https://doi.org/10.1007/s10278-013-9622-7)

---

## 4. License Terms: Creative Commons Attribution 3.0 (CC BY 3.0)

Under the terms of CC BY 3.0, you are free to:
- **Share**: Copy and redistribute the material in any medium or format.
- **Adapt**: Remix, transform, and build upon the material for any purpose, including commercial.

**Under the following terms**:
- **Attribution**: You must give appropriate credit, provide a link to the license, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.
- **No additional restrictions**: You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.

Full license text: [https://creativecommons.org/licenses/by/3.0/](https://creativecommons.org/licenses/by/3.0/)

---

## 5. Preprocessing & Derivation Pipeline

The original full-resolution CBIS-DDSM mammograms were captured via film digitizers (Lumisys, Howtek) with native resolutions exceeding $3000 \times 5000$ pixels at 12-bit or 16-bit depth.

The demo assets were derived through the standardized study preprocessing pipeline:
1. **Source Selection**: Selected from the held-out test partition of the inferred-group split (`manifests/cbis_group_split_seed42.csv`).
2. **Cropping / Normalization**: Centered on the region of interest with surrounding parenchyma context, aspect-ratio preserved.
3. **Resizing**: Bilinear interpolation to the input dimensions required by EfficientNet-B0 ($224 \times 224 \times 3$).
4. **Quantization**: Exported as 8-bit per channel RGB PNG files for browser canvas compatibility.
5. **Quality Verification**: Verified that pixel values preserve tissue contrast without lossy JPEG compression artifacts.
