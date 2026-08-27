# -*- coding: utf-8 -*-
"""
===============================================================================
  A EXCECAO DE HOJE — a que se desfaz sozinha
===============================================================================

  ORDEM DO LUIS, 18/08:
    "Como e que a gente vai fazer pro sistema ser uma excecao e na proxima
     rodada ele voltar ao normal? SEM A GENTE ESQUECER DISSO."

  ⛔ O PROBLEMA COM EXCECAO: ela e feita as pressas e desfeita nunca. Quem
     desliga um interruptor para "so hoje" nao esta la amanha para religar, e
     seis meses depois ninguem sabe mais por que aquilo esta desligado. Foi
     assim que o `VOLTAR-PARA-A-FILA.txt` ficou desligado por dias.

  ⛔ ELA NAO MEXE EM INTERRUPTOR NENHUM — e essa e a 2a versao, de 18/08.
     A 1a versao APAGAVA o LIGAR-MOTOR-AUTOMATICO.txt e repunha depois. Dois
     defeitos: mexia em arquivo que nao e dela, e se algo desse errado no meio
     o interruptor sumia sem dono. Agora a excecao so DECLARA, num arquivo so:

         EXCECAO-DE-HOJE.json  ->  { "vale_no_dia": "...",
                                     "nao_chamar_o_motor": true }

     Quem le e a rodada. Nenhum outro arquivo e tocado, entao nao ha o que
     repor: no dia seguinte a excecao simplesmente deixa de valer.

  COMO SE USA
     ligar     -> escreve a declaracao com a data de hoje
     conferir  -> (a rodada chama sozinha, no comeco) arquiva se venceu
     vale()    -> a rodada pergunta: esta excecao vale agora?
     ver       -> so mostra o estado, nao mexe em nada
===============================================================================
"""
import io
import json
import os
import sys
from datetime import datetime

AQUI = os.path.dirname(os.path.abspath(__file__))


def acha_a_pasta_do_sistema(inicio):
    p = inicio
    for _ in range(4):
        if os.path.exists(os.path.join(p, 'config.txt')):
            return p
        pai = os.path.dirname(p)
        if pai == p:
            break
        p = pai
    return None


CASA = acha_a_pasta_do_sistema(AQUI)
if not CASA:
    print('nao achei o config.txt subindo a partir de %s' % AQUI)
    raise SystemExit(1)
os.chdir(CASA)

RECIBO = 'EXCECAO-DE-HOJE.json'

# o que uma excecao pode declarar, e o que cada coisa significa
DESVIOS = {
    'nao_chamar_o_motor':
        'a rodada faz TUDO e nao chama o motor. A fila fica pronta esperando, '
        'e quem roda o motor e o SO-O-MOTOR.bat, depois que a rodada terminar.',
}


def hoje():
    return datetime.now().date().isoformat()


def le():
    if not os.path.exists(RECIBO):
        return None
    try:
        return json.load(io.open(RECIBO, encoding='utf-8'))
    except Exception:
        return None


def vale(desvio):
    """A rodada pergunta aqui. Devolve True so se a excecao e DE HOJE."""
    r = le()
    if not r:
        return False
    if r.get('vale_no_dia') != hoje():
        return False
    return bool(r.get(desvio))


def ligar(por_que, desvios):
    r = le()
    if r and r.get('vale_no_dia') == hoje():
        print('  Ja existe uma excecao de hoje. Nao mexi.')
        mostra(r)
        return 0
    d = {'o_que_e': ('a excecao vale SO no dia gravado aqui. A rodada pergunta a data '
                     'antes de obedecer; no dia seguinte ela arquiva isto sozinha.'),
         'vale_no_dia': hoje(),
         'por_que': por_que}
    for k in desvios:
        d[k] = True
    json.dump(d, io.open(RECIBO, 'w', encoding='utf-8', newline=''),
              ensure_ascii=False, indent=1)
    print('  EXCECAO LIGADA para o dia %s.' % hoje())
    mostra(d)
    print()
    print('  Nenhum interruptor foi tocado. Ela vale so hoje, pela data.')
    return 0


def mostra(r):
    print('  %s' % (r.get('por_que') or ''))
    for k, oque in DESVIOS.items():
        if r.get(k):
            print('     %-22s %s' % (k, oque))


def conferir():
    r = le()
    if not r:
        return 0
    dia = r.get('vale_no_dia')
    if dia == hoje():
        print()
        print('=' * 68)
        print('  ⚠️ EXCECAO LIGADA — vale so hoje (%s)' % dia)
        print('=' * 68)
        mostra(r)
        print()
        print('  Amanha ela deixa de valer sozinha. Ninguem precisa lembrar.')
        return 0
    try:
        os.replace(RECIBO, RECIBO + '.DESFEITA-EM-' + hoje())
    except Exception:
        try:
            os.remove(RECIBO)
        except Exception:
            pass
    print()
    print('=' * 68)
    print('  ✅ A EXCECAO DE %s ACABOU — o sistema esta no desenho normal' % dia)
    print('=' * 68)
    mostra(r)
    print()
    print('  Nada precisou ser reposto: ela nunca mexeu em interruptor nenhum.')
    return 0


if __name__ == '__main__':
    cmd = (sys.argv[1] if len(sys.argv) > 1 else 'ver').lower()
    if cmd == 'ligar':
        raise SystemExit(ligar(
            'hoje a rodada nao chama o motor: ele roda depois, com tudo numa lista so',
            ['nao_chamar_o_motor']))
    if cmd == 'conferir':
        raise SystemExit(conferir())
    r = le()
    if not r:
        print('  Nenhuma excecao ligada. O sistema esta no desenho normal.')
    elif r.get('vale_no_dia') == hoje():
        print('  Excecao VALENDO hoje (%s).' % hoje())
        mostra(r)
    else:
        print('  Ha uma excecao do dia %s, e hoje e %s — ela ja nao vale.' %
              (r.get('vale_no_dia'), hoje()))
        print('  A proxima rodada arquiva ela sozinha.')
