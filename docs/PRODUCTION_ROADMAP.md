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

- [x] Docker build, compose startup, health/readiness, read-only mounted artifacts, snapshot provenance, prediction smoke, restart persistence, Nginx smoke, log review, and shutdown verification.

## External deployment work

- [x] Server availability confirmed by the user.
- [ ] Confirm server access, architecture, OS, CPU/RAM/disk, firewall, and Docker/Compose.
- [ ] Configure DNS/domain.
- [ ] Configure HTTPS certificate and HTTPS CORS origin.
- [ ] Deploy only the checksum-verified runtime artifacts outside Git.
- [ ] Run the operator procedure in `docs/DEPLOYMENT_RUNBOOK.md` and complete public smoke.

## Release boundary

Local production readiness and final documentation are complete. The next branch is `deploy/server-production`; do not create it automatically. This remains a research/educational prototype and is not clinical software.
