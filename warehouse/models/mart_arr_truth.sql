-- Finance snapshot is the demo reporting reference. Differences are flagged, never overwritten.
with history as (
 select *,lag(finance_arr_cents,1,0) over(partition by account_id order by billing_period) as previous_arr_cents
 from {{ ref('stg_invoices') }}
), current_invoice as (
 select * from history qualify row_number() over(partition by account_id order by billing_period desc,issued_date desc,invoice_id desc)=1
), crm as (
 select * from {{ ref('stg_hubspot_deals') }} where stage='Closed Won'
 qualify row_number() over(partition by account_id order by close_date desc nulls last,deal_id desc)=1
)
select c.account_id,c.account_name,c.tier,c.csm_owner,c.renewal_date,c.close_date,
 i.billing_period,i.payment_status,c.hubspot_arr_cents as crm_arr_cents,
 i.finance_arr_cents as arr_cents,i.previous_arr_cents,
 c.hubspot_arr_cents-i.finance_arr_cents as variance_cents,
 case when c.close_date is null then 'Missing close date'
      when c.hubspot_arr_cents<>i.finance_arr_cents then 'ARR mismatch'
      else 'Reconciled' end as reconciliation_status,
 case when i.previous_arr_cents=0 and i.finance_arr_cents>0 then 'New business'
      when i.previous_arr_cents>0 and i.finance_arr_cents=0 then 'Churn'
      when i.finance_arr_cents>i.previous_arr_cents then 'Expansion'
      when i.finance_arr_cents<i.previous_arr_cents then 'Contraction'
      else 'Stable' end as movement,
 i.finance_arr_cents-i.previous_arr_cents as delta_arr_cents
from current_invoice i left join crm c using(account_id)

