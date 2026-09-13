from pathlib import Path
import tempfile,sys
sys.path.insert(0,r'C:/Users/Luis Fernando/Downloads/ClubEFootball--main/ClubEFootball--main/2-MOTORES/OTIMIZADOR')
from complemento_contexto_v14 import ler_config
with tempfile.TemporaryDirectory() as tmp:
 base=Path(tmp)/'2-MOTORES';root=base/'OTIMIZADOR';app=root/'COMPLEMENTO-LOCAL-V14';app.mkdir(parents=True)
 for p in [base/'config.txt',root/'config.txt',root/'OPERACAO-LOCAL-JSON/config.txt',app/'config.txt']:
  p.parent.mkdir(parents=True,exist_ok=True);p.write_text('SUPABASE_URL=[https://trqqpsnafpbudtvvicch.supabase.co]\nSUPABASE_KEY=teste-local-sem-acesso\n',encoding='utf-8-sig')
  assert ler_config(root,app)==('https://trqqpsnafpbudtvvicch.supabase.co','teste-local-sem-acesso');p.unlink()
 (base/'config.txt').write_text('SUPABASE_URL=https://outro.supabase.co\nSUPABASE_KEY=teste\n')
 try:ler_config(root,app)
 except RuntimeError as e:assert 'Projeto diferente' in str(e)
 else:raise AssertionError('Projeto errado aceito')
print('Quatro caminhos de configuracao aprovados; projeto incorreto bloqueado; nenhuma rede usada.')
