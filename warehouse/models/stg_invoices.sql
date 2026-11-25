-- Demo invoice field is the annualised recurring contract equivalent, in EUR.
select invoice_id,account_id,cast(billing_period as date) as billing_period,
 round(invoiced_arr_eur*100)::bigint as finance_arr_cents,
 payment_status,cast(issued_date as date) as issued_date
from {{ ref('finance_invoices') }}

