"""Compile the same verified warehouse into a no-server, offline browser edition."""
import json,sys
from pathlib import Path
from datetime import date,datetime
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from warehouse.pipeline import run_pipeline,get_frames
from automations.copilot import build_alerts,webhook_payload,QUERIES,EXAMPLES,answer_question
from data.generate_data import AS_OF

def clean(obj):
 if isinstance(obj,(datetime,date)):return obj.isoformat()[:10]
 if hasattr(obj,'item'):return obj.item()
 if str(obj)=='NaT':return None
 raise TypeError(str(type(obj)))

def export():
 con,checks=run_pipeline();frames=get_frames(con)
 rows=lambda f:json.loads(f.to_json(orient='records',date_format='iso'))
 data={'as_of':str(AS_OF),'arr':rows(frames['mart_arr_truth']),'adoption':rows(frames['mart_feature_adoption']),'checks':checks,
       'alerts':build_alerts(frames['mart_arr_truth'],frames['mart_feature_adoption']),
       'trend':rows(con.execute('select billing_period,sum(finance_arr_cents) as arr_cents from stg_invoices group by 1 order by 1').df()),
       'lineage':{p.stem:p.read_text() for p in (ROOT/'warehouse'/'models').glob('*.sql')},'answers':{},
       'raw_events':con.execute('select count(*) from posthog_events').fetchone()[0],
       'clean_events':len(frames['stg_posthog_events'])}
 for q in EXAMPLES:
  result=answer_question(con,q)
  data['answers'][q]={'sql':result['sql'],'rows':rows(result['data'])}
 for alert in data['alerts']:alert['payload']=webhook_payload(alert)
 text=json.dumps(data,default=clean,indent=2,allow_nan=False)
 (ROOT/'dist'/'data.js').write_text('window.DEMO_DATA = '+text+';\n')
 (ROOT/'dist'/'snapshot.json').write_text(text)
 con.close();print('Verified browser snapshot exported.')

if __name__=='__main__':export()
