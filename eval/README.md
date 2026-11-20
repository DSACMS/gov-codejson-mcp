# Discovery evaluation

## Purpose

Evaluate the four inventory discovery tools through a local, in-process
MCP client connected to the final Databricks inventory:

- `govcode_catalog_info`
- `govcode_search_projects`
- `govcode_get_project`
- `govcode_compare_projects`

The functional workflow checks tool discovery, response consistency,
comparison ordering, missing records, and invalid input handling.

This runner does not invoke an LLM or verify the deployed App endpoint.
Manual model-connected evaluation is documented separately in
[manual-agent-evaluation.md](manual-agent-evaluation.md).

## Current dataset and identity

The runner targets:

`users.natalia_luzuriaga1.gov_code_complete`

It uses the `complete` inventory layout, mapping the source `govcode_id`
column to the public `entry_id` response field.

The team confirmed that `govcode_id` values persist across future refreshes.
A direct SQL check found 9,430 populated, distinct IDs, with no blank IDs
or surrounding whitespace in the checked table.

The final functional run observed:

- 9,430 inventory entries
- 11 represented agencies
- 67 agency and organization groups

These counts describe the evaluated table, not comprehensive federal
software coverage or independently verified distinct repositories.

Stable entry IDs do not establish an immutable dataset snapshot.
No snapshot identifier was captured for this evaluation.

## Run

From the repository root, with dependencies installed and local Databricks
OAuth access available:

```bash
uv run --no-sync python eval/local_discovery.py
```

The runner loads the root `.env` and selects local-user authentication
for its process. It explicitly enables all four inventory discovery tools
on a temporary MCP server and selects the final table and `complete` layout.

It does not modify `.env` or the deployed App configuration.

Run with ordinary Python settings. The evaluation uses assertions and
must not be run with assertion checks disabled.

## Functional cases

| Case | Verification |
|---|---|
| Tool discovery | All four required inventory tools are advertised |
| Catalog response | A populated inventory returns validated groups whose counts sum to the reported total |
| Search to detail | VA search preserves filters and page limits; lookup returns the same modeled fields as the selected search result, without contact keys |
| Search to comparison | Comparison returns the same modeled records as search, preserves requested order, reports the intentionally missing ID separately, and omits contact keys |
| No-match search | An intentionally unmatched phrase returns zero entries, an empty page, and no further results |
| Unknown project | A missing entry ID returns the controlled not-found error without a substitute |
| Invalid pagination | A limit of 101 returns an MCP error |

The catalog check verifies internal response consistency. It does not
independently validate every source record.

The search, lookup, and comparison checks verify agreement between tools,
not the factual accuracy or freshness of the underlying metadata.

Automated tests separately cover adapters, license parsing, parameter
binding, pagination boundaries, configuration, registration, and controlled
failures.

### Additional final-table check

A separate live MCP lookup retrieved `2026-DOD-18`, STIG Manager, and
verified that its MIT and GPL-3.0-only license names retained their
corresponding supplied URLs.

This was a console-based check, separate from the seven-case saved report.
It does not establish the applicable legal terms or permission for a
particular reuse.

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
treated as not executed.

Reports retain exception types rather than raw exception messages.
Console output and tracebacks are separate and should be reviewed before
sharing.

## Final inventory functional results

All seven cases passed on November 19, 2026, Mountain Time
(November 20 UTC).

Report:
[Final inventory functional run](results/20261120T001022398682Z-discovery.json)

Code revision: `a387e69b6861cda3a79d687b4a4afe526e36a244`

The tracked worktree was clean when the run started.

| Case | Outcome | Observed seconds |
|---|---|---:|
| Tool discovery | PASS | 0.006 |
| Catalog response | PASS | 13.589 |
| Search to detail | PASS | 23.863 |
| Search to comparison | PASS | 18.792 |
| No-match search | PASS | 7.387 |
| Unknown project | PASS | 6.980 |
| Invalid pagination | PASS | 0.005 |
| Overall run | PASS | 70.749 |

The catalog reported 9,430 entries across 11 agencies and 67 agency and
organization groups.

The VA search for “data” reported 10 matches. Its first page returned
`2026-VA-1` and `2026-VA-13`. Lookup and comparison agreed with the
selected search records. Comparison preserved the reversed requested
order and reported the intentionally missing ID separately.

