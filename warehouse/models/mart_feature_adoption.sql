-- Grain: eligible account / governed feature. The fixed snapshot keeps the demo reproducible.
with features as (
 select unnest(['technical_doc_generated','pms_report_exported','regulatory_check_run','audit_trail_verified','ai_gap_analysis_triggered']) as feature
), usage as (
 select account_id,event_name,
 count(*) filter(where event_time>=timestamp '2026-10-26' and event_time<timestamp '2026-11-25') as current_events,
 count(*) filter(where event_time>=timestamp '2026-09-26' and event_time<timestamp '2026-10-26') as previous_events
 from {{ ref('stg_posthog_events') }} group by account_id,event_name
)
select a.account_id,a.account_name,a.tier,a.csm_owner,a.arr_cents,a.renewal_date,
 f.feature,coalesce(u.current_events,0) as current_events,coalesce(u.previous_events,0) as previous_events,
 coalesce(u.current_events,0)>=3 as adopted
from {{ ref('mart_arr_truth') }} a cross join features f
left join usage u on u.account_id=a.account_id and u.event_name=f.feature
where a.arr_cents>0

