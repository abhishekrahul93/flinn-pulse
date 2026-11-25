"""Explainable alerts, review-only delivery simulation and constrained SQL Q&A."""
import hashlib,json,os,threading,urllib.request
from datetime import date
import duckdb
import sqlglot
from sqlglot import exp
from data.generate_data import AS_OF

EXAMPLES=[
 'What is our total ARR?',
 'Which accounts have ARR mismatches?',
 'Which accounts renew in the next 45 days?',
 'Show ARR by tier',
 'Which features have lowest Mid-Market adoption?',
 'Which high-value accounts have declining usage?',
 'What is our net revenue retention?'
]
QUERIES={
 'total':"SELECT SUM(arr_cents)/100.0 AS finance_arr_eur, SUM(crm_arr_cents)/100.0 AS crm_arr_eur, SUM(variance_cents)/100.0 AS net_variance_eur FROM mart_arr_truth",
 'mismatch':"SELECT account_name,tier,crm_arr_cents/100.0 AS crm_arr_eur,arr_cents/100.0 AS finance_arr_eur,variance_cents/100.0 AS variance_eur FROM mart_arr_truth WHERE variance_cents<>0 ORDER BY ABS(variance_cents) DESC",
 'renewal':"SELECT account_name,tier,arr_cents/100.0 AS arr_eur,renewal_date FROM mart_arr_truth WHERE renewal_date BETWEEN DATE '2026-11-24' AND DATE '2027-01-08' AND arr_cents>0 ORDER BY renewal_date",
 'tier':"SELECT tier,SUM(arr_cents)/100.0 AS arr_eur,COUNT(*) AS accounts FROM mart_arr_truth WHERE arr_cents>0 GROUP BY tier ORDER BY arr_eur DESC",
 'feature':"SELECT feature,COUNT(*) AS eligible_accounts,SUM(CASE WHEN adopted THEN 1 ELSE 0 END) AS adopted_accounts,ROUND(100.0*SUM(CASE WHEN adopted THEN 1 ELSE 0 END)/COUNT(*),1) AS adoption_pct FROM mart_feature_adoption WHERE tier='Mid-Market' GROUP BY feature ORDER BY adoption_pct,feature",
 'risk':"SELECT account_name,MAX(arr_cents)/100.0 AS arr_eur,SUM(previous_events) AS previous_events,SUM(current_events) AS current_events,ROUND(100.0*(SUM(current_events)-SUM(previous_events))/NULLIF(SUM(previous_events),0),1) AS change_pct FROM mart_feature_adoption GROUP BY account_name HAVING MAX(arr_cents)>=6000000 AND SUM(previous_events)>=10 AND SUM(current_events)*2<=SUM(previous_events) ORDER BY change_pct",
 'retention':"SELECT ROUND(100.0*SUM(CASE WHEN previous_arr_cents>0 THEN arr_cents ELSE 0 END)/NULLIF(SUM(previous_arr_cents),0),2) AS nrr_pct, ROUND(100.0*SUM(CASE WHEN previous_arr_cents>0 THEN LEAST(arr_cents,previous_arr_cents) ELSE 0 END)/NULLIF(SUM(previous_arr_cents),0),2) AS grr_pct FROM mart_arr_truth"
}

def classify(question):
 q=question.lower()
 if any(w in q for w in ['mismatch','discrepanc','variance','reconcil']):return 'mismatch'
 if 'renew' in q:return 'renewal'
 if any(w in q for w in ['retention','nrr','grr']):return 'retention'
 if any(w in q for w in ['declin','risk','drop']):return 'risk'
 if any(w in q for w in ['feature','adoption','mid-market']):return 'feature'
 if any(w in q for w in ['by tier','segment','per tier']):return 'tier'
 if any(w in q for w in ['total','overall','our arr','current arr']):return 'total'
 return None

ALLOWED_TABLES={'mart_arr_truth','mart_feature_adoption'}
ALLOWED_FUNCTIONS={'SUM','COUNT','AVG','MIN','MAX','ROUND','ABS','COALESCE','NULLIF','LOWER','UPPER','LEAST','GREATEST','CAST','TRY_CAST','IF','CASE','AND','OR','NOT'}