These timings are single observations, not averages, percentiles,
response-time guarantees, or a controlled performance benchmark.
Warehouse-backed timings include connection and query work. Some cases
include multiple tool calls, and overall time includes setup and teardown.

No LLM or deployed App endpoint participated in this functional run.

## Manual chat verification

A separate guided ChatGPT Desktop conversation exercised the final
inventory through local STDIO with local-user authentication.

Observed answers matched the checked search, comparison, pagination,
and missing-entry results. The comparison answer distinguished inventory
metadata from established security, active maintenance, or reuse permission.

### Agency-count error and recovery

The initial catalog answer correctly reported 9,430 entries but incorrectly
counted 12 represented agencies. When asked to enumerate the distinct agency
values, the model listed 11 and corrected its answer.

A direct SQL grouping and the saved functional report also reported
11 agencies. The initial answer failed the agency-count check.
The follow-up demonstrated recovery after prompting.

Correct tool output did not guarantee correct model interpretation.

This was one guided conversation with shared context, not independent
trials or a general accuracy benchmark. Complete tool traces and exact
per-call arguments were not retained in the manual evaluation record.

See [manual-agent-evaluation.md](manual-agent-evaluation.md) for the
session observations and evidence limitations.

## Security considerations

The discovery tools use read-only queries with bound values and quoted
table identifiers. Pagination and comparison inputs have bounds.
Approved project responses omit contact fields.

Local-user verification does not establish deployed App service-principal
permissions. Credentials must remain outside committed files and shared
evaluation artifacts.

### Databricks scanner findings

Reviewed three `hardcoded-secret-assignment` warnings for
`SECRET_SCOPE`, `SECRET_KEY_CLIENT_ID`, and `SECRET_KEY_CLIENT_SECRET`
in `eval/databricks/agent_eval_offline.py`.

The flagged strings are a secret scope name and lookup key names,
not credentials. Actual credentials are retrieved at runtime through
Databricks secrets or environment variables.

These specific assignments were assessed as false positives.
The findings have not yet been dismissed in Databricks.
This review does not constitute a repository-wide security audit.

## Historical functional runs

Earlier reports remain as evidence of the code and datasets evaluated
at those times. They do not describe the current runner's target.

| Dataset | Saved report | Cases passed | Overall seconds |
|---|---|---:|---:|
| Development mock inventory | [November 17 run](results/20261117T203540895756Z-discovery.json) | 6 | 44.417 |
| Earlier legacy inventory | [November 19 run](results/20261119T164435384869Z-discovery.json) | 7 | 58.535 |

The mock run used revision
`7138e619ab26ad9ef0274d90b72097804f19d8c3`.

The legacy run used revision
`f7ceb4d963aee9378b8e951f889ae5ae6231da1b` and reported 8,044 entries.

The runs differ in code, data, and executed cases. Their elapsed times
do not establish a performance trend.

## Security considerations

### Databricks scanner findings

Reviewed three `hardcoded-secret-assignment` warnings for
`SECRET_SCOPE`, `SECRET_KEY_CLIENT_ID`, and `SECRET_KEY_CLIENT_SECRET`
in `eval/databricks/agent_eval_offline.py`.

The flagged strings are a secret scope name and lookup key names,
not credentials. Actual credentials are retrieved at runtime through
Databricks secrets or environment variables.

These specific assignments were assessed as false positives.
The findings have not yet been dismissed in Databricks.
This review does not constitute a repository-wide security audit.

## Limitations and follow-up

- No immutable dataset snapshot was captured. Records may change between runs.
- Search counts and pages use separate queries. Concurrent updates can affect
  consistency and pagination.
- Comparison reads entries separately and does not guarantee a shared snapshot.
- Functional consistency does not establish source metadata accuracy,
  repository accessibility, software security, maintenance, or reuse rights.
- Manual evaluation remains limited to guided questions and a narrow
  selection of records.
- Repeat model evaluation with complete tool traces, confirmed client/model
  settings, and the exact loaded server revision.
- Add unfamiliar cross-agency questions and adversarial metadata tests.
- Deployed App endpoint access remains unverified following the observed
  unauthorized PrivateLink access error.
- App service-principal access to the final inventory remains unverified.
- Repeated trials, a no-tool baseline, load testing, and instrumented
  end-to-end latency and cost measurements have not been completed.

The Databricks agent-evaluation scaffolding remains under `eval/databricks/`.
It requires separate configuration and generated agent files. It has not
produced the results reported here.
