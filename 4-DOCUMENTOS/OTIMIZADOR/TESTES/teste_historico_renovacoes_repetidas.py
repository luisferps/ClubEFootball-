"""Mesmo nome em renovações repetidas não pode apagar ou bloquear históricos."""
import sys,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'2-MOTORES/OTIMIZADOR/OPERACAO-LOCAL-JSON/programas'))
import operacao_local_json as api

class HistoricoRepetido(unittest.TestCase):
 def test_colisao_antiga_repeticao_e_recibos_preservados(self):
  with tempfile.TemporaryDirectory() as d:
   estrutura=api.garantir_estrutura(Path(d))
   pacote=SimpleNamespace(lote_id='lote',manifesto=dict(lote_fingerprint='lote-novo',formula_fingerprint='formula',contrato_fingerprint='contrato-novo'))
   antigo=estrutura['historico_renovacoes']/'lote-novo'/'PENDENTES'/'resultado-000001.json'
   antigo.parent.mkdir(parents=True)
   antigo.write_bytes(b'historico existente intocavel')
   for rodada in [1,2]:
    item={'linha_id':10,'calculado_em_utc':'2026-09-08T00:00:00Z','resultado':{'b1':rodada,'barras':{},'tecnico_id':1,'habilidades':[],'builds_comparadas':1,'builds_possiveis':1,'lote_fingerprint':'lote-anterior','formula_fingerprint':'formula','contrato_fingerprint':f'antigo-{rodada}'}}
    caminho=estrutura['pendentes']/'resultado-000001.json'
    envelope={'contrato':api.CONTRATO_RESULTADO,'versao':1,'lote_id':'lote','sequencia':1,'itens':[item]}
    api.gravar_json_atomico(caminho,envelope)
    recibo=estrutura['recibos']/'resultado-000001.recibos.jsonl'
    recibo.write_text(f'recibo-{rodada}',encoding='utf-8')
    resultado=api.reconciliar_historico_renovado(estrutura,pacote)
    self.assertEqual(1,resultado['arquivos_historicos_movidos'])
    destino=Path(d)/resultado['historico_relativo']
    self.assertEqual(envelope,api.ler_json(destino/'PENDENTES'/caminho.name))
    self.assertEqual(f'recibo-{rodada}',(destino/'RECIBOS'/recibo.name).read_text())
    self.assertFalse(caminho.exists())
   self.assertEqual(b'historico existente intocavel',antigo.read_bytes())
   self.assertEqual(3,len(list(estrutura['historico_renovacoes'].rglob('resultado-000001.json'))))
   self.assertEqual(0,api.reconciliar_historico_renovado(estrutura,pacote)['arquivos_historicos_movidos'])

 def test_resultado_atual_permanece_no_lugar(self):
  with tempfile.TemporaryDirectory() as d:
   estrutura=api.garantir_estrutura(Path(d))
   selos=dict(lote_fingerprint='lote',formula_fingerprint='formula',contrato_fingerprint='contrato')
   pacote=SimpleNamespace(lote_id='lote',manifesto=selos)
   item={'linha_id':10,'calculado_em_utc':'2026-09-08T00:00:00Z','resultado':dict(selos,b1=1,barras={},tecnico_id=1,habilidades=[],builds_comparadas=1,builds_possiveis=1)}
   caminho=estrutura['pendentes']/'resultado-000001.json'
   api.gravar_json_atomico(caminho,{'contrato':api.CONTRATO_RESULTADO,'versao':1,'lote_id':'lote','sequencia':1,'itens':[item]})
   antes=caminho.read_bytes()
   self.assertEqual(1,api.reconciliar_historico_renovado(estrutura,pacote)['arquivos_atuais_mantidos'])
   self.assertEqual(antes,caminho.read_bytes())

if __name__=='__main__':unittest.main()
