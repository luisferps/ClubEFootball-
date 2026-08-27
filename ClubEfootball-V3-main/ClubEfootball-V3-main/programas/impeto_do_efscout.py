# -*- coding: utf-8 -*-
"""
O IMPETO DE FABRICA, PELO efSCOUT — fecha a questao Pirlo x Varane (09/08/2026).

O FORMATO, decodificado nesta sessao:
   efscout_players.bin = 16 bytes de cabecalho + 39.524 registros de 92 bytes
   bytes 0..7 do registro ...... id numerico da Konami (u64), o MESMO que a gente usa
   bit 552, 11 bits ............ id do IMPETO DE FABRICA (0 = No Booster)
   o resto e bit-packed e nao foi decodificado — nao precisa

VALIDADO carta por carta:
   Pirlo 83 ....... No Booster            (nosso cadastro: vazio)      ✅
   MSN Messi 88 ... Magical +4  cor 3     (nosso: +4 em 4 atributos)   ✅
   Varane 87 ...... Rebuilding +3         (nosso: Reconstrucao +3)     ✅
   Bouaddi 85 ..... Offence Creator +3    (nosso: Criador de Jogadas)  ✅
   Gullit 89 ...... Strength +3           (nosso: Forca +3)            ✅
   Neuer 88 ....... Saving +3             (nosso: Defesaca +3)         ✅
   Bellingham 87 .. Striker's Instinct +2   <- a arte do efHub nao desenhava
   Cruyff 87 ...... Fantasista +2           <- idem

MEDIDO nos 2.589 cards da base: 88% de acordo com o nosso cadastro.
   os dois dizem QUE TEM ..... 1035      efscout TEM, nosso vazio ... 301
   os dois dizem QUE NAO ..... 1246      nosso TEM, efscout vazio ....  6

⚠️ O NUMERO DE VAGAS LIVRES NAO ESTA NESTE ARQUIVO. Foi procurado e nao existe campo.
   O que este script decide e SO uma coisa, e e a que estava em aberto:
   carta com impeto de fabrica NAO PODE ser de antes de o impeto existir, logo ela
   sai da trava da data. Carta com No Booster que esta na lista de datas: a trava
   fica, esta certa.
"""

# ===========================================================================
#  ⛔ 19/08 — ESTE PROGRAMA MORA NO ClubEfootball\programas.
#     "Nao existe mais essa pasta pro futebol. A pasta agora e ClubEfootball.
#      E tudo la." (Luis, 19/08)
#
#  ⛔ ESTE BLOCO VEM ANTES DOS IMPORTS, E POR MEDIDA. Quando ele ficava
#     DEPOIS, o `from equacao import ...` la de cima ja tinha rodado e pegava
#     o arquivo errado — o programa nem chegava a saber onde estava a casa.
#
#     Ele faz duas coisas, e as duas importam:
#       1. acha a pasta que tem o config.txt e trabalha LA (os dados nao se
#          mudaram: dados\, saida_v6\, encaixe\ continuam na casa);
#       2. poe `programas\` na frente do caminho de busca, para os modulos
#          vizinhos serem achados aqui e nao na raiz.
# ===========================================================================
import os as _os, sys as _sys

def _acha_a_casa(inicio):
    p = inicio
    for _ in range(5):
        if _os.path.exists(_os.path.join(p, 'config.txt')):
            return p
        pai = _os.path.dirname(p)
        if pai == p:
            break
        p = pai
    return None

_MEU_LUGAR = _os.path.dirname(_os.path.abspath(__file__))
_CASA = _acha_a_casa(_MEU_LUGAR) or _acha_a_casa(_os.getcwd())
if _CASA:
    if _os.path.abspath(_os.getcwd()) != _os.path.abspath(_CASA):
        _os.chdir(_CASA)
    if _CASA not in _sys.path:
        _sys.path.append(_CASA)          # a casa vem DEPOIS
if _MEU_LUGAR in _sys.path:
    _sys.path.remove(_MEU_LUGAR)
_sys.path.insert(0, _MEU_LUGAR)          # `programas` vem PRIMEIRO
# --------------------------------------------------------------------------
import json, os, sys, io, struct, shutil, collections

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(_CASA or os.path.dirname(os.path.abspath(__file__)))

APLICAR = '--aplicar' in sys.argv

BIN = 'efscout_players.bin'
CAT = 'efscout_boosters.json'
CARDS = 'dados/cards.json'
DATAS = 'ids_sem_vaga_pela_data.json'
CONFJ = 'impeto_conferido_no_jogo.json'
BIT, W = 552, 11

for p in (BIN, CAT, CARDS):
    if not os.path.exists(p):
        print('NAO ACHEI %s — rode o COLETAR-EFSCOUT.bat primeiro.' % p)
        raise SystemExit

