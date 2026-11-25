# Verification record

Verified on 24 November 2026 in Python 3.12.

- 13 backend regression tests passed. Coverage includes deterministic source generation, expected injected defects, financial invariants, all seven supported questions, rejected destructive/external-data SQL, result cap, provider-error fallback, unsafe-provider-output fallback, alert rules and approval/idempotency.
- Genuine `dbt build --profiles-dir .` completed: 3 seeds, 5 models and 11 data tests passed.
- Streamlit AppTest startup reported no exceptions. Tier filtering returned EUR 432,000 for Mid-Market; copilot returned EUR 1,963,200 total ARR; the custom SELECT path executed.
- Browser financial math reconciled for All, Enterprise, Mid-Market and Growth selections.
- Browser UI checked: revenue rendering, Mid-Market adoption, quality findings, approval, simulated delivery, duplicate retry, and visible discrepancy-query results.
- The four failing source/business diagnostic checks are expected demo findings, separate from regression tests and dbt invariants.

Not verified with live services: optional Gemini/OpenAI requests, imported n8n workflow execution, actual Slack delivery, Streamlit Community Cloud deployment and Render deployment. The browser publication is a static interactive edition with verified SQL snapshots, not the hosted Python runtime.
