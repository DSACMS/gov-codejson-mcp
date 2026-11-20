# Manual agent evaluation

## Purpose

Observe whether a model-connected client can use the gov-code MCP tools
to answer inventory questions and carry identifiers and filters across
follow-up requests.

This is a qualitative review of one guided conversation, not a benchmark
or a general accuracy estimate.

## November 18 legacy inventory session

## Test context

- Date: November 18, 2026
- Client: ChatGPT Desktop
- Model and effort: GPT-6 Luna / Medium, recalled by the tester
- Transport: local STDIO
- Warehouse authentication: local-user OAuth
- Dataset: users.natalia_luzuriaga1.legacy_gov_code
- Observed inventory: 8,044 entries across 10 represented agencies
- Immutable dataset snapshot: not captured
- Reported local revision: ecc273b
- Exact revision loaded by the running MCP process: not independently confirmed
- Entry-ID persistence across refreshes: provisional

No deployed Databricks App endpoint was used in these tests.

## Method

A tester entered prompts in sequence and reviewed answers and available
tool activity against previously observed inventory responses.

The catalog prompt explicitly named its tool. Later prompts described
tasks and reused conversation context. Tool-call evidence and answer
correctness were assessed separately.

## Observations

| Case | Observed answer | Tool evidence |
|---|---|---|
| Catalog discovery | Correctly reported 8,044 entries and listed 10 represented agencies | Catalog tool response supplied |
| Filtered search | Returned the expected first two VA entries matching “data,” with IDs and repository links; reported 10 total matches | Exact invocation arguments not retained in this record |
| Comparison follow-up | Preserved order, descriptions, technologies, usage classifications, unknown licenses, and reported modification dates | Comparison-shaped response supplied; complete trace not retained |
| Unsupported assurances | Declined to declare either project definitely secure, actively maintained, or legally cleared for reuse | Additional retrieval was not necessary to answer from existing context |
| Unknown entry ID | Reported the requested ID as not found without substituting another project | Tester supplied the answer; raw lookup error not retained |
| Pagination follow-up | Returned two different VA entries, preserved the total of 10, and reported more results remaining | Offset 2 recalled by tester; exact invocation not retained |

The observed answers matched the case expectations. Evidence is insufficient
to independently confirm every tool invocation and argument.

## Example records

First search page:

- BAE40FCB6 — Administrative Data Repository
- A89020919 — Clinical Data Repository/Health Data Repository

Next search page:

- AFE1F599F — Collaborative Terminology Tooling Data Management
- C3EE78C96 — Community Care - Electronic Data Interchange Gateway

The first two records reported governmentWideReuse and null licenses.
The model explained that these values do not establish security,
ongoing maintenance, suitability, or specific reuse permission.

## Limitations

- One conversation, one tester, and one reported model/effort configuration.
- Prompts were guided and do not establish broad task success.
- Follow-up answers could reuse previously returned information.
- Complete model traces and exact per-call arguments were not retained here.
- Displayed “Worked for” durations are not instrumented performance metrics.
- The mutable dataset and temporary IDs limit reproducibility.
- Technologies in the source languages field are not exclusively
  programming languages.
- Deployed App access and service-principal warehouse access remain unverified.

## Follow-up

- Repeat from a fresh conversation with exact client/model versions,
  tool arguments, responses, and server revision captured.
- Add unfamiliar queries, cross-agency scenarios, empty results,
  and misleading or incomplete metadata.
- Update the functional runner for the legacy dataset and comparison tool.
- Repeat against the deployed endpoint when access is available.

## Manual chat verification against the final inventory

Dataset: `users.natalia_luzuriaga1.gov_code_complete`
Client: ChatGPT Desktop using local STDIO and local-user authentication.

| Check | Observed outcome |
|---|---|
| Coverage | Correctly reported 9,430 entries. Initially reported 12 agencies; enumerated 11 and corrected the answer after prompting. SQL and the functional report confirmed 11. |
| Search | Reported 10 VA matches for “data,” with the expected first two records, final entry IDs, and repository links. |
| Comparison and evidence limits | Returned both requested entries in order with no missing IDs. Described the checked metadata and did not claim established security, active maintenance, or reuse permission. |
| Pagination | Returned different entries, `2026-VA-15` and `2026-VA-16`, with 10 total matches and more results remaining. |
| Missing entry | Reported `__govcode_missing_entry_839271__` as not found without substituting another project. |

This was one guided conversation with shared context, not independent trials.
The initial agency-count answer failed that check; correction after prompting
was recorded separately. Correct tool output did not guarantee correct model
interpretation.

This session did not verify the deployed App.

The team confirmed that source `govcode_id` values persist across refreshes.
The server exposes these values through the existing `entry_id` response field.

Complete tool traces and exact per-call arguments are not included in this
record. Model/effort settings and the exact loaded server revision were not
confirmed for this session.
