# -*- coding: utf-8 -*-
"""
TRAVAS — o portão do motor. Nada roda sem passar por aqui.

Achado CRÍTICO 6 da auditoria dos motores (25/08):
    "Nenhum assert, raise ou gate em 957 linhas."

O motor rodava com carta incompleta, com molde furado e com régua faltando —
e o resultado saía com cara de certo. Foi assim que 1.342 builds de 356 cartas
foram calculadas com insumo faltando, e ninguém viu.

COMO USAR — uma linha, no começo da rodada:

    from travas import portao
    portao(cartas, molde, regua)      # levanta MotorTravado e diz o que falta

⛔ A trava NUNCA conserta e NUNCA preenche. Ela só para e diz o nome do que
   faltou. Quem decide o que fazer é o Luis.
"""


class MotorTravado(Exception):
    """O motor não rodou de propósito. A mensagem diz exatamente o que falta."""


def _erro(lista):
    if lista:
        raise MotorTravado('O MOTOR NAO RODOU. Falta:\n  - ' + '\n  - '.join(lista))


def confere_regua(regua, precisa=('degraus_acima_do_alvo', 'teto_da_punicao',
                                  'formula_da_punicao', 'valor_maximo_indexavel',
                                  'metade_da_habilidade_perdedora')):
    """A régua está inteira? Sem ela a nota sai errada e parece certa."""
    faltou = [('regua sem ' + c) for c in precisa if c not in (regua or {})]
    _erro(faltou)
    return True


def confere_molde(molde, funcoes, n_atributos=26):
    """Toda função tem os 26 atributos? Molde furado = alvo inventado."""
    faltou = []
    for f in funcoes:
        m = (molde or {}).get(f)
        if not m:
            faltou.append('molde da funcao ' + str(f))
            continue
        vazios = [i for i in range(n_atributos) if i not in m]
        if vazios:
            faltou.append('molde da funcao %s sem os atributos %s' % (f, vazios))
    _erro(faltou)
    return True


def confere_carta(c, n_atributos=26):
    """Um card só entra se tiver o que a conta usa. Devolve a lista do que falta
    — vazia quer dizer que pode rodar."""
    falta = []
    base = c.get('base')
    if not base:
        falta.append('os %d atributos' % n_atributos)
    elif len(base) != n_atributos:
        falta.append('tem %d atributos, deviam ser %d' % (len(base), n_atributos))
    elif any(x is None for x in base):
        falta.append('atributo em branco no meio dos %d' % n_atributos)
    if c.get('orc') is None:
        falta.append('o orcamento de barras')
    if c.get('arows') is None:
        falta.append('o molde da funcao')
    return falta


def portao(cartas, molde, regua, funcoes=None, parar_na_primeira=False):
    """O portão. Confere régua, molde e TODAS as cartas antes de a rodada começar.

    Devolve a lista de (card_id, o que falta) das cartas reprovadas.
    Se `parar_na_primeira`, levanta MotorTravado na primeira carta furada —
    útil na rodada única, onde uma carta errada contamina o ranking inteiro."""
    confere_regua(regua)
    if funcoes:
        confere_molde(molde, funcoes)

    reprovadas = []
    for c in (cartas or []):
        falta = confere_carta(c)
        if falta:
            quem = c.get('id') or c.get('card_id') or '?'
            reprovadas.append((quem, falta))
            if parar_na_primeira:
                raise MotorTravado('A carta %s nao pode rodar. Falta: %s'
                                   % (quem, ', '.join(falta)))
    return reprovadas


def relatorio(reprovadas):
    """O texto que vai para a tela do Luis quando alguma carta é barrada."""
    if not reprovadas:
        return 'PORTAO: todas as cartas passaram.'
    linhas = ['PORTAO: %d cartas ficaram de fora (nenhuma delas entrou na conta):'
              % len(reprovadas)]
    for quem, falta in reprovadas[:20]:
        linhas.append('  %s — falta %s' % (quem, ', '.join(falta)))
    if len(reprovadas) > 20:
        linhas.append('  ... e mais %d' % (len(reprovadas) - 20))
    return '\n'.join(linhas)
