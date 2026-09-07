# Frontend Redesign V3 — Product Specification (Revised)

**Document Status:** Phase 0 Product & UX Blueprint (Revised)  
**Target Branch:** `feat/frontend-redesign-v3`  
**Base Commit SHA:** `5246fa19037831726b5e74c5db5db24e09c0454d`  
**Date:** 2026-09-07  
**Author:** Senior Product Designer & Senior Frontend Architect  

---

## 1. Product Vision & Positioning: "Breast Health Intelligence Studio"

### 1.1 The Visual & Conceptual Target
The platform is reborn as the **"Breast Health Intelligence Studio"**.  
It represents an original, high-elegance fusion of:
1. **Premium Healthcare Editorial Design:** Calm, generous whitespace, bespoke typography hierarchy, and human-centered clinical storytelling.
2. **Authentic Medical & Scientific Imagery:** Curated mammograms, anatomical diagrams, cellular histology, and lab research scenes—used purposefully to anchor every concept.
3. **Transparent AI Research Visualization:** Clear statistical scorecards, interactive confusion matrices, and explainability maps (SHAP & Grad-CAM).
4. **Interactive Analysis Laboratory:** High-precision workspaces for structured cytological ML and mammography DL inference with explicit decision thresholds.
5. **Public Medical Education Hub (LEARN):** An evidence-based learning center covering tumor biology, screening guidelines, lifestyle & nutrition facts, and a curated medical video library.

### 1.2 Non-Negotiable Scientific & Safety Boundaries
- **Research / Educational Prototype Only:** `clinical_use: false`. The platform is **NOT** a certified diagnostic medical device.
- **Strictly Frozen Research Candidates:**
  - Study A (WDBC): Logistic Regression, raw classification threshold **$\ge 0.36$**.
  - Study B (CBIS-DDSM): EfficientNet-B0 full image, raw classification threshold **$\ge 0.515$**. Platt scaling is strictly for **display/reliability assessment**, never classification.
  - Multimodal: 40% ML + 60% DL is an **experimental software demonstration heuristic** on unpaired cohorts.
- **Responsible Health Communication:**
  - Educational content must be attributed to verified public health organizations (NCI, CDC, WHO, ACS).
  - Nutrition content must explicitly avoid claiming that any food "cures" or "treats" cancer; it must present evidence-based general lifestyle patterns and direct users to qualified dietitians/clinicians.

---

## 2. Top-Navigation Architecture & App Chrome

### 2.1 The Departure from Sidebars
The user explicitly rejected all forms of left-side navigation (persistent sidebars, floating sidebar cards, icon rails, and classic admin layouts).  
The Studio adopts a **full-width, top-based global navigation system** that frees 100% of horizontal screen width for medical imaging, research scorecards, and multi-column comparison tables.

### 2.2 Global Top Navigation Bar (Desktop)
A sticky, backdrop-blurred header (`height: 72px; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(16px); border-bottom: 1px solid var(--border-subtle);`):
```
[ Brand: BreastCare AI Studio ]   Explore   Analyze ▾   Research ▾   Learn ▾   Workspace ▾   AI Guide     [ Telemetry Pill ]  [ Sign In / User Menu ]
```

#### Mega-Menus & Contextual Dropdowns:
- **Analyze ▾ (Mega-Menu):**
  - *Structured Feature ML:* 30 FNA cytological inputs, frozen Logistic Regression (`threshold 0.36`).
  - *Mammography AI:* Full-image scan analysis, frozen EfficientNet-B0 (`threshold 0.515`).
  - *Experimental Multimodal:* Side-by-side heuristic fusion (40/60).
- **Research ▾ (Mega-Menu):**
  - *Research Center:* Master narrative & methodology breakdown.
  - *Model Benchmarks:* Tabular comparison with 95% bootstrap CIs.
  - *Dataset Explorer:* WDBC & CBIS-DDSM manifest splits and leakage audits.
  - *Explainability:* SHAP log-odds and Grad-CAM attention visualizations.
  - *Reliability & Calibration:* Brier scores and Platt calibration curves.
- **Learn ▾ (Mega-Menu):**
  - *Understanding Breast Cancer:* Tumor biology, benign vs. malignant, risk factors.
  - *Screening & Mammography:* How screening works, imaging types, AI limits.
  - *Nutrition & Lifestyle:* Evidence-based eating patterns, activity, body weight.
  - *Myths & Facts:* Common misconceptions debunked with peer-reviewed science.
  - *Video Library:* Curated educational lectures from trusted health organizations.
