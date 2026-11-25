select 1 where
 (select sum(previous_arr_cents)+sum(delta_arr_cents) from {{ ref('mart_arr_truth') }})
 <> (select sum(arr_cents) from {{ ref('mart_arr_truth') }})
