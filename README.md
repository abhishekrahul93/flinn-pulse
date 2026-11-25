# Flinn Pulse

[Open the public browser demo](https://abhishek-revenueops-demo.abhishekrahul642.chatgpt.site/) · [Deploy the full Python app on Render](https://render.com/deploy?repo=https://github.com/abhishekrahul93/flinn-pulse)

**MedTech BI, ARR Truth & AI Automations Hub** — an independent portfolio prototype by Abhishek Rahul. Not affiliated with Flinn. All accounts and records are fictional.

A working Streamlit application using DuckDB, Pandas and Plotly, with modular SQL, tested revenue definitions, product tracking governance, explainable review tasks and constrained SQL Q&A. A portable browser edition in `dist/` demonstrates the same compiled data without Python setup.

## Run locally

Requires Python 3.11+ (tested on Python 3.12).

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit. No API key or external account is needed. Missing CSV files are generated deterministically at startup. The normal app builds a fresh in-memory warehouse per snapshot; a session never shares a mutable DuckDB connection with another user.

## Four tabs

| Tab | What works |
| --- | --- |
| ARR Truth | Finance/CRM reconciliation, account-level exceptions, ARR bridge, tier chart, cohort NRR, CSV export |
| Product Adoption & Event QA | Five governed features, equal 30-day comparisons, tier filter, adoption chart, 12 data checks and actual SQL inspection |
| Automations | Nine review proposals, sourced evidence, stable event IDs, approval state, duplicate-safe delivery simulation, webhook JSON download |
| SQL Copilot | Seven supported natural-language intents, live DuckDB results, visible SQL, optional provider generation and custom validated SELECT queries |

The first three tabs respect the sidebar tier filter. The copilot explicitly queries the whole warehouse. Checks apply to the whole dataset. The as-of date is fixed at **24 November 2026** for a reproducible interview demonstration.

## Data and metrics

- 25 fictional accounts across Enterprise, Mid-Market and Growth; 24 currently have positive recurring ARR.
- 27 raw CRM deal records, including exactly two replayed renewal records; staging keeps one per deal ID.
- 75 Finance account-month snapshots (September-November).
- 2,095 raw product events; one malformed `ClickedExportBtn` record is quarantined.
- Three CRM/Finance ARR discrepancies; one closed-won deal lacks a close date.
- Four high-ARR accounts have a sharp usage decline within 45 days of renewal.
- Mid-Market gap-analysis adoption is 1/8 eligible accounts, or 12.5%.

**Metric contract:** Finance is the chosen demonstration reporting reference; it is not asserted to be inherently correct in every real business. The synthetic invoice field `invoiced_arr_eur` is already an annualised recurring contract equivalent, not an arbitrary invoice total. Amounts are transformed to integer EUR cents. CRM rows are total contract snapshots, not additive expansion deal line items. Pending or overdue payment alone does not remove contracted ARR. One-off fees, taxes, FX, refunds and complex multi-contract billing are outside this prototype.

**ARR bridge:** opening ARR + new business + expansion - contraction - churn = ending ARR. Current Finance reference is EUR 1,963,200 versus EUR 1,926,000 in October. The cohort NRR excludes new accounts; GRR also excludes expansion. CRM totals EUR 1,973,700, a net EUR 10,500 difference; the three absolute discrepancies total EUR 19,500. Source differences remain open and are never auto-corrected.

**Adoption:** an eligible account has positive current ARR; an account adopts a feature after at least three governed events in the current window. Current: 26 October-24 November; previous: 26 September-25 October, both 30 days in UTC. A usage decline is a review signal, not a validated churn prediction.

## Repository

```text
app.py
.streamlit/config.toml
data/generate_data.py
data/generated/*.csv
warehouse/pipeline.py
warehouse/models/stg_hubspot_deals.sql
warehouse/models/stg_invoices.sql
warehouse/models/stg_posthog_events.sql
warehouse/models/mart_arr_truth.sql
warehouse/models/mart_feature_adoption.sql
automations/copilot.py
automations/n8n_review_workflow.json
tests/test_system.py
tests/*.sql
dbt_project.yml
profiles.yml
scripts/build_snapshot.py
dist/                 # portable browser edition and verified query snapshots
requirements.txt
requirements-dev.txt
render.yaml
docs/DEMO_SCRIPT.md
```

SQL uses standard dbt `ref()` dependencies. The Python runner resolves those references against local tables and executes models transactionally. The optional dbt project executes the very same SQL files and CSV seeds.

## Verify

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python -m warehouse.pipeline
python scripts/build_snapshot.py
# Optional genuine dbt run:
pip install -r requirements-dev.txt
dbt build --profiles-dir .
```

Expected: backend regression tests pass, dbt's clean-layer invariant tests pass, and **four diagnostic source/business checks intentionally report FAIL** with row counts 2, 1, 3 and 1. Do not interpret these expected findings as a broken pipeline. They demonstrate how upstream defects remain visible while clean-layer invariants hold.

## Optional OpenAI / Gemini

Set either `GEMINI_API_KEY` or `OPENAI_API_KEY` in your deployment environment, then opt in using the copilot checkbox. Optional model overrides: `GEMINI_MODEL` and `OPENAI_MODEL`; defaults are `gemini-2.5-flash` and `gpt-4.1-mini`. Model availability depends on the provider/account and may change. Never commit keys. On Streamlit Community Cloud, optional keys can be entered as top-level entries in the app secrets configuration. The app reads top-level `st.secrets` keys and environment variables.

Provider mode sends only the question and published schema, not warehouse rows. Provider output is validated and executed through the same boundary. Missing keys, network errors, invalid SQL or provider execution errors fall back to a reviewed template when the question matches one of the seven supported intents. Unsupported questions produce an explicit suggestion instead of an invented result. Live provider calls have not been verified with credentials.

Read-only controls: AST parsing with sqlglot; one SELECT; two allowlisted marts; allowlisted scalar/aggregate functions; no database/catalog qualification or table-valued functions; fresh isolated DuckDB containing only the marts; external access disabled; 100-row response cap; 128 MB query memory limit and a three-second interrupt timer. This is a bounded demonstration, not a multi-tenant production security certification.

## Automations and n8n

Download a webhook payload from an alert. It contains a stable event ID, rule, evidence, owner, `review_required: true`, and Slack Block Kit preview. The example `automations/n8n_review_workflow.json` can be imported into n8n to receive and validate a review-only payload. The workflow is inactive, contains no Slack delivery node and was not tested in a running n8n instance.

Approval and delivery are local simulations: Streamlit uses per-session state; the browser edition uses local storage. A repeated delivery yields `duplicate_skipped`. A production queue would require persistent unique-key enforcement, authenticated approvals, delivery retries/backoff, secrets management and monitoring. No external Slack, CRM or n8n action occurs in this prototype.

## Deploy on Streamlit Community Cloud

1. Put this source tree in a GitHub repository you control. Keep `app.py` and `requirements.txt` at the repository root.
2. Open https://share.streamlit.io/ and choose **Create app** / **Deploy from GitHub**.
3. Select your repository and branch, set the main file to `app.py`, select Python 3.12 in advanced settings, then click **Deploy**.
4. No secrets are required. Optional provider keys can be added later through app settings/secrets. This repository needs no cloud warehouse or database provisioning.

This is a prepared deployment flow; account connection and repository selection are still required. No claim is made that a Streamlit Cloud instance has already been deployed.

## Deploy on Render

The included `render.yaml` is a ready-to-import Blueprint.

1. Push the source tree to a GitHub/GitLab repository you control.
2. In https://dashboard.render.com/ choose **New > Blueprint**, connect that repository and approve the generated web service.
3. Deploy the Blueprint. The manifest installs pinned dependencies and starts `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT`.
4. Optional API keys belong in environment variables, not in Git. Free services may sleep; open the app before the interview. Session and generated data are ephemeral and can be regenerated. Review the plan and any current billing terms before accepting a paid service.

Use the Render deployment link at the top of this README to import this repository and its Blueprint. Account sign-in and deployment approval are still required; this link does not imply that a Python instance is already deployed.

## Browser edition

Open `dist/index.html` directly for an offline backup, or serve `dist/` on a static host. No CDN assets or API keys are required. Tier filters, CSV/JSON export, guided presentation, reviewed action simulation and supported-question matching run in the browser. **Browser SQL answers are precomputed, verified snapshots. Live custom SQL and optional provider calls are in Streamlit.** Run `python scripts/build_snapshot.py` after any model/data change to refresh that edition.

## Production work remaining

Approved live ELT connectors (HubSpot, billing and PostHog); contractual Finance definitions and historical snapshots; roles and authentication; actual cloud warehouse/BI deployment; durable queues and delivery workers; monitoring, freshness SLAs and incident ownership; real-user validation of alert quality; provider evaluation and security review. Current automated evidence does not claim those integrations exist.

## Official references

- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- https://render.com/articles/deploy-streamlit-gradio-localhost-to-live
- https://docs.getdbt.com/docs/local/connect-data-platform/duckdb-setup
- https://docs.getdbt.com/reference/commands/build
- https://duckdb.org/docs/stable/clients/python/overview
- https://ai.google.dev/gemini-api/docs/quickstart
- https://platform.openai.com/docs/api-reference/chat/create
