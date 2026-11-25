"""Flinn Pulse: executable Streamlit portfolio prototype using synthetic data."""
import json,os
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from data.generate_data import AS_OF,FEATURES
from warehouse.pipeline import run_pipeline,get_frames,ROOT
from automations.copilot import build_alerts,webhook_payload,answer_question,execute_read_only,transition,EXAMPLES

st.set_page_config(page_title='Flinn Pulse | Abhishek Rahul',page_icon='🩺',layout='wide',initial_sidebar_state='expanded')
# Platform secrets stay server-side and are never rendered or written to disk.
for key in ['GEMINI_API_KEY','OPENAI_API_KEY','GEMINI_MODEL','OPENAI_MODEL']:
 if not os.environ.get(key):
  try:
   value=st.secrets.get(key)
   if value:os.environ[key]=str(value)
  except (FileNotFoundError,KeyError):
   pass
st.markdown('''<style>
.stApp{background:#f4f7fb;color:#17354c}h1,h2,h3{color:#17354c;letter-spacing:-.5px}
[data-testid="stSidebar"]{background:#eaf0f6;border-right:1px solid #d9e4ed}
[data-testid="stMetric"]{background:white;border:1px solid #dce5ed;border-radius:12px;padding:18px}
.block-container{padding-top:2rem}.pulse-hero{background:linear-gradient(115deg,#153e51,#172c45);padding:25px 28px;border-radius:13px;color:#fff;margin:10px 0 25px}
.pulse-hero h2{color:#fff;font-size:23px;margin:0 0 6px}.pulse-hero p{color:#c5d7e2;margin:0;font-size:14px}
.pulse-tag{display:inline-block;background:#d8f1e6;color:#1a6559;font-size:11px;border-radius:5px;padding:4px 8px;letter-spacing:1px;margin-bottom:7px}
</style>''',unsafe_allow_html=True)

@st.cache_data(show_spinner='Building the warehouse and checking the data...')
def load_snapshot():
 con,checks=run_pipeline();frames=get_frames(con);con.close()
 return frames,checks

