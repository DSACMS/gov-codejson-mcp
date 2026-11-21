# Federal Source Code Inventory MCP Server

Discover federal software inventory entries through a Model Context Protocol (MCP) server backed by Databricks. Created to support discovery and potential reuse of federal source code.

The server helps an AI client search inventory metadata, retrieve individual entries, compare selected entries, and describe the configured inventory’s coverage. It returns structured evidence for further investigation rather than recommendations that software is ready or authorized for reuse.

Built with [FastMCP](https://github.com/jlowin/fastmcp) and [uv](https://docs.astral.sh/uv/), using the GSA MCP hackathon server template.

## Inventory discovery tools

Each tool is enabled independently through configuration.

| Tool | Purpose |
|---|---|
| `govcode_catalog_info` | Report inventory entry counts grouped by agency and organization |
| `govcode_search_projects` | Search names and descriptions, filter by agency or organization, and return a page with the total matching count |
| `govcode_get_project` | Retrieve one inventory entry by `entry_id` |
| `govcode_compare_projects` | Retrieve evidence for two to five distinct entry IDs, preserve requested order, and report missing IDs separately |

Search uses case-insensitive literal substring matching in names and descriptions. Agency and organization filters use exact values.
Search is not semantic ranking.

Search defaults to 10 results per page, supports up to 100, and uses an offset for pagination. Results are ordered by name, then entry ID.

### Example workflow

In an MCP-capable client connected to this server, ask:

1. “Which agencies are represented in this inventory?”
2. “Find two VA entries whose name or description contains data.
   Include names, entry IDs, repository links, and the total matching count.”
3. “Compare those entries using their inventory records.
   Identify missing information and what I should investigate before reuse.”
4. “Show the next two matches using the same filters.”

Custom MCP availability depends on the client and organization settings.
Local interactive verification has used MCP Inspector and ChatGPT Desktop.

## Data and interpretation

The configured inventory is stored in `users.natalia_luzuriaga1.gov_code_complete`.

The latest recorded functional verification, completed November 20, 2026, observed 9,399 inventory entries across 11 agencies and 67 agency and organization groups in `users.natalia_luzuriaga1.gov_code_complete`.

All seven functional checks passed using local-user warehouse authentication and the upgraded dependencies. These counts describe the evaluated inventory, not comprehensive federal source code coverage.

The server maps the source `govcode_id` column to the public `entry_id` field. The team confirmed that these IDs persist across dataset refreshes.

The server supports three explicit dataset formats:

- `complete`: the current inventory in `gov_code_complete`. Maps stable
  source `govcode_id` values to the public `entry_id` field and supports
  pipe-separated lists, license names and URLs, versions, and metadata dates.
- `legacy`: the earlier flattened inventory, using a source `entry_id`
  column, pipe-separated lists, and timestamp columns. Retained for
  compatibility and historical evaluation.
- `mock`: the original development-table layout, using a source `id`
  column and semicolon-separated lists. Retained for development and tests.

Use `GOVCODE_PROJECT_DATASET_FORMAT=complete` with the current inventory.

### Dataset and publication

This server reads the finalized inventory in `users.natalia_luzuriaga1.gov_code_complete`. The related [govcode-index project](https://github.com/GSA-SHARE-IT/govcode-index) documents the collection and preparation of federal agency `code.json` inventory data and assigns persistent `govcode_id` values. This server exposes each source ID as `entry_id`. See the govcode-index README for details about the dataset’s sources and preparation.

Publication on Data.gov is pending.

**Data.gov listing:** [Add listing URL after publication]

### Entry identity

Use `entry_id` values returned by the server for lookup and comparison. Source identifiers and repository URLs can be shared by different inventory entries and are not reliable unique lookup keys.

The source `govcode_id` uniquely identifies an inventory entry. The team confirmed that the final IDs persist across future dataset refreshes. The server exposes them through the public `entry_id` field. Duplicate matches produce a controlled lookup error rather than selecting an arbitrary record.

The completed dataset refresh introduced the final, zero-padded IDs.
Use IDs exactly as returned by the tools, including leading zeros.

Examples include `2026-VA-000001` and `2026-VA-000011`.
Earlier evaluation reports retain the identifiers observed before finalization.

### What the inventory does not establish

- A repository link does not establish current accessibility, completeness, security, maintenance, or suitability.
- A usage classification such as `governmentWideReuse` does not establish specific reuse rights.
- A null license means the inventory did not supply license information; it does not prove that no license exists.
- Listed “languages” can include operating systems, databases, and platforms.
- Software modification dates are not dataset refresh dates.
- Entries sharing a repository remain separate inventory records.

Unavailable fields remain null. Project responses omit contact fields. Dataset version and refresh metadata were unavailable in the observed catalog responses.

## Local setup

### Prerequisites

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- Access to the Databricks workspace, SQL warehouse, catalog, schema, and configured table
- An MCP client that supports launching a local STDIO server

### Install

From the repository root:

```bash
cp .env.example .env
uv sync --group dev
```

If `.env` already exists, edit it rather than overwriting it.

### Configure

The checked-in `.env.example` contains transport and inventory settings.
Add the Databricks connection variables shown below to your local `.env`.
Replace placeholders with your workspace hostname and warehouse HTTP path.

Set the local warehouse connection and inventory settings in `.env`:

```dotenv
MCP_TRANSPORT=stdio

DATABRICKS_READER_AUTH_MODE=local
DATABRICKS_SERVER_HOSTNAME=<workspace-hostname-without-https>
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/<warehouse-id>

GOVCODE_PROJECT_DATASET_FORMAT=complete
GOVCODE_PROJECT_CATALOG=users
GOVCODE_PROJECT_SCHEMA=natalia_luzuriaga1
GOVCODE_PROJECT_TABLE=gov_code_complete

GOVCODE_PROJECT_LOOKUP_ENABLED=true
GOVCODE_PROJECT_SEARCH_ENABLED=true
GOVCODE_CATALOG_INFO_ENABLED=true
GOVCODE_PROJECT_COMPARE_ENABLED=true
```

Local mode uses Databricks OAuth. Complete authentication when prompted and ensure your user has access to the warehouse and table.

All four inventory feature flags default to false. A complete catalog, schema, and table configuration is required when any inventory tool is enabled.

Keep credentials out of committed files, screenshots, and shared logs.
Local-user access does not establish that the deployed App’s service principal has equivalent permissions.

### Start the server

```bash
uv run --no-sync example-server
```

The Python package remains `example_server`, and the console command remains
`example-server`.

STDIO mode communicates through standard input and output. Starting it in a terminal does not open a chat interface or website; an MCP client normally launches the process.

### Connect a local client

Configure a custom STDIO MCP connection with:

- Command: the absolute path returned by `command -v uv`
- Arguments: `run`, `--no-sync`, `example-server`
- Working directory: the absolute path to this repository

If the client provides one field per argument, enter each argument separately.
Restart or reconnect the server after changing configuration or code.

## Verification and evaluation

Run the automated checks:

```bash
uv run --no-sync pytest tests/ -q
uv run --no-sync ruff check .
git --no-pager diff --check
```

The latest reported development suite passed 153 tests.

Run the live functional workflow:

```bash
uv run --no-sync python eval/local_discovery.py
```

This runner requires live warehouse access and writes timestamped reports under `eval/results/`. Inspect the runner and saved report for the dataset, cases, code revision, and execution mode used.

Evaluation evidence includes:

- Automated tests for record adaptation, filters, pagination, configuration,
  registration, and controlled failures
- Scripted local MCP checks against a live warehouse
- Interactive MCP Inspector checks
- A guided manual chat evaluation using the actual inventory

Functional assertions, manual model evaluation, and deployed App verification are separate forms of evidence. Passing one does not establish the others.

See [eval/README.md](eval/README.md) for methodology, recorded results, security review notes, and limitations.

## Deployment status

Local MCP workflows have been verified with local-user warehouse authentication.

A Databricks App deployment built and started, but external access returned an unauthorized PrivateLink access error. End-to-end deployed App operation and service-principal access to the actual inventory remain unverified.

Deploy reviewed changes from `main`. Confirm the deployed revision, inventory layout, tool flags, and service-principal permissions before using the App for a demonstration.

The repository retains deployment guides inherited from the template:

- [Deployment overview](deploy/README.md)
- [Databricks Apps](deploy/databricks/)
- [IBM watsonx Orchestrate](deploy/ibm/)

The IBM deployment paths have not been verified for this project.

## Repository structure

```text
gov-codejson-mcp/
├── README.md
├── QUICKSTART.md                   # Original template walkthrough
├── pyproject.toml                  # Package, dependencies, and console command
├── .env.example                    # Local configuration reference
├── app.yaml                        # Databricks App configuration
├── src/
│   └── example_server/
│       ├── app.py                  # Server identity, instructions, and transport
│       ├── config.py               # Environment-based settings
│       ├── models.py               # Tool input and response models
│       ├── errors.py               # Inventory error types
│       ├── warehouse.py            # Shared Databricks connection setup
│       ├── inventory_layout.py     # Source columns and record adapters
│       ├── project_reader.py       # Shared record preparation
│       ├── legacy_project_adapter.py
│       ├── complete_project_adapter.py  # Final inventory field and license mapping
│       ├── warehouse_project_reader.py
│       ├── project_search.py       # Filters, counts, and result pages
│       ├── project_comparison.py   # Ordered comparison evidence
│       ├── catalog_reader.py       # Inventory coverage counts
│       ├── routes.py               # HTTP infrastructure routes
│       ├── tools/
│       │   ├── __init__.py         # Registration controlled by feature flags
│       │   ├── catalog_tool.py
│       │   ├── search_tool.py
│       │   ├── project_tool.py
│       │   └── compare_tool.py
│       ├── prompts/               # Prompt registration hook
│       └── resources/             # Resource registration hook
├── tests/                         # Automated tests
├── eval/
│   ├── README.md                  # Methodology, results, and limitations
│   ├── local_discovery.py         # Live functional workflow
│   ├── results/                   # Saved evaluation reports
│   └── databricks/                # Agent-evaluation scaffolding
├── deploy/                        # Inherited deployment guides and scripts
└── docs/                          # Partner reference materials
```

Selected files are shown; this is not an exhaustive directory listing.
The Python package and console command retain their original names, `example_server` and `example-server`.

## Known limitations and follow-up

- Record dataset versions or immutable snapshots for repeatable evaluation.
- Separate count and page queries can observe concurrent inventory changes.
- Comparison reads entries separately and does not guarantee a shared snapshot.
- Broaden manual evaluation with independent sessions and more varied use cases; current evidence covers two guided conversations and a narrow set of examples.
- Resolve deployed App access and verify its warehouse permissions.
- Filter-aware facets and inventory summaries beyond catalog counts remain unimplemented.

## Partner reference materials

The [`docs/`](docs/) directory contains educational reference materials that IBM and Databricks may contribute for hackathon participants. Vendor-contributed materials do not represent the views, positions, or policies of GSA or the United States Government.

GSA does not endorse any commercial product, service, or enterprise referenced in these materials. Reference to a commercial product, service, or enterprise does not constitute or imply endorsement, recommendation, or favoring by GSA or
the United States Government. These materials are provided for educational purposes only. See [`docs/README.md`](docs/README.md) for the complete notice and contribution guidance.

## License

[MIT](LICENSE) applies to this repository’s code. It does not establish licensing or reuse rights for software described in the inventory.

See [SECURITY.md](SECURITY.md) for vulnerability disclosure guidance and hackathon security notes.
