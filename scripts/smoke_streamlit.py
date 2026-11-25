"""Headless interaction checks for the full Python application."""
from pathlib import Path
from streamlit.testing.v1 import AppTest
root=Path(__file__).resolve().parents[1]
at=AppTest.from_file(str(root/'app.py'),default_timeout=30).run()
assert not at.exception,at.exception
next(s for s in at.selectbox if s.label=='Account tier').select('Mid-Market').run()
assert not at.exception
assert next(m for m in at.metric if m.label=='Finance reference ARR').value=='€432,000'
next(s for s in at.selectbox if s.label=='Account tier').select('All tiers').run()
next(b for b in at.button if b.label=='Answer question').click().run()
assert not at.exception
assert at.session_state['answer']['data'].iloc[0]['finance_arr_eur']==1963200
next(b for b in at.button if b.label=='Validate and run SQL').click().run()
assert not at.exception
print('Streamlit startup, tier filter, copilot execution and custom SELECT passed.')
