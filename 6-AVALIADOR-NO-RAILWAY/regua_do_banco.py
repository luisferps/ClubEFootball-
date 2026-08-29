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
        'parametro'    : 8,
        'atributo'     : 26,
        'barra'        : 10,
        'custo_nivel'  : 25,
        'multiplicador': 100,
    }
    _ATRIB = {'parametro':'p','atributo':'attr','barra':'barra','custo_nivel':'custo',
              'multiplicador':'mult'}

    def __init__(self, dados, versao_molde):
        self.versao_molde = versao_molde
        self.p           = dados['parametro']
        self.attr        = dados['atributo']
        self.barra       = dados['barra']
        self.custo       = dados['custo_nivel']
        self.mult        = dados['multiplicador']
        self.molde       = dados['molde']        # {funcao_id: {idx: (alvo, peso)}}
        self.hab         = dados['habilidade']   # {skill_id: {'fabricavel':..,'efeito':..}}
        self.tec         = dados['tecnico']      # {id: {'boosts':[idx], 'proficiencia': n}}
        self.imp         = dados['impeto']       # vazio enquanto o consumidor estiver desligado
        self.funcoes     = dados.get('funcoes') or {}
        self.skill_names = dados.get('skill_names') or {}
        self.gate        = dados.get('gate') or {}
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

    def alvo_peso(self, funcao_id, idx):
        m = self.molde.get(int(funcao_id))
        if m is None:
            raise ReguaIncompleta('molde ausente para a funcao_id %r' % funcao_id)
        v = m.get(idx)
        if v is None:
            raise ReguaIncompleta('molde da funcao_id %r sem o atributo %d' % (funcao_id, idx))
        return v

    def molde_completo(self, funcao_id):
        m = self.molde.get(int(funcao_id))
        if not m:
            raise ReguaIncompleta('molde ausente para a funcao_id %r' % funcao_id)
        faltam = [i for i in range(len(self.attr)) if i not in m]
        if faltam:
            raise ReguaIncompleta('molde da funcao %r incompleto: faltam os atributos %s'
                                  % (funcao_id, faltam))
        return True

