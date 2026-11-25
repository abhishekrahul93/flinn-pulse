-- Explicit allowlist is the tracking contract. Invalid events remain in raw data.
select event_id,account_id,user_id,event_name,cast(timestamp as timestamp) as event_time,
 duration_sec::double as duration_sec
from {{ ref('posthog_events') }}
where event_name in ('technical_doc_generated','pms_report_exported','regulatory_check_run','audit_trail_verified','ai_gap_analysis_triggered')
 and account_id in (select account_id from {{ ref('stg_hubspot_deals') }})
qualify row_number() over (partition by event_id order by timestamp desc)=1

