"""Deterministic fictional SaaS data. No Flinn or real customer data is used."""
import csv
from datetime import date, datetime, timedelta
from pathlib import Path
import random

AS_OF = date(2026, 11, 24)
DATA_DIR = Path(__file__).resolve().parent / 'generated'
FEATURES = ['technical_doc_generated','pms_report_exported','regulatory_check_run','audit_trail_verified','ai_gap_analysis_triggered']
NAMES = ['HelixMed Diagnostics','NordicOrtho GmbH','VascuCare AG','BioPulse Devices','Lumen Clinical Systems','Aster Pharma','Meridian Surgical','Solace Instruments','Clearpath Biologics','NovaLife Implants','Atlas Therapeutics','Crest Medical','Vela BioSystems','Ember Health','Northstar Devices','Aurora Diagnostics','VitalBridge Labs','Cobalt Clinical','Ardent MedTech','Pinnacle Pharma','Verity Medical','Evergreen Surgical','Lumina Health','Cascade Devices','Beacon Bioanalytics']

def generate_data(directory=DATA_DIR, force=False):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
 paths={name:directory/f'{name}.csv' for name in ['hubspot_deals','finance_invoices','posthog_events']}
 if not force and all(p.exists() for p in paths.values()):return paths
 rng=random.Random(42);deals=[];invoices=[];events=[]
 for i,name in enumerate(NAMES):
  aid=f'acct_{i+1:02d}';tier='Enterprise' if i<8 else 'Mid-Market' if i<17 else 'Growth'
  base=(120000+i*12000) if i<8 else (42000+(i-8)*3000) if i<17 else (18000+(i-17)*2400)
  previous=base
  current=base+(12000 if i in [0,5] else -6000 if i==9 else 0)
  if i==10:current=0
  if i>=23:previous=0
  renewal=AS_OF+timedelta(days=18+i*4 if i<4 else 70+i*3)
  crm=current+(9000 if i==2 else -4500 if i==11 else 6000 if i==18 else 0)
  deal=dict(deal_id=f'deal_{i+1:02d}',account_id=aid,account_name=name,tier=tier,csm_owner=['Maya Chen','Jon Bell','Lena Park','Sam Reed'][i%4],deal_type='Expansion' if i in [0,5] else 'New' if i>=23 else 'Renewal',stage='Closed Won',hubspot_arr_eur=crm,close_date='' if i==6 else '2026-11-01',renewal_date=renewal.isoformat())
  deals.append(deal)
  for month,amount in [('2026-09-01',int(previous*.95/12)*12),('2026-10-01',previous),('2026-11-01',current)]:
   invoices.append(dict(invoice_id=f'inv_{aid}_{month[:7]}',account_id=aid,billing_period=month,invoiced_arr_eur=amount,payment_status='Overdue' if i in [2,11] and month=='2026-11-01' else 'Pending' if i>=23 and month=='2026-11-01' else 'Paid',issued_date=month))
  for fi,feature in enumerate(FEATURES):
   # Only 1 of 8 currently active Mid-Market accounts adopts gap analysis.
   if tier=='Mid-Market' and feature=='ai_gap_analysis_triggered' and i!=8:continue
   if tier=='Growth' and feature=='ai_gap_analysis_triggered' and i%2:continue
   normal_count=(12 if tier=='Enterprise' else 6 if tier=='Mid-Market' else 3)+rng.randint(0,4)
   for period,start in [('previous',AS_OF-timedelta(days=59)),('current',AS_OF-timedelta(days=29))]:
    count=normal_count+rng.randint(0,3)
    if i<4 and period=='current':count=max(1,int(normal_count*.18))
    if i==10 and period=='current':count=0
    if i>=23 and period=='previous':count=0
    for n in range(count):
     ts=datetime.combine(start+timedelta(days=(n*3+fi)%30),datetime.min.time())+timedelta(hours=8+(n%9),minutes=n%60)
     events.append(dict(event_id=f'{aid}_{fi}_{period}_{n:03}',account_id=aid,user_id=f'{aid}_user_{n%4+1}',event_name=feature,timestamp=ts.isoformat(),duration_sec=round(rng.uniform(2,180),1)))
 # Exactly two repeated renewal records, three account ARR mismatches and one missing close date.
 deals.extend([dict(deals[3]),dict(deals[7])])
 events.append(dict(event_id='bad_event_001',account_id='acct_01',user_id='acct_01_user_1',event_name='ClickedExportBtn',timestamp='2026-11-24T11:00:00',duration_sec=2))
 for name,rows in [('hubspot_deals',deals),('finance_invoices',invoices),('posthog_events',events)]:
  with paths[name].open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 return paths

if __name__=='__main__':
 for name,path in generate_data(force=True).items():print(f'{name}: {path}')

