import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'executor'));sys.path.insert(0,str(ROOT/'executor'/'vendor'))
from impetos import validate_impetos
import psycopg
node=Path(r'C:\Users\Luis Fernando\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe')
p=subprocess.run([str(node),str(Path(__file__).with_name('gerar-snapshot-impetos.js'))],capture_output=True,text=True,check=True)
snapshot=json.loads(p.stdout)
c=psycopg.connect(host='db.trqqpsnafpbudtvvicch.supabase.co',dbname='postgres',user='postgres',password=os.environ['SUPABASE_DB_PASSWORD'],sslmode='require')
c.read_only=True
with c.cursor() as cur:
 cur.execute('show transaction_read_only');assert cur.fetchone()[0]=='on'
result=validate_impetos(snapshot,c);c.rollback();c.close()
print(json.dumps(result,ensure_ascii=False,indent=2))
if result['passed']: raise SystemExit(0)
raise SystemExit(2)
