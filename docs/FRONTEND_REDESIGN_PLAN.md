# Frontend Redesign Plan

## Scope

This phase refreshes the static HTML, CSS, and vanilla JavaScript interface only. FastAPI routes, frozen ML/DL artifacts, thresholds, research metrics, and all permission behavior remain unchanged.

## Current Structure

| Area | Current implementation | Preserve |
| --- | --- | --- |
| Public pages | Home, education, care, videos, and about pages | Existing educational copy and assets |
| Analysis | One prediction page with ML, DL, and multimodal tabs | API payloads, demo samples, result/history persistence |
| Research | Statistics page with evidence panel | Separate WDBC and CBIS-DDSM evidence |
| Workspace | Patients, history, HTML reports, profile | Authentication and doctor permission behavior |
| Assistant | Chat panel plus floating action | Local/remote advisor contract and saved history |
| Runtime | Model list/status fetched from final API endpoints | Research-only language and final artifact status |

## UX Findings

- The horizontal top navigation duplicates its mobile drawer and does not scale to the number of authenticated workspace routes.
- The home page mixes educational content, demo flows, and research evidence before users understand the research-only scope.
- The 30-feature ML form is long and visually flat; its three statistical feature families are not clearly grouped.
- Prediction results provide useful fields but do not visually distinguish raw decision probability from DL calibrated display probability.
- Research content is valuable but needs a stronger study boundary: WDBC ML and CBIS-DDSM DL must never read as one leaderboard.
- Styles contain more than one token layer, repeated media rules, inline layout styles, and inconsistent radii/shadows.
- `app.js` combines constants, state, data loading, renderers, and event bindings in one file. It will retain its stable endpoint/state contract in this phase, while renderer helpers are made more component-like.
- Desktop data lists need denser scan patterns; mobile needs tables/forms/sidebar to fold into vertical task-oriented surfaces.

## Information Architecture

### Public entry

- Research platform landing page: study scope, final evidence, reliability, architecture, safety.
- Optional education and care routes remain available as supporting information.

### Application shell

- Overview dashboard.
- AI Analysis: Structured ML, Mammography DL, Experimental Multimodal.
- Research: dashboard, performance, explainability/calibration evidence.
- Clinical Workspace: patients, prediction history, reports.
- System: final model status and account settings.

Unauthenticated users retain access to demo analysis; authenticated capabilities are revealed without changing backend authorization.

## Design System Plan

- Establish semantic color, surface, text, border, radius, shadow, spacing, and type-scale tokens in one canonical `:root` block.
- Use a navy/white/emerald palette with restrained teal gradients and color-independent labels/icons for status.
- Standardize buttons, inputs, panels, KPI cards, badges, alerts, tabs, drawers, tables, empty states, and result probability bars.
- Use CSS-only responsive components and inline SVG/lucide-compatible visual symbols; do not add a framework or build step.
- Honor `prefers-reduced-motion`, visible `:focus-visible`, meaningful labels, and accessible announcement surfaces.

## Implementation Sequence

1. Add this plan and preserve a clean branch baseline.
2. Replace the app shell/navigation and canonical design tokens while preserving `data-page` routes and JavaScript ids.
3. Redesign landing, overview dashboard, and research evidence with separated modality panels.
4. Upgrade ML/DL/multimodal analysis controls and reusable raw-threshold probability visuals.
5. Improve patients, history, report access, auth, chat, model status, empty/loading/error surfaces.
6. Tighten responsive behavior at 1440, 1024, 768, and 390 pixels; perform browser/static-Nginx QA.
7. Run JavaScript, backend regression, final application, and production-readiness checks; document evidence and push CI.

## Acceptance Boundaries

- No fabricated medical normal ranges, clinical approval, or cross-dataset model ranking.
- ML decisions remain raw `>= 0.36`; DL decisions remain raw `>= 0.515`; Platt remains display/reliability only.
- “Research / Educational Prototype - Not for clinical diagnosis” remains visible at entry and result surfaces.
- No model weight, database, secret, or raw dataset is introduced into Git.
