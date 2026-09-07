# Frontend Redesign V3 — Design System Specification (Revised)

**Document Status:** Phase 0 Design System Architecture (Revised)  
**Target Branch:** `feat/frontend-redesign-v3`  
**Base Commit SHA:** `5246fa19037831726b5e74c5db5db24e09c0454d`  
**Date:** 2026-09-07  
**Author:** Senior Product Designer & Design Systems Engineer  

---

## 1. Visual Language: "Breast Health Intelligence Studio"

The design system is constructed around the **"Breast Health Intelligence Studio"** aesthetic:
1. **Clinical Calm & High Trust:** Deep slate ink (`#0f172a`), crisp white canvases (`#ffffff`), and warm-slate neutral surfaces (`#f8fafc`).
2. **Editorial Medical Storytelling:** Generous whitespace, asymmetric editorial layouts, image-led content compositions, and bespoke typographic hierarchies.
3. **Calibrated Semantic Accents:**
   - **Research Emerald / Teal:** Primary brand and active accents (`#0d9488` / `#0f766e`), symbolizing clinical precision and cellular vitality.
   - **Clinical Sapphire:** Secondary analytic accents (`#2563eb`), used for comparative models, datasets, and metadata.
   - **Restrained Semantic Alerts:** Amber (`#d97706`) strictly for threshold warnings/uncertainty; Rose/Crimson (`#e11d48`) strictly for malignant indicators and critical errors.
4. **Top-Based Full-Width Canvas:** Complete removal of left-side navigation bars in favor of a sticky horizontal global navigation header and contextual sub-tab ribbons.

---

## 2. Design Tokens

### 2.1 Color Palette & Semantic Tokens
```css
:root {
  /* Neutral Palette (Slate & Ink) */
  --slate-50:  #f8fafc;
  --slate-100: #f1f5f9;
  --slate-200: #e2e8f0;
  --slate-300: #cbd5e1;
  --slate-400: #94a3b8;
  --slate-500: #64748b;
  --slate-600: #475569;
  --slate-700: #334155;
  --slate-800: #1e293b;
  --slate-900: #0f172a;
  --slate-950: #020617;

  /* Primary Research Accent (Emerald / Teal) */
  --teal-50:  #f0fdfa;
  --teal-100: #ccfbf1;
  --teal-200: #99f6e4;
  --teal-300: #5eead4;
  --teal-400: #2dd4bf;
  --teal-500: #14b8a6;
  --teal-600: #0d9488;
  --teal-700: #0f766e;
  --teal-800: #115e59;
  --teal-900: #134e4a;

  /* Secondary Clinical Accent (Sapphire Blue) */
  --blue-50:  #eff6ff;
  --blue-100: #dbeafe;
  --blue-500: #3b82f6;
  --blue-600: #2563eb;
  --blue-700: #1d4ed8;

  /* Semantic Status Palette */
  --success-bg:   #ecfdf5;
  --success-line: #a7f3d0;
  --success-text: #047857;
  --benign-color: #059669;

  --warning-bg:   #fffbeb;
  --warning-line: #fde68a;
  --warning-text: #b45309;
  --warn-marker:  #d97706;

  --danger-bg:    #fff1f2;
  --danger-line:  #fecdd3;
  --danger-text:  #be123c;
  --malig-color:  #e11d48;

  /* Surface & Canvas System */
  --canvas-bg:          var(--slate-50);
  --surface-card:       #ffffff;
  --surface-elevated:   #ffffff;
  --surface-topbar:     rgba(255, 255, 255, 0.88);
  --surface-dropdown:   #ffffff;
  --surface-hover:      var(--slate-100);
  --surface-active:     var(--teal-50);
  --border-subtle:      var(--slate-200);
  --border-strong:      var(--slate-300);

  /* Typography Colors */
  --text-main:          var(--slate-900);
  --text-muted:         var(--slate-500);
  --text-subtle:        var(--slate-400);
  --text-on-accent:     #ffffff;
}
```

### 2.2 Typography Scale
```css
:root {
  --font-sans: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;

  /* Fluid Type Scale */
  --text-xs:   0.75rem;    /* 12px */
  --text-sm:   0.875rem;   /* 14px */
  --text-base: 1rem;       /* 16px */
  --text-lg:   1.125rem;   /* 18px */
  --text-xl:   1.25rem;    /* 20px */
  --text-2xl:  1.5rem;     /* 24px */
  --text-3xl:  1.875rem;   /* 30px */
  --text-4xl:  2.25rem;    /* 36px */
  --text-5xl:  3rem;       /* 48px */

  /* Font Weights */
  --weight-regular:  400;
  --weight-medium:   500;
  --weight-semibold: 600;
  --weight-bold:     700;
  --weight-black:    800;

  /* Line Heights */
  --leading-tight:   1.15;
  --leading-snug:    1.3;
  --leading-normal:  1.5;
  --leading-relaxed: 1.65;
}
```

### 2.3 Spacing & Layout Scale
```css
:root {
  --space-1:  0.25rem;  /* 4px */
  --space-2:  0.5rem;   /* 8px */
  --space-3:  0.75rem;  /* 12px */
  --space-4:  1rem;     /* 16px */
  --space-5:  1.25rem;  /* 20px */
  --space-6:  1.5rem;   /* 24px */
  --space-8:  2rem;     /* 32px */
  --space-10: 2.5rem;   /* 40px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */
  --space-20: 5rem;     /* 80px */

  /* Structural Dimensions */
  --topbar-height: 72px;
  --subnav-height: 52px;
  --max-content-width: 1440px;
}
```

