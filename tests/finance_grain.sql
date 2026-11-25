select account_id,billing_period from {{ ref('stg_invoices') }}
group by 1,2 having count(*)<>1
