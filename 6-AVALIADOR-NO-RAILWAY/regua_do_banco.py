# -*- coding: utf-8 -*-
"""
A REGUA VEM DO BANCO — nao de arquivo, nao de constante.

Regra do Luis, 25/08: existe UM dono da regra. Ela estava escrita em tres lugares
(JSON na maquina, tabela no banco, JavaScript na tela) e nenhum mandava nos outros.
Aqui o banco manda.

SEM DEFAULT SILENCIOSO: se um insumo faltar, isto levanta ReguaIncompleta e diz o
nome do que faltou. Nunca assume zero, nunca assume "o de sempre".
"""

class ReguaIncompleta(Exception):
    pass


class Regua:
    ESPERADO = {
        'parametro'    : 7,
        'atributo'     : 26,
        'barra'        : 10,
        'custo_nivel'  : 25,
        'multiplicador': 100,
        'ordem_boost'  : 26,
    }
    _ATRIB = {'parametro':'p','atributo':'attr','barra':'barra','custo_nivel':'custo',
              'multiplicador':'mult','ordem_boost':'ordem_boost'}

    def __init__(self, dados, versao_molde):
        self.versao_molde = versao_molde
        self.p           = dados['parametro']
        self.attr        = dados['atributo']
        self.barra       = dados['barra']
        self.custo       = dados['custo_nivel']
        self.mult        = dados['multiplicador']
        self.ordem_boost = dados['ordem_boost']
        self.molde       = dados['molde']        # {funcao: {idx: (alvo, peso)}}
        self.hab         = dados['habilidade']   # {nome: {'tipo':.., 'efeito':{idx:{pct|flat}}}}
        self.tec         = dados['tecnico']      # {id: {'boosts':[idx], 'proficiencia': n}}
        self.imp         = dados['impeto']       # {impeto_id: {idx: delta}}
        self._confere()

    def _confere(self):
        faltou = []
        for nome, quanto in self.ESPERADO.items():
            tem = len(getattr(self, self._ATRIB[nome]))
            if tem != quanto:
                faltou.append('%s: esperado %d, veio %d' % (nome, quanto, tem))
        if not self.molde:
            faltou.append('molde: nenhuma funcao')
        if faltou:
            raise ReguaIncompleta('A regua veio incompleta do banco -> ' + ' | '.join(faltou))

    @property
    def degraus(self):      return self.p['degraus_acima_do_alvo']
    @property
    def teto_punicao(self): return int(self.p['teto_da_punicao'])
    @property
    def punicao(self):      return self.p['formula_da_punicao']
    @property
    def vmax(self):         return int(self.p['valor_maximo_indexavel'])

    def alvo_peso(self, funcao_codigo, idx):
        m = self.molde.get(funcao_codigo)
        if m is None:
            raise ReguaIncompleta('molde ausente para a funcao %r' % funcao_codigo)
        v = m.get(idx)
        if v is None:
            raise ReguaIncompleta('molde da funcao %r sem o atributo %d' % (funcao_codigo, idx))
        return v

    def molde_completo(self, funcao_codigo):
        m = self.molde.get(funcao_codigo)
        if not m:
            raise ReguaIncompleta('molde ausente para a funcao %r' % funcao_codigo)
        faltam = [i for i in range(len(self.attr)) if i not in m]
        if faltam:
            raise ReguaIncompleta('molde da funcao %r incompleto: faltam os atributos %s'
                                  % (funcao_codigo, faltam))
        return True


# ---------------------------------------------------------------- carregamento
SQL = {
 'versao_molde' : "select max(versao) v from clube.molde",
 'parametro'    : "select chave, valor from clube.regua_parametro",
 'atributo'     : "select idx, nome from clube.atributo",
 'barra'        : "select barra, attr from clube.barra",
 'custo_nivel'  : "select nivel, acumulado from clube.custo_nivel",
 'multiplicador': "select ponto, multiplicador from clube.multiplicador",
 'ordem_boost'  : "select pos_na_lista, atributo_idx from clube.ordem_boost_tecnico",
 'molde'        : "select funcao_codigo, atributo_idx, alvo, peso from clube.molde "
                  "where versao = (select max(versao) from clube.molde)",
 'habilidade'   : "select nome, tipo, efeito from clube.habilidade",
 'tecnico'      : "select id, boosts, extras from clube.tecnico",
 'impeto'       : "select impeto_id, atributo_idx, delta from clube.impeto_efeito",
}


def carrega_de(fonte, tatica=None):
    """`fonte` recebe SQL e devolve lista de dicionarios. O mesmo codigo serve para
    o servico, para o motor offline e para o teste.

    `tatica`: a proficiencia do tecnico e a DA TATICA JOGADA. Sem tatica cravada,
    usa o maximo — o mesmo comportamento do motor hoje (equacao.py:carrega_tecnicos)."""
    d = {}
    d['parametro']     = {r['chave']: r['valor'] for r in fonte(SQL['parametro'])}
    d['atributo']      = {int(r['idx']): r['nome'] for r in fonte(SQL['atributo'])}
    d['custo_nivel']   = {int(r['nivel']): int(r['acumulado']) for r in fonte(SQL['custo_nivel'])}
    d['multiplicador'] = {int(r['ponto']): float(r['multiplicador'])
                          for r in fonte(SQL['multiplicador'])}

    ordem = {int(r['pos_na_lista']): int(r['atributo_idx']) for r in fonte(SQL['ordem_boost'])}
    d['ordem_boost'] = ordem

    barras = {}
    for r in fonte(SQL['barra']):
        barras.setdefault(r['barra'], []).append(int(r['attr']))
    d['barra'] = barras

    molde = {}
    for r in fonte(SQL['molde']):
        molde.setdefault(r['funcao_codigo'], {})[int(r['atributo_idx'])] = \
            (float(r['alvo']), int(r['peso']))
    d['molde'] = molde

    d['habilidade'] = {r['nome']: {'tipo': r['tipo'], 'efeito': r['efeito'] or {}}
                       for r in fonte(SQL['habilidade'])}

    tec = {}
    for r in fonte(SQL['tecnico']):
        ex = r['extras'] or {}
        prof = (ex.get('proficiencias') or {})
        if tatica and tatica in prof:
            v = prof[tatica]
        elif prof:
            v = max(prof.values())
        else:
            v = None
        boosts = []
        for b in (r['boosts'] or []):
            b = int(b)
            if b in ordem:
                boosts.append(ordem[b])
            else:
                raise ReguaIncompleta('tecnico %s tem boost %d fora da ordem do efHub'
                                      % (r['id'], b))
        tec[int(r['id'])] = {'boosts': boosts, 'proficiencia': v}
    d['tecnico'] = tec

    imp = {}
    for r in fonte(SQL['impeto']):
        imp.setdefault(int(r['impeto_id']), {})[int(r['atributo_idx'])] = int(r['delta'])
    d['impeto'] = imp

    versao = fonte(SQL['versao_molde'])[0]['v']
    return Regua(d, versao)