### 2.4 Radii & Shadow Scales
```css
:root {
  --radius-xs: 4px;
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-2xl: 24px;
  --radius-full: 9999px;

  /* Multi-Layered Elevation Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(15, 23, 42, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(15, 23, 42, 0.07), 0 2px 4px -2px rgba(15, 23, 42, 0.05);
  --shadow-lg: 0 10px 15px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -4px rgba(15, 23, 42, 0.04);
  --shadow-xl: 0 20px 25px -5px rgba(15, 23, 42, 0.1), 0 8px 10px -6px rgba(15, 23, 42, 0.04);
  --shadow-dropdown: 0 25px 50px -12px rgba(15, 23, 42, 0.18);
}
```

---

## 3. UI Component Specifications

### 3.1 Global Topbar & Mega-Menu System (`.studio-topbar`)
- **Structure:** Sticky topbar with `backdrop-filter: blur(16px)` and high-efficiency flex layout.
- **Brand Identity:** Left-aligned SVG emblem with "BreastCare AI" in bold Inter + small pill tag `Studio`.
- **Top-Level Navigation Items:**
  - `Explore` (Direct link to `/index.html`)
  - `Analyze ▾` (Mega-menu dropdown)
  - `Research ▾` (Mega-menu dropdown)
  - `Learn ▾` (Mega-menu dropdown)
  - `Workspace ▾` (Contextual dropdown; indicates Doctor role status)
  - `AI Guide` (Direct link to `/pages/advisor.html`)
- **Right Utilities:**
  - Live system telemetry pulse indicator (`Runtime Online · Checksum Verified`).
  - Auth Action / Profile Avatar Menu (`[Sign In]` or User avatar with role tag).
- **Mega-Menu Overlay (`.studio-mega-menu`):**
  - High-density multi-column panel appearing smoothly below the active nav item.
  - Features categorized item cards with iconography, clear subtitles, and preview thumbnails.

### 3.2 Horizontal Context Header & Sub-Tabs (`.studio-context-nav`)
- Positioned immediately below the global topbar on multi-page domains.
- Displays the current workspace title alongside horizontal pill tabs:
  - Active tab indicated by solid teal background or bold underline accent with soft glow.
  - Zero lateral screen space consumed, preserving a wide full-bleed workspace.

### 3.3 Full-Screen Top-Sheet Navigation (Tablet & Mobile)
- Smooth top-sheet overlay that expands downward from the header upon menu trigger.
- Full viewport height, scrollable, with categorized accordions for *Analyze*, *Research*, *Learn*, and *Workspace*.
- Dedicated quick-action buttons for Google Sign-In and Analysis shortcuts.

### 3.4 Medical Image Storytelling Components
- **Image-Text Split Stage (`.studio-split-stage`):** 50/50 or 60/40 asymmetric layout pairing high-resolution medical photography or scans with editorial typography.
- **Radiological Inspection Viewer (`.studio-scan-viewer`):** Deep dark canvas (`#0b1329`) with subtle grid crosshairs, image metadata ribbon, and zoom/pan capabilities.
- **Editorial Card with Photo (`.studio-media-card`):** High-aspect-ratio image banner, category pill tag, headline, and read time badge.

### 3.5 Lazy Video Cards (`.studio-video-card`)
- High-resolution poster thumbnail with centered frosted-glass play button.
- Metadata bar: Video duration, authoring health organization (CDC, NCI, etc.), and concise summary.
- On click: In-place transition to a privacy-conscious iframe player (`youtube-nocookie.com`).

### 3.6 Dual-Probability & Decision Gauges
- **Gauge 1: Classification Decision (Raw Probability):**
  - Linear meter (0–100%) with vertical marker line at exact decision cutoff (`36.0%` for ML, `51.5%` for DL).
  - High-contrast distance label: `+18.4% above decision threshold` or `-12.1% below decision threshold`.
- **Gauge 2: Reliability Scaling (Platt Calibrated - DL Only):**
  - Muted secondary gauge labeled explicitly: *Display & Reliability Calibration Only*.

### 3.7 Form Fields & 1-Click Benchmark Presets
- **Preset Action Bar:** Top-level buttons to populate standard test vectors:
  - `[Load Typical Benign Sample]`
  - `[Load Typical Malignant Sample]`
  - `[Load Borderline Case]`
  - `[Reset Form]`
- **Categorized Parameter Tabs:** Grouping the 30 WDBC features into *Cellular Size & Shape (Mean)*, *Measurement Variance (Standard Error)*, and *Worst-Case Extremes (Worst)*.

---

## 4. Breakpoint & Responsive System

| Breakpoint | Target Devices | Layout Behavior |
|---|---|---|
| **`>= 1440px` (Desktop XL)** | Large monitors | Max content width 1440px centered; full mega-menu dropdowns; 3-column analysis grid. |
| **`1280px - 1439px` (Desktop L)** | Standard laptops (MacBook Pro 14", 16") | Full mega-menus; 2-column or 3-column layouts with fluid gutters. |
| **`1024px - 1279px` (Tablet Landscape)** | iPad Pro landscape, smaller laptops | Compact top navigation; mega-menus adapt to 2-column grids; tables scroll horizontally. |
| **`768px - 1023px` (Tablet Portrait)** | iPad portrait, tablets | Top-sheet mobile menu triggers; horizontal sub-tabs collapse to scrollable ribbon. |
| **`< 768px` (Mobile)** | iPhone, Android smartphones | Full-screen top-sheet menu; single-column stacked cards; touch targets $\ge 44 \times 44\text{px}$. |