- **Workspace ▾ (Contextual Dropdown):**
  - *Patient Registry:* Doctor-only cohort management (locked/hidden for standard users).
  - *Prediction History:* Personal or patient analysis logs.
  - *Prediction Reports:* Authenticated print-ready diagnostic-support summaries.
- **AI Guide:** One-click direct link to the AI Information Assistant.

### 2.3 Horizontal Page Context Row & Secondary Tabs
Below the global topbar, pages within complex domains (Research, Workspace, Learn) feature an editorial context header with clean horizontal sub-tabs:
- **Research Context Header:**
  `Research Studio`  
  `[ Overview ]   [ Benchmarks ]   [ Datasets ]   [ Explainability ]   [ Reliability & Calibration ]`
- **Workspace Context Header (Doctor):**
  `Research Workspace`  
  `[ Patient Registry ]   [ Prediction History ]   [ Diagnostic Reports ]`
- **Learn Context Header:**
  `Medical Education Hub`  
  `[ All Topics ]   [ Biology ]   [ Screening ]   [ Nutrition & Lifestyle ]   [ Myths vs. Facts ]   [ Video Library ]`

### 2.4 Tablet & Mobile Navigation Experience
- **Not a standard hamburger drawer:** Mobile and tablet viewports use an **intentional full-screen top-sheet overlay** that expands gracefully downwards from the topbar with smooth staggering animations.
- **Categorized Sections:** Clean accordion panels for *Analyze*, *Research*, *Learn*, and *Workspace*.
- **Direct Action Triggers:** Prominent buttons for `[Run Quick Analysis]` and `[Sign in with Google]`.

---

## 3. Public Medical Education Content Hub (LEARN)

The **Learn Hub** is an integrated public visual educational resource designed to empower patients, students, and researchers with evidence-based health knowledge.

### 3.1 Topic A: Understanding Breast Cancer
- **Cellular Biology:** What breast tissue is composed of; how normal cells transform into tumors.
- **Benign vs. Malignant:** Explaining fibroadenomas, cysts, and benign calcifications versus invasive carcinomas (ductal and lobular).
- **Staging & Terminology:** Demystifying terms like *in situ*, *metastasis*, *lymph nodes*, *biopsy*, and *histopathology*.
- **Risk Factors:** Genetic factors (BRCA1/2), age, family history, reproductive factors, and dense breast tissue.
- **Visuals:** Medical anatomical illustrations of the mammary gland and cellular histology graphics.

### 3.2 Topic B: Screening & Mammography
- **Screening Fundamentals:** Why early detection matters; screening mammograms vs. diagnostic mammograms.
- **The Procedure:** What to expect during a mammogram, positioning, compression, and radiation dose facts.
- **Dense Breasts:** Why dense breast tissue can mask lesions on standard 2D mammograms and when supplemental ultrasound or MRI is considered.
- **The Role & Limitations of AI:** How computer vision assists triage and screening; why AI is an assistive research signal and **never** a standalone diagnostic authority.
- **Visuals:** High-resolution anonymized mammography scans showing microcalcifications and circumscribed masses.

### 3.3 Topic C: Evidence-Based Nutrition & Lifestyle
- **Healthy Eating Patterns:** Emphasizing diverse vegetables, fruits, whole grains, and lean legumes/proteins.
- **Physical Activity:** Guidelines for moderate aerobic activity (150–300 min/week) and its correlation with long-term metabolic health.
- **Alcohol Context:** Honest evidence regarding alcohol intake and breast cancer risk factors.
- **Strict Medical Disclaimer:**
  > [!IMPORTANT]
  > **No food or supplement cures or treats breast cancer.** Diet and lifestyle are factors in overall long-term wellness and risk reduction, not a substitute for clinical medical care, surgery, or oncology therapy. Always consult a qualified physician or registered dietitian for individual health decisions.
- **Visuals:** High-aesthetic photography of Mediterranean-style whole foods, colorful produce, and active wellness scenes.

### 3.4 Topic D: Myths vs. Facts
Interactive card deck addressing pervasive misconceptions:
- *Myth:* "An injury or bump to the breast causes breast cancer." → *Fact:* Trauma does not cause cancer, though it may draw attention to an existing lump.
- *Myth:* "Mammograms cause breast cancer to spread." → *Fact:* Compression does not spread cancer; radiation doses from modern digital mammography are extremely low.
- *Myth:* "Only women with a family history get breast cancer." → *Fact:* Over 75% of individuals diagnosed with breast cancer have no known family history.
- *Myth:* "Antiperspirants and underwire bras cause cancer." → *Fact:* Extensive epidemiological studies have found zero causal link between deodorants or bras and breast cancer.