d = open(BIN, 'rb').read()
N = struct.unpack_from('<I', d, 0)[0]
REC, OFF = 92, 16
if 16 + N * REC != len(d):
    print('o formato do players.bin mudou (esperava %d bytes, tem %d). PARANDO.'
          % (16 + N * REC, len(d)))
    raise SystemExit

idx = {}
for k in range(N):
    o = OFF + k * REC
    idx[struct.unpack_from('<Q', d, o)[0]] = o

def bits(off, nb, o):
    v = 0
    for b in range(nb):
        bo = off + b
        v |= ((d[o + (bo >> 3)] >> (bo & 7)) & 1) << b
    return v

BY = {b['id']: b for b in json.load(open(CAT, encoding='utf-8'))}
C = json.load(open(CARDS, encoding='utf-8'))
try:
    ids_datas = set(str(x) for x in json.load(open(DATAS, encoding='utf-8'))['ids'])
except Exception:
    ids_datas = set()

print('=' * 72)
print('  O IMPETO DE FABRICA PELO efSCOUT   %s' % ('(APLICANDO)' if APLICAR else '(SO RELATORIO)'))
print('=' * 72)
print('registros no efscout .... %d' % N)

saida, r = {}, collections.Counter()
for c in C:
    b = str(c['id']).split('@')[0]
    if b in saida: continue
    o = idx.get(int(b))
    if o is None:
        r['nao esta no efscout'] += 1; continue
    bid = bits(BIT, W, o)
    bb = BY.get(bid) or {}
    saida[b] = {'booster_id': bid, 'nome': bb.get('name'),
                'efeito': bb.get('stat_modifiers'),
                'conditional': bb.get('conditional'), 'cor': bb.get('color')}
    tem_ef = bid != 0
    tem_nm = bool([x for x in (c.get('nm') or []) if x])
    r['ambos TEM' if (tem_ef and tem_nm) else
      'ambos NAO TEM' if (not tem_ef and not tem_nm) else
      'efscout TEM · nosso vazio' if tem_ef else 'nosso TEM · efscout vazio'] += 1

json.dump(saida, open('efscout_impeto_por_card.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('gravado ................. efscout_impeto_por_card.json (%d cards)' % len(saida))
print()
for k, v in r.most_common(): print('   %-30s %d' % (k, v))

# ---- a decisao: quem sai da trava da data
sai = {b for b in saida if b in ids_datas and saida[b]['booster_id'] != 0}
fica = {b for b in saida if b in ids_datas and saida[b]['booster_id'] == 0}
print()
print('NA LISTA DE DATAS:')
print('   TEM impeto -> SAI da trava (caso Varane) .... %d' % len(sai))
print('   No Booster -> a trava FICA (caso Pirlo) ..... %d' % len(fica))

nomes = {str(c['id']).split('@')[0]: (c.get('nome'), c.get('ovr')) for c in C}
with open('EFSCOUT-SAEM-DA-TRAVA.txt', 'w', encoding='utf-8') as f:
    f.write('CARTAS QUE TEM IMPETO DE FABRICA E ESTAVAM NA TRAVA DA DATA — %d\n\n' % len(sai))
    for b in sorted(sai, key=lambda x: -(nomes.get(x, ('', 0))[1] or 0)):
        nm, ov = nomes.get(b, ('?', 0))
        f.write('%-26s OVR %-4s %-28s %s\n' % (nm, ov, saida[b]['nome'], b))
print('   lista nominal ............................... EFSCOUT-SAEM-DA-TRAVA.txt')

if not APLICAR:
    print()
    print('Nada foi alterado. Para aplicar, use o APLICAR-IMPETO-EFSCOUT.bat')
else:
    j = {'conferidos': {}, 'sem_impeto_nenhum_conferido': {}}
    if os.path.exists(CONFJ):
        try: j = json.load(open(CONFJ, encoding='utf-8'))
        except Exception: pass
        shutil.copy2(CONFJ, CONFJ + '.ANTES-DO-EFSCOUT')
    j.setdefault('conferidos', {})
    j['_fonte_efscout'] = ('efscout players.bin dataVersion do COLETAR-EFSCOUT · bit 552/11 · '
                           'carta com impeto de fabrica nao pode ser de antes do impeto existir')
    for b in sai:
        nm, ov = nomes.get(b, ('?', 0))
        j['conferidos'][b] = '%s %s — efscout: %s. Tem impeto de fabrica, logo sai da trava da data.' \
                             % (nm, ov, saida[b]['nome'])
    json.dump(j, open(CONFJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print()
    print('APLICADO em %s: %d cards na lista de conferidos (backup .ANTES-DO-EFSCOUT)'
          % (CONFJ, len(j['conferidos'])))
    print('Agora: REVISAR-FILA.bat  ->  COMECAR-TUDO.bat')

print()
try:
    if sys.stdin and sys.stdin.isatty(): input('Enter para fechar...')
except Exception: pass
