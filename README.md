# CI Fabric Release Gate

This public repository stores **hash-only privileged authorization records**
for private CI Fabric source repositories.

It intentionally contains no private source code, repository names, private
commit SHAs, IP addresses, hostnames, runner IDs, service paths, URLs,
secret names, tokens, or credentials.

Each `authorizations/<candidate-digest>.json` record is immutable and must be
introduced as the only file in a protected pull request.

The authoritative private-side verifier additionally requires:

- exact-head approval from `control-center-release-gate[bot]`;
- merge by `controlcenter-release-reviewer`.

Direct pushes, owner merges, stale approvals, modified authorization files
and multi-file authorization PRs are not accepted by trusted-root admission.
