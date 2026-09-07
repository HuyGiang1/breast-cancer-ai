# Deployment

The canonical production handoff is [DEPLOYMENT_RUNBOOK.md](DEPLOYMENT_RUNBOOK.md).

The user has a server, but production deployment has not yet been executed. Access/configuration details are pending; domain, DNS, HTTPS, and external production smoke remain pending unless configured during the next phase. No server address or credential is stored in this repository.

Local Docker, model checksum, read-only mount, Nginx, persistence, backup/restore, and readiness gates have passed. The next branch is `deploy/server-production`; do not begin deployment without the operator-provided access and target configuration.
