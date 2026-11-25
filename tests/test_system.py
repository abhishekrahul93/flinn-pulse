"""Business invariants, source defects, read-only boundary and action state tests."""
import tempfile,unittest
from unittest.mock import patch
from pathlib import Path
from warehouse.pipeline import run_pipeline,get_frames
from data.generate_data import generate_data
from automations.copilot import EXAMPLES,answer_question,validate_sql,execute_read_only,build_alerts,transition

class PulseTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.con,cls.checks=run_pipeline();cls.frames=get_frames(cls.con)
 @classmethod
 def tearDownClass(cls):cls.con.close()
 def test_expected_source_defects(self):
  counts={c['name']:c['failing_rows'] for c in self.checks}
  self.assertEqual(counts['Raw duplicate renewal records'],2)
  self.assertEqual(counts['Closed-won deal close date'],1)
  self.assertEqual(counts['CRM / Finance ARR reconciliation'],3)
  self.assertEqual(counts['Governed event names'],1)
  self.assertEqual(sum(c['status']=='PASS' for c in self.checks),8)
 def test_account_and_feature_grains(self):
  self.assertEqual(len(self.frames['mart_arr_truth']),25)
  self.assertEqual(len(self.frames['stg_hubspot_deals']),25)
  self.assertEqual(len(self.frames['mart_feature_adoption']),24*5)
 def test_no_revenue_double_counting(self):
  a=self.frames['mart_arr_truth'];self.assertEqual(int(a.arr_cents.sum()),196320000)
  self.assertEqual(int(a.previous_arr_cents.sum()+a.delta_arr_cents.sum()),int(a.arr_cents.sum()))
 def test_all_supported_questions_execute(self):
  for q in EXAMPLES:
   with self.subTest(question=q):self.assertIsNotNone(answer_question(self.con,q)['data'])
 def test_unsupported_question_is_explicit(self):
  self.assertIsNone(answer_question(self.con,'Who will win the football game?')['data'])
 def test_provider_errors_fall_back(self):
  with patch('automations.copilot.provider_sql',side_effect=TimeoutError('offline')):
   result=answer_question(self.con,EXAMPLES[0],use_provider=True)
   self.assertEqual(result['mode'],'Deterministic')
   self.assertEqual(float(result['data'].iloc[0].finance_arr_eur),1963200)
 def test_unsafe_provider_sql_falls_back(self):
  with patch('automations.copilot.provider_sql',return_value=('DROP TABLE mart_arr_truth','test')):
   self.assertEqual(answer_question(self.con,EXAMPLES[0],True)['mode'],'Deterministic')
 def test_unsafe_queries_blocked(self):
  bad=['DROP TABLE mart_arr_truth','SELECT 1; DELETE FROM mart_arr_truth',"SELECT * FROM read_csv('/etc/passwd')",'SELECT * FROM information_schema.tables','SELECT * FROM hubspot_deals',"SELECT getenv('OPENAI_API_KEY')",'ATTACH database pulse','SELECT * FROM duckdb_settings()','SELECT * FROM mart_arr_truth UNION ALL SELECT * FROM read_parquet(\'https://example.com/data\')','SELECT * FROM range(1000000000)']
  for sql in bad:
   with self.subTest(sql=sql),self.assertRaises(ValueError):validate_sql(sql)
 def test_result_cap_and_readonly_cte(self):
  sql='WITH x AS (SELECT * FROM mart_feature_adoption) SELECT * FROM x'
  self.assertEqual(len(execute_read_only(self.con,sql)),100)
 def test_sql_failure_does_not_modify_source(self):
  with self.assertRaises(ValueError):execute_read_only(self.con,'DELETE FROM mart_arr_truth')
  self.assertEqual(self.con.execute('select count(*) from mart_arr_truth').fetchone()[0],25)
 def test_risk_and_feature_signals(self):
  a=build_alerts(self.frames['mart_arr_truth'],self.frames['mart_feature_adoption'])
  self.assertEqual(sum(x['rule']=='renewal_usage_risk' for x in a),4)
  self.assertEqual(sum(x['rule']=='feature_underadoption' for x in a),1)
  self.assertEqual(len({x['event_id'] for x in a}),len(a))
 def test_approval_and_idempotency(self):
  ledger={};self.assertEqual(transition(ledger,'id','record'),'invalid_transition')
  self.assertEqual(transition(ledger,'id','approve'),'approved')
  self.assertEqual(transition(ledger,'id','record'),'recorded')
  self.assertEqual(transition(ledger,'id','record'),'duplicate_skipped')
 def test_generation_is_deterministic(self):
  with tempfile.TemporaryDirectory() as d:
   files=generate_data(d,True);before={n:p.read_bytes() for n,p in files.items()};generate_data(d,True)
   self.assertEqual(before,{n:p.read_bytes() for n,p in files.items()})
if __name__=='__main__':unittest.main()