def chart_layout(fig):
 fig.update_layout(template='plotly_white',font={'family':'Arial','color':'#26465a'},paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',margin=dict(l=10,r=10,t=35,b=10),height=330)
 return fig

def euro(cents):return f'€{cents/100:,.0f}'
def money_view(df):
 df=df.copy()
 for col in list(df):
  if col.endswith('_cents'):df[col.replace('_cents','_eur')]=df.pop(col)/100
 return df

frames,checks=load_snapshot()
arr_all=frames['mart_arr_truth'];adoption_all=frames['mart_feature_adoption']
with st.sidebar:
 st.markdown('## Flinn Pulse')
 st.caption('MEDTECH BI & AUTOMATIONS HUB')
 st.markdown('**Built by Abhishek Rahul**')
 st.info('Independent portfolio prototype. All 25 accounts and records are fictional.')
 tier=st.selectbox('Account tier',['All tiers','Enterprise','Mid-Market','Growth'])
 st.caption(f'Fixed snapshot: {AS_OF:%d %B %Y}\n\nCurrent usage: 26 Oct–24 Nov\n\nPrevious: 26 Sep–25 Oct')
 if st.button('Rebuild warehouse',width='stretch'):
  load_snapshot.clear();st.rerun()
 with st.expander('What this demonstrates'):
  st.write('Modular SQL, ARR reconciliation, event governance, explainable signals, review controls and guarded SQL Q&A.')
  st.write('No live HubSpot/PostHog connection. No Slack messages are sent. The review ledger lasts only for this browser session.')
 source=ROOT/'dist'/'Flinn_Pulse_Source.zip'
 if source.exists():st.download_button('Download full source',source.read_bytes(),file_name=source.name,width='stretch')
 else:st.link_button('View source on GitHub','https://github.com/abhishekrahul93/flinn-pulse',width='stretch')

arr=arr_all if tier=='All tiers' else arr_all[arr_all.tier==tier]
adoption=adoption_all if tier=='All tiers' else adoption_all[adoption_all.tier==tier]
alerts_all=build_alerts(arr_all,adoption_all)
alerts=alerts_all if tier=='All tiers' else [a for a in alerts_all if a['tier']==tier]
st.markdown('<span class="pulse-tag">SYNTHETIC DATA / EXECUTABLE PROTOTYPE</span>',unsafe_allow_html=True)
st.title('Flinn Pulse')
st.caption('MedTech BI, ARR Truth & AI Automations Hub')
st.markdown('<div class="pulse-hero"><h2>Trusted numbers. Clear signals. Reviewed actions.</h2><p>A complete path from raw business records to explainable decisions, with every assumption visible.</p></div>',unsafe_allow_html=True)
tabs=st.tabs(['ARR Truth','Product Adoption & Event QA','Automations','SQL Copilot'])

with tabs[0]:
 st.subheader('One recurring-revenue reference')
 st.caption('Finance is the chosen demo reporting reference; CRM conflicts remain visible for investigation. All amounts are annualised recurring EUR, excluding one-off fees and taxes.')
 start=int(arr.previous_arr_cents.sum());end=int(arr.arr_cents.sum())
 nrr=arr.loc[arr.previous_arr_cents>0,'arr_cents'].sum()/start if start else 0
 cols=st.columns(4)
 cols[0].metric('Finance reference ARR',euro(end),euro(end-start)+' vs October')
 cols[1].metric('CRM reference ARR',euro(int(arr.crm_arr_cents.sum())))
 cols[2].metric('ARR discrepancies',int((arr.variance_cents!=0).sum()),'Requires source review',delta_color='off')
 cols[3].metric('Net revenue retention',f'{nrr:.1%}','Starting customer cohort',delta_color='off')
 left,right=st.columns([1.5,1])
 with left:
  st.markdown('#### ARR movement bridge')
  vals=[int(arr.loc[arr.movement==m,'delta_arr_cents'].sum())/100 for m in ['New business','Expansion','Contraction','Churn']]
  fig=go.Figure(go.Waterfall(x=['October','New business','Expansion','Contraction','Churn','November'],measure=['absolute','relative','relative','relative','relative','total'],y=[start/100,*vals,0],connector={'line':{'color':'#b8c9d4'}},increasing={'marker':{'color':'#138e80'}},decreasing={'marker':{'color':'#d06a76'}},totals={'marker':{'color':'#183e52'}}))
  fig.update_layout(yaxis_tickprefix='€');st.plotly_chart(chart_layout(fig),width='stretch')
 with right:
  st.markdown('#### ARR by account tier')
  grouped=arr.groupby('tier',as_index=False).arr_cents.sum();grouped['ARR EUR']=grouped.arr_cents/100
  st.plotly_chart(chart_layout(px.bar(grouped,x='tier',y='ARR EUR',color='tier',color_discrete_sequence=['#173e52','#138e80','#8bcdbd'])),width='stretch')
 st.markdown('#### Account-level reconciliation')
 st.dataframe(money_view(arr[['account_name','tier','crm_arr_cents','arr_cents','variance_cents','reconciliation_status','renewal_date','payment_status']]),hide_index=True,width='stretch')
 st.download_button('Export ARR reconciliation CSV',money_view(arr).to_csv(index=False),'arr_reconciliation.csv','text/csv')
 with st.expander('Metric policy and reporting limits'):
  st.write('ARR is a point-in-time annualised recurring contract equivalent. Synthetic invoice snapshots already contain annualised amounts; this demo does not annualise arbitrary invoice totals. Pending or overdue payment does not by itself remove contracted ARR. CRM deal records are full contract snapshots, not additive expansion line items. One latest closed-won snapshot per account is selected.')
  st.write('GRR excludes expansion; NRR includes expansion but excludes new accounts. All data is EUR; no foreign-exchange modelling. A production implementation would agree contract status, credits, cancellations, FX, history and ownership with Finance.')
  st.write('Critical source issues remain open. Passing transformation tests does not mean every business record is reconciled.')

with tabs[1]:
 st.subheader('Usage signals grounded in a tracking contract')
 st.caption('Adoption means at least 3 governed feature events during the current 30-day window. Only accounts with positive current ARR are eligible.')
 c1,c2,c3=st.columns(3)
 c1.metric('Eligible active accounts',adoption.account_id.nunique())
 c2.metric('Governed features',len(FEATURES))
 bad=[c for c in checks if c['name']=='Governed event names'][0]
 c3.metric('Quarantined event names',bad['failing_rows'])
 grouped=adoption.groupby(['tier','feature'],as_index=False).adopted.mean();grouped['adoption_pct']=grouped.adopted*100
 fig=px.bar(grouped,x='feature',y='adoption_pct',color='tier',barmode='group',color_discrete_sequence=['#173e52','#138e80','#8bcdbd'],labels={'adoption_pct':'Adoption %','feature':'Governed feature'})
 fig.update_yaxes(range=[0,105]);st.plotly_chart(chart_layout(fig),width='stretch')
 st.markdown('#### Account usage, current vs previous 30 days')
 usage=adoption.groupby(['account_name','tier','arr_cents'],as_index=False)[['current_events','previous_events']].sum()
 usage['change_pct']=((usage.current_events-usage.previous_events)/usage.previous_events.replace(0,float('nan'))*100).round(1)
 st.dataframe(money_view(usage).sort_values('change_pct'),hide_index=True,width='stretch')
 st.markdown('#### Automated data quality checks · whole warehouse')
 st.caption('Expected source defects are deliberately visible below. Eight clean-layer/invariant checks pass; four source/business checks fail on the injected records.')
 st.dataframe(pd.DataFrame(checks)[['name','status','severity','failing_rows','description']],hide_index=True,width='stretch')
 with st.expander('Tracking contract and modular SQL'):
  st.write('Required fields: event_id, account_id, user_id, event_name, timestamp and duration_sec. Event names use an explicit object_action allowlist. Unknown names stay in raw data and are excluded from adoption. Windows use UTC timestamps and a fixed as-of date.')
  st.code('\n'.join(FEATURES))
  model=st.selectbox('Inspect an actual SQL model',[p.stem for p in (ROOT/'warehouse'/'models').glob('*.sql')])
  st.code((ROOT/'warehouse'/'models'/f'{model}.sql').read_text(),language='sql')

with tabs[2]:
 st.subheader('Proactive, explainable automation proposals')
 st.caption('Rules identify review tasks. Payloads are Slack/n8n-compatible examples; delivery is simulated. The session ledger uses stable event IDs to avoid duplicate recording.')
 st.session_state.setdefault('ledger',{});st.session_state.setdefault('audit',[])
 c1,c2,c3=st.columns(3)
 c1.metric('Review proposals',len(alerts));c2.metric('Renewal usage signals',sum(a['rule']=='renewal_usage_risk' for a in alerts));c3.metric('Recorded locally',sum(st.session_state.ledger.get(a['event_id'])=='Recorded locally' for a in alerts))
 with st.expander('Rule definitions'):
  st.write('Renewal review: ARR ≥ €60,000; renewal within 45 days; at least 10 previous events; current events down ≥50% over equal 30-day windows. Feature review: Mid-Market feature adoption <20%. Finance review: nonzero CRM/Finance variance. These are transparent heuristics, not validated churn predictions.')
 for a in alerts:
  aid=a['event_id'];state=st.session_state.ledger.get(aid,'Needs review')
  with st.expander(f"{a['title']} · {a['account_name']} · {state}"):
   st.write(a['evidence']);st.caption(f"Owner: {a['owner']} | Stable event ID: {aid}")
   payload=webhook_payload(a);st.json(payload,expanded=False)
   buttons=st.columns(3)
   if buttons[0].button('Approve proposal',key='approve_'+aid,disabled=state!='Needs review'):
    result=transition(st.session_state.ledger,aid,'approve');st.session_state.audit.append({'event_id':aid,'action':result});st.rerun()
   if buttons[1].button('Simulate delivery',key='record_'+aid,disabled=state not in ['Approved','Recorded locally']):
    result=transition(st.session_state.ledger,aid,'record');st.session_state.audit.append({'event_id':aid,'action':result});st.rerun()
   buttons[2].download_button('Download webhook JSON',json.dumps(payload,indent=2),f'pulse_{aid}.json','application/json',key='download_'+aid)
 st.markdown('#### Review audit · this session')
 st.dataframe(pd.DataFrame(st.session_state.audit,columns=['event_id','action']),hide_index=True,width='stretch')
 if st.button('Reset simulated review state'):
  st.session_state.ledger={};st.session_state.audit=[];st.rerun()

with tabs[3]:
 st.subheader('Ask the warehouse. Inspect the SQL.')
 st.caption('Seven reviewed question types work without any API key. Answers come from live DuckDB queries, not generated numbers. This tab queries the whole warehouse; the sidebar tier filter does not apply.')
 example=st.selectbox('Suggested question',EXAMPLES)
 question=st.text_input('Your question',value=example,key='question_'+str(EXAMPLES.index(example)))
 configured=bool(os.environ.get('GEMINI_API_KEY') or os.environ.get('OPENAI_API_KEY'))
 use_provider=st.checkbox('Use configured AI provider for SQL generation',value=False,disabled=not configured)
 st.caption('Provider mode sends only your question and the published schema. Missing/invalid provider responses fall back to a supported deterministic query. Arbitrary questions may be unsupported.')
 if st.button('Answer question',type='primary'):
  con,_=run_pipeline()
  try:st.session_state['answer']=answer_question(con,question,use_provider)
  finally:con.close()
 if 'answer' in st.session_state:
  result=st.session_state.answer;st.info(result['mode']+' · '+result['notice'])
  if result['data'] is not None:
   st.code(result['sql'],language='sql');st.dataframe(result['data'],hide_index=True,width='stretch')
   st.download_button('Export answer CSV',result['data'].to_csv(index=False),'copilot_answer.csv','text/csv')
 with st.expander('Run your own read-only SQL'):
  custom=st.text_area('SELECT from the two published marts',value='SELECT account_name, arr_cents / 100.0 AS arr_eur FROM mart_arr_truth ORDER BY arr_cents DESC LIMIT 5')
  if st.button('Validate and run SQL'):
   con,_=run_pipeline()
   try:st.dataframe(execute_read_only(con,custom),hide_index=True,width='stretch')
   except Exception as exc:st.error('Query rejected or failed: '+str(exc))
   finally:con.close()
 st.caption('Guardrails: one SELECT; allowlisted marts and functions; no catalog/file/network access; isolated in-memory query connection; 100-row response cap; bounded memory and query timer. This prototype is not a multi-tenant production security boundary.')

st.divider();st.caption('Independent Flinn-role portfolio prototype by Abhishek Rahul. Not affiliated with Flinn. Source records are synthetic; financial policy and signals are illustrative.')
