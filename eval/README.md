# Discovery evaluation

## Purpose

Evaluate the catalog → search → project-details workflow through a local,
in-process MCP client using the live Databricks mock inventory.

This is a functional integration evaluation. It does not measure an LLM's
tool selection or answer quality, or verify the deployed App endpoint.

## Run

From the repository root, with dependencies installed and local Databricks
OAuth access available:

```bash
uv run --no-sync python eval/local_discovery.py
```

The runner loads the root `.env` and selects local-user authentication for
its process. It explicitly enables catalog, search, and lookup on a temporary
MCP server. It does not modify `.env` or the deployed App configuration.

The current evaluation targets:

`users.natalia_luzuriaga1.mock_dataset`

Run with ordinary Python settings; the evaluation uses assertions and must
not be run with assertion checks disabled.

## Cases

| Case | Verification |
|---|---|
| Tool discovery | All three discovery tools are advertised |
| Catalog response | A populated inventory returns validated groups whose counts sum to the reported total |
| Search to detail | VA search preserves filters and page limits; a returned ID retrieves consistent project fields without contact keys |
| No-match search | An intentionally unmatched phrase returns zero entries and no further page |
| Unknown project | A missing entry ID returns the controlled not-found error |
| Invalid pagination | A limit of 101 returns an MCP error |

The catalog count check verifies internal response consistency. It is not an
independent comparison with a separately curated inventory.

The search-to-detail case checks consistency between tools, not the factual
accuracy of the underlying source metadata.

Automated tests separately cover additional behavior, including parameter
binding, pagination boundaries, configuration, and controlled failures.

## Reports

Each run writes a timestamped JSON file to `eval/results/`, containing:

- UTC start and finish times
- Git commit and tracked-worktree modification status
- Execution mode, authentication mode, and target dataset
- Overall and individual case outcomes
- Observed elapsed times
- Explicit LLM and deployed-App evaluation flags

The runner stops at the first failed check or execution error and exits
unsuccessfully. Cases not reached are absent from the report and must be
treated as not executed.

Reports retain exception types rather than raw exception messages.
Console output and tracebacks are separate and should be reviewed before sharing.

## Recorded run

Report: `results/20261117T203540895756Z-discovery.json`

Code revision: `7138e619ab26ad9ef0274d90b72097804f19d8c3`

Captured November 17, 2026, with no tracked worktree modifications.
All six cases passed.

| Case | Observed seconds |
|---|---:|
| Tool discovery | 0.006 |
| Catalog response | 11.651 |
| Search to detail | 21.764 |
| No-match search | 5.461 |
| Unknown project | 5.392 |
| Invalid pagination | 0.003 |
| Overall run | 44.417 |

These are single observations, not averages, percentiles, or service-level
guarantees. Warehouse-backed timings include connection and query work;
search-to-detail includes multiple tool calls. Overall time also includes
setup and teardown.

## Limitations and follow-up

- No immutable dataset snapshot was captured. Results may change as the
  mock table is updated.
- Search counts and result pages use separate queries. Concurrent inventory
  updates can affect consistency and pagination.
- Coverage is limited to the configured inventory; it is not government-wide.
- Earlier live inspection found two entries without agency values and an
  organization value containing descriptive prose. Source quality needs review.
- The deployed App built and started, but external endpoint verification
  remains blocked by a PrivateLink access error.
- App service-principal warehouse access remains unverified.
- No LLM agent, judge, or model endpoint participated in this evaluation.

The Databricks agent-evaluation scaffolding remains under `eval/databricks/`.
It requires separate configuration and generated agent files. Its results
must be reported separately from this functional evaluation.