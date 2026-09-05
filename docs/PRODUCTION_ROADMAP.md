# Production Roadmap

## Completed local gates

- [x] Final ML/DL runtime artifacts are checksum-verified and fail closed.
- [x] Packaged research snapshot is byte-checked against the frozen source.
- [x] CI production-readiness validation is green for `8fce90d` (`33945903158`).
- [x] SQLite backup plus safe temporary restore rehearsal.
- [x] Final local system benchmark.
- [x] Production-readiness validator.
- [x] Operational safety review.
- [x] Deployment runbook and Nginx review.

## Required before release preparation

- [ ] Docker build, compose startup, health/readiness, mounted artifacts, snapshot, prediction smoke, restart persistence, and shutdown verification.
  Blocked: Docker daemon is unavailable locally.

## External deployment work

- [ ] Provision VPS.
- [ ] Configure DNS/domain.
- [ ] Configure HTTPS certificate and HTTPS CORS origin.
- [ ] Deploy only the checksum-verified runtime artifacts outside Git.
- [ ] Run the operator procedure in `docs/DEPLOYMENT.md`.

## Release boundary

Begin `docs/final-documentation` only after the two release-preparation gates above are completed. This remains a research/educational prototype and is not clinical software.