### 3.5 Topic E: Curated Medical Video Library
- **Architecture:** Professional video cards featuring high-resolution poster thumbnails, topic tags, duration badges, authoring institutions (e.g., National Cancer Institute, CDC, Johns Hopkins Medicine), and a concise written abstract.
- **Performance & Privacy:** Videos are **lazy-loaded**. No raw iframes are embedded on page load; players instantiate only upon user click via privacy-conscious `youtube-nocookie.com` or local embeds.
- **Curated Video Roster:**
  1. *Understanding Mammograms & Early Screening* (Source: National Cancer Institute / CDC).
  2. *How Breast Cancer Develops: Cellular Perspective* (Source: Dana-Farber Cancer Institute).
  3. *Nutrition, Exercise, and Long-Term Breast Health* (Source: Memorial Sloan Kettering Cancer Center).
  4. *Dense Breasts Explained* (Source: American College of Radiology).

---

## 4. Medical Imagery Strategy & Visual Storytelling

### 4.1 Purposeful Imagery Hierarchy
Images are deployed as vital clinical and educational anchors, avoiding generic stock-photo spam:

| Category | Typical Usage | Format & Target Size | Visual Tone & Guidelines |
|---|---|---|---|
| **Mammography Scans** | DL Studio, Screening Learn Module, Hero | WebP, 1200x1200px max | Dark radiological background (`#0b1329`), high-contrast grayscale, annotated ROIs with subtle teal bounding boxes. |
| **Breast Anatomy & Histology** | Biology Learn Module, WDBC Cytology Context | SVG / WebP, 800x600px | Clean medical editorial vector illustrations; clear anatomical labels; neutral clinical coloring. |
| **Laboratory & AI Research** | Landing Page, Model Telemetry, Research Hub | WebP, 1600x900px | High-aperture photography of pathology microscopes, high-performance computing clusters, and researchers collaborating. |
| **Nutrition & Wellness** | Nutrition Learn Module | WebP, 800x600px | Natural light photography of fresh produce, legumes, and whole grains; vibrant, uplifting, and authentic. |
| **Clinician & Patient Care** | Workspace, Auth Split Panels, About | WebP, 1200x800px | Empathetic, respectful, professional clinical interactions. |

### 4.2 Content Governance & Asset Metadata
All educational and media assets are managed under a structured content layer (`frontend/content/`):
```typescript
interface EducationalArticle {
  title: string;
  slug: string;
  category: 'biology' | 'screening' | 'nutrition' | 'myths' | 'videos';
  summary: string;
  bodyHtml: string;
  sourceOrg: string;        // e.g. "National Cancer Institute"
  sourceUrl: string;        // e.g. "https://www.cancer.gov/..."
  reviewedDate: string;     // e.g. "2026-08-15"
  heroImage: {
    src: string;
    alt: string;
    caption: string;
    license: string;
  };
  video?: {
    embedUrl: string;
    duration: string;
    publisher: string;
  };
}
```

---

## 5. Landing Page 12-Beat Storytelling Sequence

The homepage abandons simple card grids to deliver an immersive editorial narrative:
1. **Beat 01 — Immersive Visual Hero:** Full-viewport editorial composition pairing a high-resolution dark mammography scan and fine-needle aspirate cell graphic with headline: *"Precision Breast Health Intelligence & AI Research Studio"*. Live system telemetry pill + immediate action buttons.
2. **Beat 02 — Mission & Dual-Domain Vision:** Editorial statement connecting rigorous data science with human health empowerment.
3. **Beat 03 — Two Independent Research Studies:** Full-width asymmetric split comparing **Study A (WDBC Tabular ML)** and **Study B (CBIS-DDSM Mammography DL)**. Emphasizing distinct cohorts and zero cross-dataset leakage.
4. **Beat 04 — Interactive Analysis Preview:** Live interactive widget allowing visitors to preview the dual-probability gauge and test sample predictions directly.
5. **Beat 05 — Understanding Breast Health:** Image-led editorial feature introducing the new Learn Hub, with direct links to tumor biology and benign vs. malignant concepts.
6. **Beat 06 — Screening & Mammography Story:** Visual guide to mammography imaging, dense breast considerations, and assistive AI boundaries.
7. **Beat 07 — Evidence-Based Nutrition & Lifestyle:** Vibrant split-card highlighting physical activity and whole-food nutrition facts with medical disclaimers.
8. **Beat 08 — Transparency & Explainability:** Visual preview of SHAP feature contributions and Grad-CAM coarse attention heatmaps.
9. **Beat 09 — Featured Video:** Prominent video player showcasing a curated lecture on early detection from a recognized health institution.
10. **Beat 10 — Safety Boundaries & Limitations:** High-contrast clinical safety block detailing prototype scope, lack of regulatory clearance, and absence of external clinical validation.
11. **Beat 11 — Research Team & Academic Provenance:** Profiles of the research team (Nguyễn Bá Duy, Trần Mỹ Anh, Hoàng Nhật Anh, Nguyễn Huy Giang, Ngô Tiến Đạt; Supervisor: Đoàn Thị Thanh Hằng).
12. **Beat 12 — Call to Action:** Split action banner: `[Explore Research Center]` or `[Launch Analysis Studio]`.

