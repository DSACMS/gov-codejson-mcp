# Discovery evaluation

## Purpose

This document records the functional integration checks for the four inventory
discovery tools:

- `govcode_catalog_info`
- `govcode_search_projects`
- `govcode_get_project`
- `govcode_compare_projects`

The saved functional runner connects a local, in-process MCP client to the
configured Databricks inventory. It checks tool discovery, response consistency,
comparison ordering, missing records, and invalid input handling.

The functional runner does not invoke an LLM or verify the deployed App
endpoint. The separate guided manual-client evaluation is documented in
[manual-agent-evaluation.md](manual-agent-evaluation.md).

## Current dataset and identity

The runner targets
`users.natalia_luzuriaga1.gov_code_complete` using the `complete` layout.
It maps the source `govcode_id` column to the public `entry_id` field.

The team confirmed that `govcode_id` values persist across future refreshes.
A direct SQL check of the final table found 9,399 populated, distinct IDs,
with no missing IDs or surrounding whitespace.

The final recorded functional run observed:

- 9,399 inventory entries
- 11 represented agencies: DHS, DOD, DOE, EPA, FEC, GSA, HHS, NSF, SSA,
  USDA, and VA
- 67 agency and organization groups

These counts describe the evaluated table. They do not establish comprehensive
federal source-code coverage or the number of distinct repositories. No
immutable dataset snapshot identifier was captured.

The final refresh introduced the zero-padded IDs used in current responses.
Use IDs exactly as returned by the tools. Earlier reports and conversations
may contain pre-refresh IDs.

## Run

From the repository root, with dependencies installed and local Databricks
OAuth access available:

```bash
uv run --no-sync python eval/local_discovery.py
```

The runner loads the root `.env`, selects local-user authentication for its
process, and explicitly enables all four discovery tools on a temporary MCP
server. It selects the final table and `complete` layout. It does not modify
`.env` or the deployed App configuration.

Run with ordinary Python settings. The evaluation uses assertions and must
not be run with assertion checks disabled.

## Functional cases

| Case | Verification |
|---|---|
| Tool discovery | All four inventory tools are advertised |
| Catalog response | A populated inventory returns validated groups whose counts sum to the reported total |
| Search to detail | VA search preserves filters and page limits; lookup returns consistent modeled fields without contact keys |
| Search to comparison | Comparison returns consistent modeled records, preserves requested order, reports the intentionally missing ID, and omits contact keys |
| No-match search | An unmatched phrase returns zero entries, an empty page, and no further results |
| Unknown project | A missing entry ID returns the controlled not-found error without a substitute |
| Invalid pagination | A limit of 101 returns an MCP error |

The catalog check verifies internal response consistency; it does not
independently validate every source record. Search, lookup, and comparison
check agreement between tools, not the factual accuracy or freshness of source
metadata. Automated tests separately cover adapters, license parsing,
parameter binding, pagination boundaries, configuration, registration, and
controlled failures.

## Latest functional run

All seven cases passed on November 20, 2026, against the completed refresh of
`users.natalia_luzuriaga1.gov_code_complete`, using local-user authentication
and the upgraded dependencies.

Report: [Final refresh verification](results/20261120T182632549755Z-discovery.json)

Code revision: `2bd79c4eea63039a9e7e0a9b8082571180c8e45d`. The tracked
worktree was clean when the run started.

| Case | Outcome | Observed seconds |
|---|---:|---:|
| Tool discovery | PASS | 0.006 |
| Catalog response | PASS | 13.127 |
| Search to detail | PASS | 26.305 |
| Search to comparison | PASS | 33.092 |
| No-match search | PASS | 7.233 |
| Unknown project | PASS | 5.916 |
| Invalid pagination | PASS | 0.004 |
| Overall run | PASS | 85.820 |

The catalog reported 9,399 entries, 11 agencies, and 67 agency and
organization groups. The VA search for “data” returned 10 matches; its first
page returned `2026-VA-000001` and `2026-VA-000011`. Lookup and comparison
agreed with the selected search records. Comparison preserved requested order
and reported the intentionally missing ID separately.

These are single observed timings, not averages, percentiles, response-time
guarantees, or a controlled performance benchmark. Warehouse-backed timings
include connection and query work; some cases include multiple tool calls.
Overall time includes setup and teardown.

No LLM or deployed App endpoint participated in this functional run. No
immutable dataset snapshot was captured.

## Latest manual-client check

A separate guided ChatGPT Desktop conversation checked the final inventory
through local STDIO with local-user OAuth. The client used GPT-6 Luna / Medium.
The check is recorded in [manual-agent-evaluation.md](manual-agent-evaluation.md).

The fresh catalog response reported 9,399 entries and 11 represented agencies.
The VA “data” search returned 10 matches. The first page included
`2026-VA-000001` and `2026-VA-000011`; the next page included
`2026-VA-000123` and `2026-VA-000147`, with more results remaining.
Comparison returned the requested entries in order with no missing IDs.
A deliberately missing ID returned the not-found response without a substitute.

Screenshots were captured. This was one guided conversation with shared
context, not independent trials or a general accuracy estimate. Complete tool
traces and exact per-call arguments were not retained. The App was running,
but an authenticated request to its MCP endpoint returned HTTP 403 with a
PrivateLink access error before MCP initialization; deployed endpoint behavior
therefore remains unverified.

