from pathlib import Path
import sys,json,copy
base=Path.cwd(); sys.path.insert(0,r'C:/Users/Luis Fernando/Downloads/ClubEFootball--main/ClubEFootball--main/2-MOTORES/OTIMIZADOR')
from complemento_recomposicao_v14 import preparar
from complemento_contexto_v14 import por_funcao
from complemento_solucao_v14 import aplicar
ctx=json.loads((base/'work/teste-exe-complemento/contexto.json').read_text())
r=preparar(json.loads((base/'work/teste-exe-complemento/regua.json').read_text()))
import fonte_unica
rows=json.loads((base/'work/teste-exe-complemento/FILA/pagina-000001.json').read_text())+json.loads((base/'work/complemento-cas-elegivel.json').read_text())
for row in rows:
 l=row['linha'];o=row['anterior'];m=r._W['M']; c=fonte_unica.aplica_impetos_da_linha(r.carrega_carta_snapshot_producao_v3(row['carta']),l['impeto_condicional_codigo'],l['impeto_condicional_nivel']);c['arows']=copy.deepcopy(r._W['MOLDE'][l['funcao_id']])
 t=next(t for t in r._W['TECS'] if t['id']==o['tecnico_id']);cd=m.Card(c,m=t['m']);imp=list(cd.nm)
 if o['impeto_adicional_codigo'] is not None:
  extra=next(x[0] for x in m._cands_impeto(cd) if x[1]==o['impeto_adicional_codigo']);imp=[a+b for a,b in zip(imp,extra)]
 boost=[0]*26
 for i in t['boost']:boost[i]+=1
 sol=dict(habilidades=o['habilidades_adicionais'],nota=o['pontuacao'],m=t['m'],lvl=o['barras'],impeto_add=imp,boost_add=boost)
 res=aplicar(m,c,sol,funcao_id=l['funcao_id'],**por_funcao(ctx,l['funcao_id']))
 path=base/('work/complemento-ca-'+str(l['id'])+'.json') if l['id']==34628 else base/'outputs/auditoria-habilidades-essenciais-1009/golden-complemento-v14-resultado.json'
 esperado=json.loads(path.read_text())
 assert res['habilidades']==esperado['habilidades'];assert res['vals']==esperado['vals'];assert res['nota']==esperado['b1'];assert sol['habilidades']==o['habilidades_adicionais']
 print('Runtime e corretor iguais:',l['id'],res['habilidades_complementares'])
 c['dimensoes_ids']['tipo_fisico']=4
 assert aplicar(m,c,sol,funcao_id=l['funcao_id'],**por_funcao(ctx,l['funcao_id']))['habilidades_complementares']==[]
print('Tipos inelegiveis bloqueados no runtime')
