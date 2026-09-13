from pathlib import Path
import ast,contextlib,io,json,os,tempfile,urllib.error,urllib.request
R=Path(__file__).resolve().parents[3]
F=R/'2-MOTORES/BONIFICADOR/motor_bonus.py'
regua=json.loads(Path(__file__).with_name('fixture_estilos_v12.json').read_text(encoding='utf-8'))['regua']
regua['pode_rodar']=True
regua['liberado_para_producao']=True
ctx={'build_linha_card_id':488143,'card_id':'8557147','funcao_id':1,'funcao_codigo':'CA','posicao_id':12,
     'carta_versao':'teste','carta_fingerprint':'a'*64,'contrato_versao':regua['contrato'],
     'contrato_fingerprint':regua['contrato_fingerprint'],'formula_fingerprint':regua['formula_fingerprint']}
tests=[]
for scenario in ('403','sem_reserva_com_falha','concluido'):
    calls=[]
    def rpc_fake(nome,corpo=None,timeout=60):
        calls.append(nome)
        if nome=='bonificador_regua_v4':return json.loads(json.dumps(regua))
        if nome=='bonificador_correcao_proxima_linha_v2':return dict(ctx) if scenario=='403' else None
        if nome=='bonificador_carta_v3':raise urllib.error.HTTPError('https://teste.invalid',403,'Forbidden',{},None)
        if nome=='bonificador_correcao_registrar_v1':return {'ok':True}
        if nome=='bonificador_correcao_status_v1':return {'ok':True,'contagens':{'pendente':14106,'falha':1} if scenario=='sem_reserva_com_falha' else {'preparado':178528}}
        raise AssertionError('Chamada inesperada: '+nome)
    tree=ast.parse(F.read_text(encoding='utf-8'))
    for i,n in enumerate(tree.body):
        if isinstance(n,ast.FunctionDef) and n.name=='rpc':tree.body[i]=ast.parse('rpc=rpc_fake').body[0]
    ast.fix_missing_locations(tree)
    before=os.getcwd();oldenv=dict(os.environ)
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);(tmp/'config.txt').write_text('SUPABASE_URL=https://teste.invalid\nSUPABASE_KEY=teste\n')
        os.environ['CLUBEF_BONIFICADOR_CONFIG']=str(tmp/'config.txt')
        os.environ['CLUBEF_BONIFICADOR_CORRECAO_LOTE_ID']='0ddaa775-24c1-4293-86ca-77fe698aa044'
        os.environ['_CLUBEF_BONIFICADOR_RODADA_INTERNA']='1'
        scope={'__file__':str(tmp/'motor_bonus.py'),'__name__':'teste_rodada','rpc_fake':rpc_fake}
        code=0;log=io.StringIO()
        try:
            with contextlib.redirect_stdout(log):exec(compile(tree,str(F),'exec'),scope)
        except SystemExit as e:code=e.code or 0
        finally:os.chdir(before);os.environ.clear();os.environ.update(oldenv)
        expected=0 if scenario=='concluido' else 2
        assert code==expected,(scenario,code,log.getvalue())
        assert not any(n.startswith('gravar_') for n in calls)
        if code:assert 'PRONTO.' not in log.getvalue() and 'CONCLUIDO:' not in log.getvalue()
        tests.append({'caso':scenario,'codigo':code,'gravacoes':0})

print(json.dumps(tests))