---

## 6. Authentication Architecture & Security Overhaul

### 6.1 Open Public Registration (`role = user`)
- Anyone may create an account to access the AI Analysis Lab, saved prediction history, and AI Advisor.
- **Security Rule:** Public registration strictly and irrevocably assigns `role = 'user'`. The client cannot pass or request a `doctor` role.
- **Doctor Role Promotion:** Privileged doctor access (which unlocks the Patient Registry and patient-linked predictions) requires an administrative promotion step.

### 6.2 Sign in with Google (OAuth 2.0 / OpenID Connect)
- **Frontend Integration:** Official Google Identity Services SDK (`https://accounts.google.com/gsi/client`) rendering a branded `Continue with Google` button.
- **Backend Verification (`POST /api/v1/auth/google/`):**
  1. Receives the Google ID token JWT credential.
  2. Server-side token validation: Verifies Google signature using Google's public keys (`google.oauth2.id_token` or `pyjwt` against Google certs).
  3. Validates issuer (`accounts.google.com` or `https://accounts.google.com`), audience (`GOOGLE_CLIENT_ID`), and expiry.
  4. Extracts Google subject (`sub`), `email`, and `name`. Requires `email_verified == true`.
- **Database Schema Extension:**
  ```sql
  CREATE TABLE IF NOT EXISTS oauth_accounts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      provider TEXT NOT NULL,
      provider_subject TEXT NOT NULL,
      email TEXT NOT NULL,
      created_at TEXT NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
      UNIQUE(provider, provider_subject)
  );
  ```
- **Account Linking Behavior:**
  - If a user with the verified Google email already exists in `users`, automatically and safely link their Google identity in `oauth_accounts` without creating duplicate accounts.
  - If no user exists, create a new row in `users` (`role = 'user'`, `password_hash = NULL`) and record the link.
  - Issue the standard application session token into `sessions`, preserving seamless Bearer token authentication for all existing endpoints.

### 6.3 Premium Auth Visual Direction
- Modern split-screen composition:
  - **Left / Hero Canvas (55%):** High-resolution medical imaging background with soft ambient dark gradient, animated scientific particle mesh, key research metric badges (`ROC-AUC 99.54%`), and breast-health educational microcopy.
  - **Right / Form Canvas (45%):** Pristine white card container with:
    - Studio logo + welcome title.
    - `[Continue with Google]` button (official styling).
    - Subtle horizontal divider: `or sign in with email`.
    - Form fields (Email, Password, Remember session).
    - Clear password visibility toggles and recovery links.
    - Zero role selection inputs for public registrants.

---

## 7. Responsible Research Phrasing & Terminology Guardrails

To prevent misleading medical claims while elevating product feel, the following naming conventions are enforced across all UI surfaces:

| Unsafe / Clinical Claim Term (FORBIDDEN) | Approved Research Phrasing (MANDATORY) | Rationale |
|---|---|---|
| *Clinical AI Workspace* | **AI Analysis Lab** | Clarifies experimental/laboratory research setting. |
| *Diagnostic Report Center* | **Prediction Reports** | Distinguishes AI outputs from official medical diagnoses. |
| *Clinician AI Diagnosis* | **Model Prediction / Classification** | Reaffirms statistical output rather than clinician verdict. |
| *DL Screening Diagnosis* | **Mammography AI Analysis** | Accurately describes computer vision assistance. |
| *Anti-Cancer Diet / Cancer Cure Diet* | **Evidence-Based Nutrition & Lifestyle** | Complies with oncology communication ethics. |
| *Patient Diagnosis Timeline* | **Prediction History Timeline** | Clarifies history logs model predictions, not patient medical charts. |
