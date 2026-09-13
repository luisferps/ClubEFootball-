"""Selecao pura do complemento aprovado em 10/09/2026.

Nao calcula efeitos, nao grava resultados e nao modifica a busca vencedora.
O chamador deve recompor os 26 atributos e a nota com o formatador oficial.
"""
from fractions import Fraction

VERSAO = 'complemento-nativo-10pct-20260910-v2'


def selecionar(*, funcao_id, nativas, adicionais, aceita_adicionais,
               catalogo, ranking, bloqueios, pesos_por_codigo):
    anteriores = list(adicionais)
    if len(anteriores) > 5 or len(set(anteriores)) != len(anteriores):
        raise ValueError('Lista de adicionais invalida')
    if set(anteriores) & set(nativas):
        raise ValueError('Adicional duplicada nas nativas')
    resultado = {'versao': VERSAO, 'habilidades': anteriores[:],
                 'complementares': [], 'motivos': {}}
    if not aceita_adicionais:
        return resultado
    presentes = set(nativas) | set(anteriores)

    def inserir(skill_id, motivo, excecao=False):
        h = catalogo.get(skill_id)
        if len(resultado['habilidades']) >= 5 or skill_id in presentes:
            return
        if not h or not h.get('fabricavel') or not h.get('pode_rodar'):
            return
        if skill_id in bloqueios or (h.get('vetada') and not excecao):
            return
        # Complemento considera utilidade propria da habilidade: gemeas podem
        # coexistir. A duplicidade proibida e somente do mesmo skill_id.
        if not h.get('efeito_por_codigo'):
            return
        presentes.add(skill_id)
        resultado['habilidades'].append(skill_id)
        resultado['complementares'].append(skill_id)
        resultado['motivos'][str(skill_id)] = motivo

    elegiveis = []
    vistos = set()
    for r in ranking:
        if int(r['funcao_id']) != int(funcao_id):
            continue
        sid = int(r['skill_id']); n = int(r['cartas_com']); total = int(r['cartas_total'])
        if sid in vistos or total < 0 or n < 0 or n > total:
            raise ValueError('Ranking nativo invalido')
        vistos.add(sid)
        if total and n * 10 >= total:
            elegiveis.append((Fraction(n, total), sid))
    for _, sid in sorted(elegiveis, key=lambda x: (-x[0], x[1])):
        # Os dois vetos globais continuam fora da etapa de incidencia.
        inserir(sid, 'incidencia_nativa_10pct')
    # Criterio aprovado: indispensavel (12) OU desejavel (7).
    # Penalti usa Finalizacao como criterio de utilidade; seu efeito continua
    # sendo Cobranca de bola parada. Nao confundir elegibilidade com efeito.
    for sid, codigos in ((69, ('PB:498:6', 'PB:530:6')), (48, ('PB:530:6',))):
        if all(pesos_por_codigo.get(c) in (7, 12) for c in codigos):
            inserir(sid, 'atributos_indispensaveis_ou_desejaveis', excecao=True)
    return resultado