def validate_sql(sql):
 if len(sql)>10000:raise ValueError('Query is too long.')
 try:trees=sqlglot.parse(sql,read='duckdb')
 except sqlglot.errors.ParseError as exc:raise ValueError('SQL could not be parsed.') from exc
 if len(trees)!=1 or not isinstance(trees[0],(exp.Select,exp.Union)):
  raise ValueError('Only one read-only SELECT statement is permitted.')
 tree=trees[0];ctes={c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
 for table in tree.find_all(exp.Table):
  if not isinstance(table.this,exp.Identifier) or table.db or table.catalog or table.name.lower() not in ALLOWED_TABLES|ctes:
   raise ValueError('Only the two published marts may be queried; external data access is blocked.')
 for node in tree.walk():
  if isinstance(node,exp.Func):
   name=node.name.upper() if isinstance(node,exp.Anonymous) else node.sql_name().upper()
   if name not in ALLOWED_FUNCTIONS:raise ValueError(f'Function {name} is not permitted.')
 return tree.sql(dialect='duckdb')

def execute_read_only(warehouse,sql):
 sql=validate_sql(sql)
 # Query a fresh, isolated database containing only published marts.
 # It has no raw data, credentials, file-backed DB or enabled external access.
 sandbox=duckdb.connect(':memory:',config={'enable_external_access':'false','memory_limit':'128MB','threads':'1'})
 try:
  for table in sorted(ALLOWED_TABLES):
   frame=warehouse.execute(f'select * from {table}').df()
   sandbox.register('_frame',frame)
   sandbox.execute(f'create table {table} as select * from _frame');sandbox.unregister('_frame')
  timer=threading.Timer(3,sandbox.interrupt);timer.start()
  try:result=sandbox.execute('SELECT * FROM ('+sql+') AS answer LIMIT 100').df()
  finally:timer.cancel()
  return result
 finally:sandbox.close()

SCHEMA='mart_arr_truth(account_id,account_name,tier,csm_owner,renewal_date,close_date,billing_period,payment_status,crm_arr_cents,arr_cents,previous_arr_cents,variance_cents,reconciliation_status,movement,delta_arr_cents); mart_feature_adoption(account_id,account_name,tier,csm_owner,arr_cents,renewal_date,feature,current_events,previous_events,adopted). Money is EUR cents. As of 2026-11-24. Return only SELECT SQL against these two marts. No markdown, functions that access external data, DDL or DML.'

def provider_sql(question):
 # Only schema and the question leave the app. No warehouse rows or keys are logged.
 if os.environ.get('GEMINI_API_KEY'):
  model=os.environ.get('GEMINI_MODEL','gemini-2.5-flash')
  url=f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
  body={'contents':[{'parts':[{'text':SCHEMA+'\nQuestion: '+question}]}],'generationConfig':{'temperature':0}}
  headers={'Content-Type':'application/json','x-goog-api-key':os.environ['GEMINI_API_KEY']}
  req=urllib.request.Request(url,json.dumps(body).encode(),headers)
  with urllib.request.urlopen(req,timeout=15) as r:data=json.load(r)
  text=data['candidates'][0]['content']['parts'][0]['text'];provider='Gemini'
 elif os.environ.get('OPENAI_API_KEY'):
  body={'model':os.environ.get('OPENAI_MODEL','gpt-4.1-mini'),'messages':[{'role':'system','content':SCHEMA},{'role':'user','content':question}]}
  headers={'Content-Type':'application/json','Authorization':'Bearer '+os.environ['OPENAI_API_KEY']}
  req=urllib.request.Request('https://api.openai.com/v1/chat/completions',json.dumps(body).encode(),headers)
  with urllib.request.urlopen(req,timeout=15) as r:data=json.load(r)
  text=data['choices'][0]['message']['content'];provider='OpenAI'
 else:raise ValueError('No provider key configured.')
 return text.strip().removeprefix('```sql').removeprefix('```').removesuffix('```').strip(),provider

def answer_question(warehouse,question,use_provider=False):
 intent=classify(question);notice=''
 if use_provider:
  try:
   sql,mode=provider_sql(question)
   df=execute_read_only(warehouse,sql)
   return {'sql':sql,'data':df,'mode':mode,'notice':'Provider-generated SQL passed the same validator. Inspect the result before using it.'}
  except Exception:
   notice='The configured provider was unavailable or returned an invalid query. Used a supported deterministic answer instead.'
 if not intent:return {'sql':'','data':None,'mode':'Deterministic','notice':'Choose a suggested question or ask about total ARR, mismatches, renewals, tier ARR, feature adoption, declining usage or retention.'}
 sql=QUERIES[intent];df=execute_read_only(warehouse,sql)
 return {'sql':sql,'data':df,'mode':'Deterministic','notice':notice or 'A supported question was mapped to a reviewed SQL template, then executed against the marts.'}

def build_alerts(arr,adoption):
 alerts=[]
 def add(rule,key,title,account,tier,owner,evidence):
  event_id=hashlib.sha256(f'{AS_OF}|{rule}|{key}'.encode()).hexdigest()[:20]
  alerts.append({'event_id':event_id,'rule':rule,'title':title,'account_name':account,'tier':tier,'owner':owner,'evidence':evidence,'as_of':AS_OF.isoformat(),'status':'Needs review'})
 for r in arr.to_dict('records'):
  if r['variance_cents']:
   add('arr_reconciliation',r['account_id'],'Reconcile CRM vs Finance',r['account_name'],r['tier'],'Finance',f"CRM €{r['crm_arr_cents']/100:,.0f}; Finance €{r['arr_cents']/100:,.0f}; difference €{r['variance_cents']/100:,.0f}. Do not overwrite either source automatically.")
  if r['reconciliation_status']=='Missing close date':
   add('crm_required_field',r['account_id'],'Complete required CRM field',r['account_name'],r['tier'],r['csm_owner'],'Closed-won deal is missing close_date; request the correct date from the record owner.')
 usage=adoption.groupby(['account_id','account_name','tier','csm_owner','arr_cents','renewal_date'],dropna=False)[['current_events','previous_events']].sum().reset_index()
 for r in usage.to_dict('records'):
  days=(r['renewal_date'].date()-AS_OF).days
  if r['arr_cents']>=6000000 and 0<=days<=45 and r['previous_events']>=10 and r['current_events']*2<=r['previous_events']:
   drop=100*(1-r['current_events']/r['previous_events'])
   add('renewal_usage_risk',r['account_id'],'Review renewal adoption decline',r['account_name'],r['tier'],r['csm_owner'],f"€{r['arr_cents']/100:,.0f} ARR; renewal in {days} days; events fell {drop:.1f}% ({r['previous_events']} to {r['current_events']}) across equal 30-day windows. A review signal, not a churn prediction.")
 mm=adoption[adoption.tier=='Mid-Market']
 for feature,g in mm.groupby('feature'):
  rate=float(g.adopted.mean())
  if rate<.2:add('feature_underadoption',feature,'Investigate feature adoption','Mid-Market portfolio','Mid-Market','Product',f'{feature}: {int(g.adopted.sum())}/{len(g)} eligible accounts adopted ({rate:.1%}); adoption requires 3+ events in 30 days. Check onboarding and customer relevance before changing the feature.')
 return alerts

def webhook_payload(alert):
 return {'schema_version':'1.0','event_id':alert['event_id'],'event_type':alert['rule'],'occurred_at':alert['as_of']+'T12:00:00Z','mode':'demo_review_only','review_required':True,'owner':alert['owner'],'account':alert['account_name'],'evidence':alert['evidence'],'slack':{'text':alert['title']+' | '+alert['account_name'],'blocks':[{'type':'section','text':{'type':'mrkdwn','text':'*'+alert['title']+'*\n'+alert['account_name']+'\n'+alert['evidence']}}]}}

def transition(ledger,event_id,command):
 current=ledger.get(event_id,'Needs review')
 if command=='approve' and current=='Needs review':ledger[event_id]='Approved';return 'approved'
 if command=='record' and current=='Approved':ledger[event_id]='Recorded locally';return 'recorded'
 if command=='record' and current=='Recorded locally':return 'duplicate_skipped'
 return 'invalid_transition'
