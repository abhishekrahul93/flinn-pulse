"""Create a portable, credential-free copy; no Site identity or generated DBs."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist'/'Flinn_Pulse_Source.zip'
skip={'.git','.openai','.venv','target','logs','__pycache__','dbt_packages'}
with ZipFile(OUT,'w',ZIP_DEFLATED) as z:
 for p in sorted(ROOT.rglob('*')):
  rel=p.relative_to(ROOT)
  if not p.is_file() or any(x in skip for x in rel.parts):continue
  if p==OUT or p.suffix in {'.duckdb','.wal','.pyc'}:continue
  z.write(p,Path('Flinn_Pulse')/rel)
print('Source archive:',OUT.stat().st_size,'bytes')
