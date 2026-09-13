"""Altura por função, sem redistribuir parcelas físicas (09/09/2026).

Funções puras. Não consulta banco, não escreve resultados e não ativa política.
O chamador deve fornecer a parcela-base V10/V12, nunca uma parcela já migrada.
"""
from decimal import Decimal

VERSAO = 'altura-independente-20260909-v1'
ATIVAS = frozenset((1, 4, 5, 6, 17, 18, 19))
INVERTIDAS = frozenset((4, 6))


def separar_altura(detalhe, funcao_id, aplicar_regra=False):
    """Preserva exatamente os onze itens restantes e soma sem arredondá-los.

    aplicar_regra=False é a etapa estrutural, sem mudança numérica.
    True aplica as sete funções e inverte 4/6 em relação à base preservada.
    """
    if not isinstance(detalhe, dict) or len(detalhe) != 12 or 'altura' not in detalhe:
        raise ValueError('Detalhe físico completo com 12 parcelas é obrigatório')
    f = int(funcao_id)
    if f not in range(1, 20):
        raise ValueError('Função não cadastrada na política de altura')
    valores = {k: Decimal(str(v)) for k, v in detalhe.items()}
    if any(not v.is_finite() for v in valores.values()):
        raise ValueError('Parcela física não finita')
    antiga = valores['altura']
    nova = antiga
    if aplicar_regra:
        nova = -antiga if f in INVERTIDAS else antiga if f in ATIVAS else Decimal(0)
    outros = sum((v for k, v in valores.items() if k != 'altura'), Decimal(0))
    novo_detalhe = dict(detalhe)
    novo_detalhe['altura'] = nova
    return {'politica': VERSAO, 'altura_anterior': antiga, 'altura': nova,
            'restante_corpo': outros, 'total': outros + nova, 'detalhe': novo_detalhe,
            'delta': nova - antiga}