### Earlier pre-refresh manual check

An earlier guided conversation used the 9,430-entry pre-refresh inventory.
The model initially reported 12 agencies, then enumerated 11 and corrected
itself after prompting. A direct SQL grouping and the saved functional report
also showed 11 agencies. This records one interpretation error and a prompted
recovery; it is not evidence about the final refreshed inventory or a general
model-accuracy rate.

## Supplementary license lookup

A separate console-based lookup reported that the entry ID
`2026-DOD-18` (STIG Manager) retained the supplied MIT and GPL-3.0-only
license names and URLs. This check was separate from the saved seven-case
report. Its dataset revision and relationship to the final refreshed ID
format were not recorded, so it is not counted as a verified final-table
result. It does not establish the applicable legal terms or permission for
a particular reuse.

## Reports

Each run writes a timestamped JSON file to `eval/results/`, containing:

- UTC start and finish times
- Git commit and tracked-worktree modification status
- Execution mode and warehouse identity
- Target dataset, layout, and source ID column
- Overall and individual case outcomes
- Observed elapsed times
- Observed inventory counts and selected search results, when reached
- Explicit LLM and deployed-App evaluation flags

The runner stops at the first failed check or execution error and exits
unsuccessfully. Cases not reached are absent from the report and must be
treated as not executed. Reports retain exception types rather than raw
exception messages. Console output and tracebacks are separate and should be
reviewed before sharing.

## Historical functional runs

Earlier reports remain as evidence of the code and datasets evaluated at
those times. They do not describe the current runner target.

| Dataset and date | Saved report | Cases passed | Overall seconds |
|---|---|---:|---:|
| Development mock inventory, November 17 | [Mock run](results/20261117T203540895756Z-discovery.json) | 6 | 44.417 |
| Earlier legacy inventory, November 19 | [Legacy run](results/20261119T164435384869Z-discovery.json) | 7 | 58.535 |
| Pre-refresh complete inventory, November 19 Mountain Time / November 20 UTC | [Pre-refresh run](results/20261120T001022398682Z-discovery.json) | 7 | 70.749 |

The mock run used revision
`7138e619ab26ad9ef0274d90b72097804f19d8c3`. The legacy run used revision
`f7ceb4d963aee9378b8e951f889ae5ae6231da1b` and reported 8,044 entries.
The pre-refresh complete-inventory run used revision
`a387e69b6861cda3a79d687b4a4afe526e36a244` and reported 9,430 entries.
It returned the then-current VA IDs `2026-VA-1` and `2026-VA-13`; those IDs
predate the completed refresh.

The runs differ in code, data, and executed cases. Their elapsed times do not
establish a performance trend.

## Security considerations

The discovery tools use read-only queries with bound values and quoted table
identifiers. Pagination and comparison inputs have bounds. Approved project
responses omit contact fields. Local-user verification does not establish
deployed App service-principal permissions. Credentials must remain outside
committed files and shared evaluation artifacts.

### Databricks scanner findings

Three `hardcoded-secret-assignment` warnings were reviewed for
`SECRET_SCOPE`, `SECRET_KEY_CLIENT_ID`, and `SECRET_KEY_CLIENT_SECRET` in
`eval/databricks/agent_eval_offline.py`. The flagged strings are a secret
scope name and lookup key names, not credentials. Actual credentials are
retrieved at runtime through Databricks secrets or environment variables.
These specific assignments were assessed as false positives; the findings
have not been dismissed in Databricks. This review is not a repository-wide
security audit.

## Dependency and container verification

Following the dependency update, 153 automated tests passed. Package
compatibility, Ruff, and whitespace checks passed. The recorded `pip-audit`
result reported no known vulnerabilities in the exported pinned runtime
requirements; this is a point-in-time scan, not a guarantee against future
findings.

Docker was unavailable locally, so the image was not built on the developer’s
machine. The later GitHub Actions Docker build and health-check workflow
passed. This confirms that CI built the container and reached its health
endpoint; it does not verify the deployed App endpoint or its warehouse
permissions.

## Limitations and follow-up

- No immutable dataset snapshot was captured; records may change between runs.
- Search counts and pages use separate queries. Concurrent updates can affect
  consistency and pagination.
- Comparison reads entries separately and does not guarantee a shared snapshot.
- Functional consistency does not establish source metadata accuracy,
  repository accessibility, software security, maintenance, or reuse rights.
- Manual evaluation remains qualitative, based on guided conversations with
  shared context and a narrow selection of records. Broaden it with independent
  sessions and more varied use cases.
- Repeat model evaluation with complete tool traces, confirmed client/model
  settings, and the exact loaded server revision.
- Add unfamiliar cross-agency questions and adversarial metadata tests.
- Deployed App endpoint access remains unverified after the observed
  unauthorized PrivateLink response.
- App service-principal access to the final inventory remains unverified.
- Repeated trials, a no-tool baseline, load testing, and instrumented
  end-to-end latency and cost measurements have not been completed.

The Databricks agent-evaluation scaffolding remains under
`eval/databricks/`. It requires separate configuration and generated agent
files and did not produce the results reported here.
