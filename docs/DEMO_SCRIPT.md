# Flinn Pulse: your five-minute walkthrough

Use the **Present demo** button in the browser edition for the same speaking prompts. Keep the tier filter on **All tiers** when starting. Open the app in advance and reset the automation simulation before your call.

## Opening: 30 seconds

“Peter, I built a small prototype around the responsibilities in the job description. It connects recurring-revenue reconciliation, product tracking and reviewed automation. All 25 accounts and records are fictional. I would be happy to give you a short walkthrough if useful.”

If this is only a short screening call, offer a two-minute version and let Peter choose whether to see it.

## ARR Truth: 60 seconds

Show Finance reference ARR **EUR 1,963,200**, three CRM discrepancies and the movement bridge. CRM totals **EUR 1,973,700**, a net difference of **EUR 10,500**. The absolute discrepancies total **EUR 19,500**, because one is negative.

“The important part is the definition and reconciliation. Finance is my chosen demo reporting reference. I don't silently overwrite CRM. The account-level exceptions show exactly what needs investigation. Integer cents and an explicit account grain avoid accidental rounding and duplicate revenue.”

Opening **1,926,000** + new **67,200** + expansion **24,000** - contraction **6,000** - churn **48,000** = ending **1,963,200**. NRR is **98.4%** and GRR **97.2%**, using the starting customer cohort.

## Product Adoption & Event QA: 60 seconds

Select **Mid-Market**. Show gap-analysis adoption **1/8 = 12.5%**. Scroll to data quality checks. Show **two repeated renewals**, **three ARR conflicts**, **one missing close date**, **one malformed event**. Reset the tier to **All tiers** before moving on.

“Adoption requires at least three valid feature events over 30 days. Raw events stay available; the malformed event doesn't contaminate the mart. The failing source checks are deliberate. Passing transformation tests is different from claiming every business record is correct.”

## Automations: 60 seconds

Open the HelixMed renewal proposal. It has **EUR 132,000 ARR**, renewal in **18 days** and an **87.3%** usage decline (**79 to 10** events). Inspect the payload, approve the proposal, simulate delivery and retry simulation to show the duplicate is skipped.

“This is an interpretable review signal, not a churn prediction. An owner sees the evidence. The payload can enter an n8n workflow or a Slack message. Delivery here is simulated and recorded locally; a real queue would persist the stable ID and enforce the unique constraint.”

## SQL Copilot: 60 seconds

Choose **Which accounts have ARR mismatches?** Show SQL and the three account rows. Optionally choose the retention question or Mid-Market adoption question. Scroll to **Inspect an actual SQL model** and select `mart_arr_truth`.

“Seven question types work without any model API. The full Python app executes the reviewed SQL in DuckDB. This browser edition shows the same verified query snapshots. Optional provider generation uses the same validator. It cannot query raw tables, read files or run a write statement.”

## Close: 30 seconds

“The full source includes Streamlit, DuckDB, five modular SQL models, automated tests and deployment configuration. The next step would be to agree the actual Finance policy, connect approved sources and validate these signals with Product and Customer Success. Which of these problems would be most useful for your team first?”

## If Peter asks difficult questions

**Did you build this for production customers?** No. It is a focused prototype using deterministic synthetic data. No claims of real users, business savings or live Flinn integrations.

**Did you use AI to build it?** “Yes, I used AI coding assistance to accelerate the implementation. I reviewed and tested the logic, and I can walk through the components I understand. I would use the same discipline for code reviews and validation at work.” Practise the code paths before saying this.

**Is this genuine dbt?** The SQL files use `ref()` and can run through the included dbt project. The normal app uses a lightweight Python runner over the same SQL. A real dbt build was run against the synthetic seeds; the clean-layer data tests pass.

**Why DuckDB instead of BigQuery?** Reproducible local demo, no cloud credentials or spend. The modelling habits transfer, but BigQuery deployment needs a real adapter, IAM, partitioning/cost choices and dialect review. Do not imply that you already operated BigQuery at scale.

**Why isn't Finance always correct?** It is a chosen reference for this scenario. Real ARR must be agreed against contract terms and operational policy; invoice amounts, cash collection and accounting revenue are not interchangeable with ARR.

**How does read-only validation work?** Parse a single SELECT; restrict tables and functions; copy only published marts into an isolated in-memory DuckDB with external access disabled; cap results, memory and execution time. It is a prototype guardrail, not a claim of production security certification.

**Where is the AI?** Optional provider-assisted SQL generation. The no-key mode is deterministic intent matching and reviewed queries. The proactive risk engine is a rules engine. Describe each accurately rather than calling every component an AI agent.

**What doesn't work yet?** Live ELT connectors, cloud warehouse deployment, actual outbound Slack/n8n delivery, durable queue state, authenticated roles and production monitoring. The imported n8n workflow is a review-only example and has not been run against a live n8n instance.

## Run the full Python app

Download and unzip `Flinn_Pulse_Source.zip`. In the project directory:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

For a zero-install backup, open `dist/index.html` from the extracted source. It has no CDN dependencies. Read the README for Streamlit Community Cloud and Render deployment steps.

## Study before tomorrow at 15:00 Berlin time

1. Practise the opening and demonstrate each tab once.
2. Read the five SQL files; understand grain, deduplication, joining and date windows.
3. Explain ARR vs revenue vs cash, NRR vs GRR and the adoption denominator.
4. Explain why the four diagnostic checks fail while regression/dbt tests pass.
5. Test the offline backup, microphone and calendar link. Stop adding features and focus on explaining the working ones.
