# -*- coding: utf-8 -*-
"""
GERA O PAINEL - uma tela unica para acompanhar o sistema.

O painel e um arquivo PAINEL.html com TODOS OS NUMEROS DENTRO DELE.
Nao busca nada, nao depende de servidor, nao depende de internet.
Abre com duplo clique e mostra o retrato do momento em que foi gerado.

E gerado sozinho no fim de cada rodada diaria, e tambem quando voce
clicar no PAINEL.bat.
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
import os, sys, io, json, re, time, datetime, subprocess, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
# ⛔ 19/08 — a pasta dos DADOS e a CASA (a do config.txt), nao a
#    pasta deste arquivo. Ele mudou de lugar; os dados nao.
AQUI = _CASA or os.path.dirname(os.path.abspath(__file__))
os.chdir(AQUI)

SEG_POR_LINHA = 21.0   # medido pelo Luis em 06/08: 45 h / 7.716 linhas


def le_json(p, padrao=None):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return padrao


def le_txt(p):
    try:
        return open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        return ''


def quando(p):
    try:
        return datetime.datetime.fromtimestamp(os.path.getmtime(p))
    except Exception:
        return None


def idade_txt(d):
    if not d:
        return 'nao existe'
    h = (datetime.datetime.now() - d).total_seconds() / 3600.0
    if h < 1:
        return 'ha %d min' % int(h * 60)
    if h < 48:
        return 'ha %d h' % int(h)
    return 'ha %d dias' % int(h / 24)


def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


# ======================================================================
#  1. A FILA - quanto ja foi e quanto falta
# ======================================================================
fila = le_json('fila_v6.json', []) or []
total_linhas = len(fila)
feitos = set()
for l in le_txt('feitos.txt').splitlines():
    l = l.strip()
    if l:
        feitos.add(l)
n_feitos = len(feitos)
falta = max(0, total_linhas - n_feitos)
pct = (n_feitos * 100.0 / total_linhas) if total_linhas else 0.0
horas_falta = falta * SEG_POR_LINHA / 3600.0

cards_da_fila = {str(r.get('card_id', '')).split('@')[0] for r in fila if r.get('card_id')}

# ======================================================================
#  2. A BASE UNICA - cobertura campo a campo
# ======================================================================
bu = le_json('dados/base_unica.json', {}) or {}
cob = bu.get('cobertura', {}) or {}
conferido = bu.get('conferido', {}) or {}

# ---------------------------------------------------------------------------
# QUEM PRECISA DE VOCE - a lista com nome, o que falta e o botao que resolve
# ---------------------------------------------------------------------------
# Ordem do Luis, 14/08: "voce tem que dar um jeito da gente ficar sabendo disso,
# senao como e que a gente vai procurar?". Um numero nao e tarefa. Nome + o que
# falta + o botao e tarefa.
BOTAO = {
    'corpo':    ('os 12 numeros do fisico',   'CORPO-PARA-CARDS.bat'),
    'modelo':   ('estilo de jogo da IA',      'COLETAR-EFHUB.bat / efScout'),
    'fab':      ('habilidades de fabrica',    'COLETAR-EFHUB.bat'),
    'base':     ('os 26 atributos',           'COLETAR-EFHUB.bat'),
    'sl':       ('vagas de impeto',           'CONSERTAR-SL.bat'),
    'orc':      ('orcamento de progressao',   'COLETAR-EFHUB.bat'),
    'ovr':      ('OVR',                       'COLETAR-EFHUB.bat'),
    'pos':      ('posicao',                   'POSICOES-DO-EFSCOUT.bat'),
    'np':       ('posicao nativa',            'POSICOES-DO-EFSCOUT.bat'),
    'nome':     ('nome',                      'COLETAR-EFHUB.bat'),
}
TRAVAM = list(BOTAO)

def _vazio(v):
    return v is None or v == [] or v == '' or v == {}

pendentes = []
for c in (bu.get('cards') or []):
    fdc = c.get('fonte_de_cada_campo') or {}
    faltam = [k for k in TRAVAM
              if _vazio(c.get(k)) and fdc.get(k) != 'CONFERIDO']
    if faltam:
        pendentes.append({
            'id': str(c.get('id')), 'nome': c.get('nome') or '?',
            'pos': c.get('pos') or '', 'ovr': c.get('ovr') or 0,
            'faltam': faltam,
            'botoes': sorted({BOTAO[k][1] for k in faltam}),
        })
pendentes.sort(key=lambda x: (-len(x['faltam']), -(x['ovr'] or 0)))

# por botao: quantos cards cada clique resolve
por_botao = {}
for x in pendentes:
    for b_ in x['botoes']:
        por_botao[b_] = por_botao.get(b_, 0) + 1

# e a lista tambem em texto, para abrir fora do painel
try:
    with open('QUEM-PRECISA-DE-VOCE.txt', 'w', encoding='utf-8') as _f:
        _f.write('OS CARDS QUE AINDA TRAVAM O CALCULO - %s\n' % datetime.datetime.now().strftime('%d/%m/%Y %H:%M'))
        _f.write('=' * 74 + '\n\n')
        _f.write('Sao %d registros. Campo com fonte CONFERIDO nao entra aqui.\n\n' % len(pendentes))
        for b_, n_ in sorted(por_botao.items(), key=lambda t: -t[1]):
            _f.write('  %-34s resolve %d\n' % (b_, n_))
        _f.write('\n' + '-' * 74 + '\n\n')
        for x in pendentes:
            _f.write('%-17s %-28s %-5s ovr %-3s  falta: %s\n'
                     % (x['id'], x['nome'][:28], x['pos'], x['ovr'], ', '.join(x['faltam'])))
except Exception:
    pass

# ---------------------------------------------------------------------------
# O QUE TRAVA O CALCULO x O QUE E VAZIO LEGITIMO
# ---------------------------------------------------------------------------
# Ate 14/08 o painel juntava as duas coisas numa coluna so e mostrava 5.017
# "faltando" onde o buraco real era 59. As listas abaixo sao as mesmas do
# completude_base.py — se mudar la, mudar aqui.
TRAVA = ['nome', 'ovr', 'pos', 'np', 'base', 'orc', 'sl', 'fab', 'corpo', 'modelo']
ACABAMENTO = ['max_ovr', 'tier', 'nm', 'vaga', 'box', 'dt', 'pe_ruim', 'levelCap']
NAO_COBRADO = {
    'raras': 'card sem habilidade rara e normal',
    'sec': 'card sem posicao secundaria e normal',
    'nx': 'so existe quando o impeto e condicional',
    'nmn': 'idem',
    'falta': 'o motor nao le mais (POOL=regra desde 08/08) — pool medido 10 a 40',
}
total_reg = bu.get('total_cards', 0)
cards_base = len({str(c.get('id', '')).split('@')[0] for c in (bu.get('cards') or [])})
conflitos = len(bu.get('conflitos') or [])
imp_naoresolv = len(bu.get('impeto_nao_resolvido') or [])
fontes = bu.get('fontes_lidas', {}) or {}

# ======================================================================
#  3. A ULTIMA RODADA - etapa por etapa
# ======================================================================
ultima = le_txt('ULTIMA-RODADA.txt')
etapas = []
for ln in ultima.splitlines():
    m = re.match(r'\s*\[(OK|XX|--)\]\s*(.+)$', ln)
    if m:
        etapas.append((m.group(1), m.group(2).strip()))
m = re.search(r'RODADA DIARIA - ([0-9/: ]+)', ultima)
data_rodada = m.group(1).strip() if m else None

motor_ligado = os.path.exists('LIGAR-MOTOR-AUTOMATICO.txt')
# A trava existe enquanto a rodada corre. Mas o painel e gerado PELA propria
# rodada, na ultima etapa - ai a trava e a dela mesma, nao de outra.
rodando_agora = (os.path.exists('RODADA-DIARIA-RODANDO.txt')
                 and os.environ.get('PAINEL_DENTRO_DA_RODADA') != '1')

agendado = None
try:
    r = subprocess.run(['schtasks', '/query', '/TN', 'TrueFootball - Rodada Diaria'],
                       capture_output=True, timeout=20)
    agendado = (r.returncode == 0)
except Exception:
    agendado = None

novos_hoje = le_json('cards_novos_de_hoje.json', []) or []

# ======================================================================
#  4. FRESCOR DAS FONTES
# ======================================================================
ARQS = [
    ('dados/cards.json',              'o cards.json - o que o motor le'),
    ('dados/base_unica.json',         'a base unica - a fonte unica'),
    ('fila_v6.json',                  'a fila - o escopo do que roda'),
    ('fila_PRIORIDADE.json',          'a ordem - quem roda antes'),
    ('feitos.txt',                    'o que ja rodou'),
    ('efscout_impeto_por_card.json',  'impeto pelo efScout'),
    ('box_por_card.json',             'box e data de lancamento'),
    ('vaga_por_card.json',            'vagas de impeto'),
    ('cards_efhub.json',              'as fichas novas do efHub'),
    ('tecnicos.json',                 'os tecnicos (coleta pelo Chrome)'),
    ('pe_ruim.json',                  'pe ruim (coleta pelo Chrome)'),
    ('dados/molde.json',              'o molde - o denominador da pontuacao'),
]
frescor = []
for p, desc in ARQS:
    d = quando(p)
    frescor.append({'arq': p, 'desc': desc, 'quando': d.strftime('%d/%m %H:%M') if d else '-',
                    'idade': idade_txt(d), 'horas': ((datetime.datetime.now() - d).total_seconds() / 3600.0) if d else -1})

backups = sorted(glob.glob('backups_base/*'), reverse=True)[:5]
backups_banco = sorted(glob.glob('backups_banco/*'), reverse=True)[:5]

historico = []
hist = le_txt('RODADA-DIARIA-LOG.txt')
for bloco in hist.split('#' * 68):
    m1 = re.search(r'RODADA DIARIA - ([0-9/: ]+)', bloco)
    if not m1:
        continue
    def g(pat):
        mm = re.search(pat + r'\s*\.*\s*(\d+)', bloco)
        return int(mm.group(1)) if mm else 0
    historico.append({'quando': m1.group(1).strip(), 'ok': g('etapas OK'),
                      'falha': g('etapas com falha'), 'pulada': g('etapas puladas'),
                      'novos': g('cards novos')})
historico = historico[-12:][::-1]

# ---------------------------------------------------------------------------
# 15/08 — O SISTEMA CONFERINDO A SI MESMO
# Ordem do Luis: "voce acha que eu vou olhar card por card? E o seu metodo que
# esta errado". Os dois detectores (contradicoes.py e quem_veio_pela_metade.py)
# gravam o que acharam; aqui o painel so mostra. Se nao rodaram ainda, some.
def _le_json(nome):
    try:
        return json.load(open(nome, encoding='utf-8'))
    except Exception:
        return None
_contra = _le_json('CONTRADICOES.json') or {}
_metade = _le_json('VEIO-PELA-METADE.json') or {}

DADOS = {
    'gerado': datetime.datetime.now().strftime('%d/%m/%Y %H:%M'),
    'contradicoes': _contra, 'metade': _metade,
    'fila': {'total': total_linhas, 'feitos': n_feitos, 'falta': falta,
             'pct': round(pct, 1), 'horas': round(horas_falta, 1),
             'cards': len(cards_da_fila)},
    'base': {'registros': total_reg, 'cards': cards_base, 'conflitos': conflitos,
             'impeto_nao_resolvido': imp_naoresolv, 'cobertura': cob, 'fontes': fontes,
             'trava': TRAVA, 'acabamento': ACABAMENTO, 'nao_cobrado': NAO_COBRADO,
             'conferido': conferido.get('quantos', 0)},
    'pendentes': pendentes[:400], 'pendentes_total': len(pendentes),
    'por_botao': por_botao,
    'rodada': {'quando': data_rodada, 'etapas': etapas, 'motor': motor_ligado,
               'rodando': rodando_agora, 'agendado': agendado, 'novos': novos_hoje},
    'frescor': frescor, 'backups': backups, 'backups_banco': backups_banco,
    'historico': historico,
    'texto_ultima': ultima[-14000:],
}

HTML = r'''<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TrueFootball - Painel</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0e1116;color:#e6edf3;font:15px/1.5 -apple-system,Segoe UI,Roboto,Arial,sans-serif;padding:22px}
.wrap{max-width:1180px;margin:0 auto}
h1{font-size:23px;font-weight:700;letter-spacing:-.3px}
.sub{color:#8b949e;font-size:13px;margin-top:3px}
.grid{display:grid;gap:14px;margin-top:18px}
.g4{grid-template-columns:repeat(auto-fit,minmax(215px,1fr))}
.g2{grid-template-columns:repeat(auto-fit,minmax(400px,1fr))}
.c{background:#161b22;border:1px solid #262c36;border-radius:12px;padding:16px 18px}
.c h2{font-size:12px;font-weight:600;color:#8b949e;text-transform:uppercase;letter-spacing:.7px;margin-bottom:12px}
.big{font-size:34px;font-weight:700;line-height:1.1;letter-spacing:-1px}
.lbl{color:#8b949e;font-size:12.5px;margin-top:4px}
.bar{height:9px;background:#21262d;border-radius:99px;overflow:hidden;margin:12px 0 8px}
.bar>i{display:block;height:100%;background:linear-gradient(90deg,#2f81f7,#3fb950);border-radius:99px}
.ok{color:#3fb950}.no{color:#f85149}.wt{color:#d29922}.mut{color:#8b949e}
table{width:100%;border-collapse:collapse;font-size:13.5px}
td,th{padding:6px 8px;border-bottom:1px solid #21262d;text-align:left}
th{color:#8b949e;font-size:11px;text-transform:uppercase;letter-spacing:.6px;font-weight:600}
tr:last-child td{border-bottom:none}
.num{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-block;padding:2px 9px;border-radius:99px;font-size:11.5px;font-weight:600}
.pok{background:#12261e;color:#3fb950}.pno{background:#2a1215;color:#f85149}.pmu{background:#21262d;color:#8b949e}
.mini{height:6px;background:#21262d;border-radius:99px;overflow:hidden;width:110px;display:inline-block;vertical-align:middle}
.mini>i{display:block;height:100%}
pre{background:#0d1117;border:1px solid #21262d;border-radius:9px;padding:13px;font-size:12px;
 white-space:pre-wrap;max-height:430px;overflow:auto;color:#adbac7}
.aviso{border-left:3px solid #d29922;background:#1c1810;padding:11px 14px;border-radius:0 8px 8px 0;
 font-size:13.5px;margin-top:12px}
.tag{font-size:11.5px;color:#6e7681}
</style></head><body><div class="wrap">
<h1>TrueFootball &mdash; Painel</h1>
<div class="sub" id="ger"></div>
<div id="app"></div>
</div>
<script>
const D = __DADOS__;
const N = n => (n==null?'-':n.toLocaleString('pt-BR'));
const E = s => String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
document.getElementById('ger').textContent = 'retrato de ' + D.gerado;

let h = '';

/* ---------- os quatro numeros de cima ---------- */
const f = D.fila, r = D.rodada;
h += '<div class="grid g4">';
h += '<div class="c"><h2>A fila do motor</h2><div class="big">'+f.pct+'%</div>'+
     '<div class="bar"><i style="width:'+f.pct+'%"></i></div>'+
     '<div class="lbl">'+N(f.feitos)+' de '+N(f.total)+' linhas prontas</div>'+
     '<div class="lbl">faltam <b>'+N(f.falta)+'</b> &middot; ~'+N(f.horas)+' h de motor</div></div>';

h += '<div class="c"><h2>A base unica</h2><div class="big">'+N(D.base.cards)+'</div>'+
     '<div class="lbl">cards na base</div>'+
     '<div class="lbl">'+N(D.base.registros)+' registros (card por posicao)</div>'+
     '<div class="lbl">'+N(D.base.conflitos)+' conflitos entre fontes</div></div>';

const motor = r.motor
  ? '<span class="pill pok">LIGADO</span>'
  : '<span class="pill pmu">DESLIGADO</span>';
const agd = r.agendado===true ? '<span class="pill pok">agendado</span>'
          : r.agendado===false ? '<span class="pill pno">nao agendado</span>'
          : '<span class="pill pmu">nao sei</span>';
h += '<div class="c"><h2>A rodada diaria</h2>'+
     '<div style="margin-bottom:9px">'+agd+(r.rodando?' <span class="pill pok">rodando agora</span>':'')+'</div>'+
     '<div class="lbl">ultima: <b>'+(r.quando||'nunca rodou')+'</b></div>'+
     '<div class="lbl" style="margin-top:9px">motor automatico: '+motor+'</div></div>';

h += '<div class="c"><h2>Cards novos</h2><div class="big">'+N(r.novos.length)+'</div>'+
     '<div class="lbl">entraram na ultima rodada</div>'+
     (r.novos.length && !r.motor
       ? '<div class="lbl wt" style="margin-top:8px">estao na FRENTE da fila, esperando voce mandar rodar</div>'
       : '<div class="lbl">nada esperando</div>')+'</div>';
h += '</div>';

if(!r.motor){
  h += '<div class="aviso"><b>O motor automatico esta desligado</b> &mdash; e assim que voce mandou deixar. '+
       'As coletas, a base e o Encaixe rodam sozinhos; o motor nao. '+
       'Para ligar, crie nesta pasta um arquivo vazio chamado <b>LIGAR-MOTOR-AUTOMATICO.txt</b>.</div>';
}

h += '<div class="grid g2">';

/* ---------- etapas da ultima rodada ---------- */
h += '<div class="c"><h2>A ultima rodada, etapa por etapa</h2>';
if(!r.etapas.length){ h += '<div class="mut">Ainda nao rodou nenhuma vez.</div>'; }
else{
  h += '<table>';
  r.etapas.forEach(e=>{
    const p = e[0]==='OK' ? '<span class="pill pok">ok</span>'
            : e[0]==='XX' ? '<span class="pill pno">falhou</span>'
            : '<span class="pill pmu">pulada</span>';
    h += '<tr><td>'+E(e[1])+'</td><td class="num">'+p+'</td></tr>';
  });
  h += '</table>';
}
h += '</div>';

/* ---------- frescor ---------- */
h += '<div class="c"><h2>Quando cada fonte foi atualizada</h2><table>';
D.frescor.forEach(x=>{
  const cls = x.horas<0 ? 'no' : x.horas>72 ? 'wt' : 'ok';
  h += '<tr><td>'+E(x.desc)+'<div class="tag">'+E(x.arq)+'</div></td>'+
       '<td class="num '+cls+'">'+E(x.idade)+'<div class="tag">'+E(x.quando)+'</div></td></tr>';
});
h += '</table></div>';
h += '</div>';

/* ---------- cobertura, separada em tres ---------- */
const cob = D.base.cobertura, ks = Object.keys(cob);
if(ks.length){
  const tot = cob[ks[0]].preenchidos + cob[ks[0]].faltando;
  const linha = k => ({k:k, p:cob[k].preenchidos, f:cob[k].faltando,
                       pc: tot? cob[k].preenchidos*100/tot : 0});
  const tabela = (titulo, subtitulo, campos, mostrarMotivo) => {
    const arr = campos.filter(k=>cob[k]).map(linha).sort((a,b)=>a.pc-b.pc);
    if(!arr.length) return '';
    const somaF = arr.reduce((s,x)=>s+x.f,0);
    let t = '<div class="c"><h2>'+titulo+'</h2>'+
            '<div class="lbl" style="margin:-6px 0 12px">'+subtitulo+'</div>'+
            '<table><tr><th>campo</th><th>tem</th><th class="num">'+
            (mostrarMotivo?'por que nao se cobra':'falta')+'</th></tr>';
    arr.forEach(x=>{
      const cor = x.pc>=99?'#3fb950':x.pc>=70?'#d29922':'#f85149';
      t += '<tr><td><b>'+E(x.k)+'</b></td>'+
           '<td><span class="mini"><i style="width:'+x.pc.toFixed(1)+'%;background:'+
             (mostrarMotivo?'#6e7681':cor)+'"></i></span> '+N(x.p)+'</td>';
      t += mostrarMotivo
        ? '<td class="num mut" style="text-align:left;font-size:12.5px">'+E(D.base.nao_cobrado[x.k]||'')+'</td>'
        : '<td class="num">'+(x.f?('<span class="'+(x.pc>=99?'wt':'no')+'">'+N(x.f)+'</span>')
                                 :'<span class="ok">0</span>')+'</td>';
      t += '</tr>';
    });
    if(!mostrarMotivo) t += '<tr><td colspan="2" class="mut">total</td><td class="num"><b>'+N(somaF)+'</b></td></tr>';
    return t + '</table></div>';
  };
  h += '<div class="grid g2">';
  h += tabela('1. Trava o calculo',
              'Sem isto o motor calcula errado, ou nem calcula. E aqui que mora o buraco de verdade.',
              D.base.trava, false);
  h += tabela('2. Acabamento',
              'O motor anda sem. Melhora a tela e a organizacao, nao muda a escolha da build.',
              D.base.acabamento, false);
  h += '</div><div class="grid">';
  h += tabela('3. Nao se cobra &mdash; vazio aqui e resposta, nao buraco',
              'Estes campos ficam vazios de proposito. Contar como falta e o que inflava o numero.',
              Object.keys(D.base.nao_cobrado), true);
  h += '</div>';
  if(D.base.conferido){
    h += '<div class="aviso" style="border-color:#3fb950;background:#12261e">'+
         '<b>'+N(D.base.conferido)+' vazios CONFERIDOS</b> &mdash; foram checados em duas fontes e a resposta '+
         'e "esse card nao tem". Estao gravados no CONFERIDO.json e nao aparecem mais como falta.</div>';
  }
}

h += '<div class="grid g2">';

/* ---------- O QUE NAO PODE SER VERDADE (15/08) ---------- */
if((D.contradicoes && D.contradicoes.total) || (D.metade && D.metade.vencidos)){
  h += '<div class="grid"><div class="c">'+
       '<h2>O que o sistema achou sozinho</h2>'+
       '<div class="lbl" style="margin:-6px 0 14px">Ninguem olhou card por card. '+
       'Sao contradicoes do proprio dado &mdash; o que nao pode ser verdade.</div>';
  if(D.metade && D.metade.vencidos){
    h += '<div class="alerta" style="background:#3a1111;border-left:4px solid #c33;'+
         'padding:10px 12px;margin-bottom:12px;border-radius:4px">'+
         '<b>'+N(D.metade.vencidos)+' cards passaram de 24h esperando a fonte responder.</b>'+
         '<div class="lbl">Ja deviam ter saido em algum lugar &mdash; procurar na mao. '+
         'A lista esta no RELATORIO-VEIO-PELA-METADE.txt.</div></div>';
  }
  const cs = Object.entries((D.contradicoes && D.contradicoes.regras) || {})
                   .sort((a,b)=>b[1]-a[1]);
  if(cs.length){
    h += '<table><tr><th>o que nao pode ser verdade</th><th class=n>casos</th></tr>';
    for(const [regra,n] of cs)
      h += '<tr><td>'+regra+'</td><td class=n>'+N(n)+'</td></tr>';
    h += '</table><div class="lbl" style="margin-top:8px">'+
         'Detalhe e o que fazer com cada um: RELATORIO-CONTRADICOES.txt</div>';
  }
  h += '</div></div>';
}

/* ---------- QUEM PRECISA DE VOCE ---------- */
if(D.pendentes_total){
  h += '<div class="grid"><div class="c">'+
       '<h2>Quem precisa de voce &mdash; '+N(D.pendentes_total)+' registros travando o calculo</h2>'+
       '<div class="lbl" style="margin:-6px 0 14px">Estes o motor calcula errado, ou nem calcula. '+
       'Cada linha diz o que falta e qual botao resolve.</div>';
  const pb = Object.entries(D.por_botao).sort((a,b)=>b[1]-a[1]);
  h += '<table style="margin-bottom:16px"><tr><th>o botao</th><th class="num">resolve quantos</th></tr>';
  pb.forEach(([b_,n])=>{ h += '<tr><td><b>'+E(b_)+'</b></td><td class="num wt">'+N(n)+'</td></tr>'; });
  h += '</table>';
  h += '<table><tr><th>card</th><th>pos</th><th class="num">ovr</th><th>o que falta</th></tr>';
  D.pendentes.forEach(x=>{
    h += '<tr><td><b>'+E(x.nome)+'</b><div class="tag">'+E(x.id)+'</div></td>'+
         '<td class="mut">'+E(x.pos)+'</td>'+
         '<td class="num mut">'+(x.ovr||'')+'</td>'+
         '<td>'+x.faltam.map(f=>'<span class="pill pno" style="margin-right:4px">'+E(f)+'</span>').join('')+'</td></tr>';
  });
  h += '</table>';
  if(D.pendentes_total > D.pendentes.length){
    h += '<div class="lbl" style="margin-top:10px">Mostrando '+N(D.pendentes.length)+' de '+N(D.pendentes_total)+
         '. A lista inteira esta no arquivo <b>QUEM-PRECISA-DE-VOCE.txt</b>, na mesma pasta.</div>';
  } else {
    h += '<div class="lbl" style="margin-top:10px">Esta lista inteira tambem esta em <b>QUEM-PRECISA-DE-VOCE.txt</b>.</div>';
  }
  h += '</div></div>';
} else {
  h += '<div class="grid"><div class="c"><h2>Quem precisa de voce</h2>'+
       '<div class="ok" style="font-size:17px">Ninguem. Nenhum card esta travando o calculo.</div></div></div>';
}

/* ---------- historico ---------- */
h += '<div class="c"><h2>As ultimas rodadas</h2>';
if(!D.historico.length){ h += '<div class="mut">Sem historico ainda.</div>'; }
else{
  h += '<table><tr><th>quando</th><th class="num">ok</th><th class="num">falhas</th><th class="num">puladas</th><th class="num">novos</th></tr>';
  D.historico.forEach(x=>{
    h += '<tr><td>'+E(x.quando)+'</td><td class="num ok">'+x.ok+'</td>'+
         '<td class="num '+(x.falha?'no':'mut')+'">'+x.falha+'</td>'+
         '<td class="num mut">'+x.pulada+'</td>'+
         '<td class="num '+(x.novos?'wt':'mut')+'">'+x.novos+'</td></tr>';
  });
  h += '</table>';
}
h += '</div>';

/* ---------- backups ---------- */
h += '<div class="c"><h2>Backups mais recentes</h2>';
h += '<div class="lbl" style="margin-bottom:6px">da base</div>';
h += D.backups.length ? '<table>'+D.backups.map(b=>'<tr><td>'+E(b)+'</td></tr>').join('')+'</table>'
                      : '<div class="no">nenhum backup da base.</div>';
h += '<div class="lbl" style="margin:14px 0 6px">do banco</div>';
h += D.backups_banco.length ? '<table>'+D.backups_banco.map(b=>'<tr><td>'+E(b)+'</td></tr>').join('')+'</table>'
                            : '<div class="wt">nenhum backup do banco ainda &mdash; rode o BACKUP-DO-BANCO.bat.</div>';
h += '</div>';
h += '</div>';

/* ---------- as fontes lidas ---------- */
const fo = D.base.fontes, fk = Object.keys(fo);
if(fk.length){
  h += '<div class="grid"><div class="c"><h2>De onde a base se alimentou</h2><table>'+
    '<tr><th>arquivo</th><th class="num">linhas que ele deu</th></tr>'+
    fk.sort((a,b)=>fo[b]-fo[a]).map(k=>'<tr><td>'+E(k)+'</td><td class="num">'+N(fo[k])+'</td></tr>').join('')+
    '</table></div></div>';
}

/* ---------- o relatorio inteiro ---------- */
if(D.texto_ultima.trim()){
  h += '<div class="grid"><div class="c"><h2>O relatorio inteiro da ultima rodada</h2><pre>'+
       E(D.texto_ultima)+'</pre></div></div>';
}

document.getElementById('app').innerHTML = h;
</script></body></html>'''

saida = HTML.replace('__DADOS__', json.dumps(DADOS, ensure_ascii=False))
open('PAINEL.html', 'w', encoding='utf-8').write(saida)

print('PAINEL.html gerado - %d KB' % (len(saida) // 1024))
print('  fila ......... %d de %d linhas (%.1f%%)' % (n_feitos, total_linhas, pct))
print('  base ......... %d cards / %d registros' % (cards_base, total_reg))
print('  motor auto ... %s' % ('LIGADO' if motor_ligado else 'DESLIGADO'))
print('  travando ..... %d registros -> QUEM-PRECISA-DE-VOCE.txt' % len(pendentes))
