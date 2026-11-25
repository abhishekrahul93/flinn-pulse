"""Shared, idempotent warehouse runner. SQL files are also a genuine dbt project."""
from dataclasses import asdict, dataclass
from pathlib import Path
import re
import duckdb
from data.generate_data import generate_data, DATA_DIR, AS_OF, FEATURES

ROOT=Path(__file__).resolve().parents[1]
MODEL_ORDER=['stg_hubspot_deals','stg_invoices','stg_posthog_events','mart_arr_truth','mart_feature_adoption']

@dataclass
class Check:
 name:str
 severity:str
 failing_rows:int
 description:str
 @property
 def status(self):return 'PASS' if self.failing_rows==0 else 'FAIL'
 def as_dict(self):return {**asdict(self),'status':self.status}

def run_pipeline(db_path=':memory:', data_dir=DATA_DIR):
 paths=generate_data(data_dir)
 con=duckdb.connect(str(db_path))
 con.execute("SET memory_limit='256MB'");con.execute('SET threads=1')
 try:
  con.execute('begin transaction')
  for name,path in paths.items():
   con.execute(f'create or replace table {name} as select * from read_csv_auto(?,header=true)',[str(path)])
  for name in MODEL_ORDER:
   text=(ROOT/'warehouse'/'models'/f'{name}.sql').read_text()
   text=re.sub(r"\{\{\s*ref\('([a-z_]+)'\)\s*\}\}",r'\1',text)
   con.execute(f'create or replace table {name} as {text}')
  con.execute('commit')
 except Exception:
  con.execute('rollback');con.close();raise
 checks=run_checks(con)
 return con,checks

def run_checks(con):
 allowed=','.join("'"+f+"'" for f in FEATURES)
 specs=[
 ('Raw duplicate renewal records','warning','select count(*)-count(distinct deal_id) from hubspot_deals','Replay records are removed in staging; upstream fix remains open.'),
 ('Closed-won deal close date','critical',"select count(*) from stg_hubspot_deals where stage='Closed Won' and close_date is null",'Required CRM field; no date is invented.'),
 ('CRM / Finance ARR reconciliation','critical',"select count(*) from mart_arr_truth where variance_cents<>0",'Account-level recurring ARR differs; Finance reference retained pending review.'),
 ('Governed event names','warning',f'select count(*) from posthog_events where event_name not in ({allowed})','Non-contract event is quarantined, not silently renamed.'),
 ('Staged deal IDs unique','critical','select count(*)-count(distinct deal_id) from stg_hubspot_deals','One staged row per deal ID.'),
 ('Staged event IDs unique','critical','select count(*)-count(distinct event_id) from stg_posthog_events','Replays cannot inflate adoption.'),
 ('ARR truth account grain','critical','select count(*)-count(distinct account_id) from mart_arr_truth','Exactly one row per reporting account.'),
 ('Finance account-period grain','critical',"select count(*) from (select account_id,billing_period from stg_invoices group by 1,2 having count(*)<>1)",'No duplicate account-month invoice snapshots.'),
 ('Finance amounts nonnegative','critical','select count(*) from stg_invoices where finance_arr_cents<0 or finance_arr_cents is null','Integer EUR cents with required amounts.'),
 ('Product account references','critical','select count(*) from posthog_events e left join stg_hubspot_deals a using(account_id) where a.account_id is null','All product events reference known accounts.'),
 ('ARR bridge reconciles','critical','select case when sum(previous_arr_cents)+sum(delta_arr_cents)=sum(arr_cents) then 0 else 1 end from mart_arr_truth','Opening ARR plus movements equals ending ARR.'),
 ('Snapshot freshness','warning',f"select case when max(billing_period)=date '{AS_OF.replace(day=1)}' then 0 else 1 end from stg_invoices",'Latest financial snapshot matches the fixed demo month.'),
 ]
 return [Check(n,s,int(con.execute(sql).fetchone()[0]),d).as_dict() for n,s,sql,d in specs]

def get_frames(con):
 return {name:con.execute(f'select * from {name}').df() for name in MODEL_ORDER}

if __name__=='__main__':
 c,checks=run_pipeline(ROOT/'warehouse'/'pulse.duckdb')
 for ch in checks:print(f"{ch['status']:4} {ch['severity']:8} {ch['failing_rows']:3} {ch['name']}")
 c.close()

