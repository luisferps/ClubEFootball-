from pathlib import Path
import json,hashlib,urllib.request
root=Path(r'C:/Users/Luis Fernando/Downloads/ClubEFootball--main/ClubEFootball--main')
pkg=Path('outputs/ATUALIZACAO-COMPLEMENTO-V14');fixture=Path('work/teste-instalacao-complemento/OTIMIZADOR')
for rel in ['OPERACAO-LOCAL-JSON/config.txt','OPERACAO-LOCAL-JSON/FILA-ATIVA.json','OPERACAO-LOCAL-JSON/RESULTADOS-JSON/sentinela.json']: assert (fixture/rel).read_text()=='PRESERVAR'
for x in json.loads((pkg/'manifesto.json').read_text()): assert hashlib.sha256((fixture/x['arquivo']).read_bytes()).hexdigest()==x['sha256']
for n in ['ficha.js','ficha.css','ficha-editor-api.js','ficha.html']:
 with urllib.request.urlopen('https://imaginative-granita-ace1ca.netlify.app/'+n+'?v=20260910-complemento-v14') as r: data=r.read()
 assert data==(Path('work/deploy-complemento-v14')/n).read_bytes(),n
print('Instalacao isolada: 15 arquivos conferidos; filas/config/resultados preservados. Netlify: 4 arquivos iguais ao pacote.')
