-- Contract snapshots, not additive deal line items. Remove replayed deal IDs.
select deal_id, account_id, account_name, tier, csm_owner, deal_type, stage,
 round(hubspot_arr_eur*100)::bigint as hubspot_arr_cents,
 try_cast(close_date as date) as close_date, cast(renewal_date as date) as renewal_date
from {{ ref('hubspot_deals') }}
qualify row_number() over (partition by deal_id order by close_date desc nulls last, account_id)=1

