# -*- coding: utf-8 -*-
"""
GERAR A COLETA DO efHUB — passo 5. 16/08/2026

POR QUE ELE NAO BUSCA SOZINHO:
  A API do efHub devolve 403 fora do Chrome. Esta escrito no
  COLETAR-EFHUB-PELO-CONSOLE.md desde 10/08 e foi conferido de novo em 16/08:
  de dentro de uma aba do efhub.com a MESMA chamada responde 200.

  Entao este programa nao coleta. Ele MONTA a coleta: le a fila, pega a lista
  exata de cartas que estao em "nao sei", e escreve uma pagina com o bloco
  pronto para colar no Console (F12).

⛔ NAO pede o banco inteiro. Pede SO as cartas da fila. Ordem do Luis, 14/08:
   "nada de recoletar 2.600 cartas para achar 17".

⛔ A ficha vem INTEIRA e crua. Quem decide o que aproveitar e o programa de
   entrada, depois. Coletar cru uma vez serve para todos os campos; coletar
   recortado obriga a voltar na fonte a cada campo novo.
"""
import json, os, sys, io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def P(*a):
    print(*a, flush=True)


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
    P('⛔ nao achei o config.txt subindo a partir de %s' % AQUI)
    sys.exit(1)
os.chdir(CASA)

FILA = os.path.join('dados', 'fila_de_coleta.json')
SAIDA = 'COLETAR-EFHUB-AGORA.html'

P('=' * 78)
P('  GERAR A COLETA DO efHUB  ·  ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
P('=' * 78)
P('')

if not os.path.exists(FILA):
    P('⛔ nao achei o %s. Rode antes o FILA-DE-COLETA.bat.' % FILA)
    sys.exit(1)

F = json.load(open(FILA, encoding='utf-8'))
porc = F.get('por_campo') or {}

MEUS = [c for c, v in porc.items() if (v.get('quem_perguntar') or [None])[0] == 'efhub']
if not MEUS:
    P('⛔ a fila nao tem nenhum campo cujo primeiro da vez seja o efHub.')
    P('   Ou ja acabou, ou a fila esta velha.')
    sys.exit(1)

por_carta = {}
for campo in MEUS:
    for cid in (porc[campo].get('cartas_a_perguntar') or []):
        por_carta.setdefault(str(cid).split('@')[0], set()).add(campo)

ids = sorted(por_carta, key=lambda c: -len(por_carta[c]))

P('  fila lida ................. gerada em %s' % (F.get('gerado_em') or '?')[:16])
P('  campos que o efHub responde:')
for campo in sorted(MEUS, key=lambda c: -len(porc[c].get('cartas_a_perguntar') or [])):
    P('     %-10s %6d linhas em "nao sei"' % (campo, len(porc[campo].get('cartas_a_perguntar') or [])))
P('')
P('  CARTAS de verdade a buscar  %d' % len(ids))
P('  tempo no navegador ........ ~%d minuto(s) (2 pedidos por vez, com recuo)' % max(1, int(len(ids) * 0.42 / 60) + 1))
P('')

# ============================================================================
JS = """(async function(){
 const IDS = %s;
 const LINHAS = 2, PAUSA = 700;
 const fichas = {}, falhas = [];
 let feito = 0, e429 = 0;
 const dorme = ms => new Promise(r => setTimeout(r, ms));
 const t0 = Date.now();
 console.log('%%cCOLETA DO efHUB — ' + IDS.length + ' cartas. NAO FECHE ESTA ABA.',
             'background:#f0a531;color:#000;font-weight:700;padding:3px 8px');
 let i = 0;
 const worker = async () => {
  while (i < IDS.length) {
   const id = IDS[i++];
   let espera = 700, ok = false;
   for (let t = 0; t < 6 && !ok; t++) {
    try {
     const r = await fetch('/api/public/players/' + id, {credentials:'include'});
     if (r.status === 429) { e429++; await dorme(espera); espera = Math.min(espera*2, 15000); continue; }
     if (r.ok) { const j = await r.json(); fichas[id] = (j && j.player) ? j.player : j; ok = true; }
     else { falhas.push(id + ' HTTP' + r.status); ok = true; }
    } catch(e) { await dorme(espera); espera = Math.min(espera*2, 15000); }
   }
   if (!ok) falhas.push(id + ' desistiu');
   feito++;
   if (feito %% 50 === 0) {
    const seg = (Date.now()-t0)/1000, resta = seg/feito*(IDS.length-feito);
    console.log('   ' + feito + '/' + IDS.length + ' · trouxe ' + Object.keys(fichas).length +
                ' · 429 ' + e429 + ' · falhas ' + falhas.length +
                ' · faltam ~' + Math.ceil(resta/60) + ' min');
   }
   await dorme(PAUSA);
  }
 };
 await Promise.all(Array.from({length: LINHAS}, worker));
 const pacote = {
   o_que_e: 'as fichas cruas do efHub, uma por carta, como o site devolveu',
   fonte: 'efhub /api/public/players/<id>',
   colhido_em: new Date().toISOString(),
   pedidas: IDS.length,
   trouxe: Object.keys(fichas).length,
   falhas: falhas,
   fichas: fichas
 };
 console.log('%%cPRONTO — ' + pacote.trouxe + ' de ' + IDS.length +
             ' · falhas ' + falhas.length + ' · 429 ' + e429,
             'background:#22c58b;color:#000;font-weight:700;padding:3px 8px');
 const b = new Blob([JSON.stringify(pacote)], {type:'application/json'});
 const a = document.createElement('a');
 a.href = URL.createObjectURL(b); a.download = 'efhub_fichas.json';
 document.body.appendChild(a); a.click(); a.remove();
 console.log('baixado: efhub_fichas.json — mande para a pasta do motor');
})();""" % json.dumps(ids)

campos_txt = ''.join(
    '<tr><td><code>%s</code></td><td class="n">%d</td></tr>' % (c, len(porc[c].get('cartas_a_perguntar') or []))
    for c in sorted(MEUS, key=lambda c: -len(porc[c].get('cartas_a_perguntar') or [])))

HTML = """<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Coletar o efHub — %(quando)s</title>
<style>
:root{--bg:#0e1116;--pn:#151a22;--tx:#cfd6e4;--tx2:#8d97a8;--vd:#22c58b;--dr:#d8b45a;--lr:#2a3140}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.6 -apple-system,Segoe UI,Roboto,Arial,sans-serif}
.wrap{max-width:900px;margin:0 auto;padding:28px 20px 70px}
h1{font-size:27px;margin:0 0 4px;color:#fff;letter-spacing:-.3px}
h2{font-size:20px;margin:32px 0 10px;color:var(--dr);border-bottom:1px solid var(--lr);padding-bottom:6px}
.sub{color:var(--tx2);margin:0 0 20px}
.card{background:var(--pn);border:1px solid var(--lr);border-radius:9px;padding:15px 17px;margin:14px 0}
table{width:100%%;border-collapse:collapse;margin:10px 0 14px;font-size:14px}
th,td{border:1px solid var(--lr);padding:7px 9px;text-align:left}
th{background:var(--pn);color:var(--dr)}
td.n{text-align:right;font-variant-numeric:tabular-nums}
ol{padding-left:22px} li{margin:9px 0}
a{color:var(--vd)}
pre{background:#0a0d12;border:1px solid var(--lr);border-radius:8px;padding:14px;overflow:auto;
    font:12px/1.5 Consolas,Menlo,monospace;color:#d7e2f0;max-height:300px}
button{background:var(--vd);color:#06231a;border:0;border-radius:8px;padding:12px 22px;
       font-size:16px;font-weight:700;cursor:pointer}
button:active{transform:translateY(1px)}
.ok{color:var(--vd)} .mut{color:var(--tx2)} .er{color:#e05555}
.big{font-size:32px;color:#fff;font-variant-numeric:tabular-nums}
</style></head><body><div class="wrap">

<h1>Coletar o efHub</h1>
<p class="sub">%(quando)s — <span class="big">%(n)d</span> cartas, e só elas.</p>

<div class="card">
<b>Por que isto não é um duplo clique.</b><br>
A porta do efHub <b>recusa quem chama de fora do navegador</b> — devolve 403. De dentro de
uma aba do próprio site, a mesma chamada responde 200. Está assim desde 10/08 e foi
conferido de novo hoje. <b>Só o seu Chrome passa.</b>
</div>

<h2>O que vem nesta coleta</h2>
<table>
<tr><th>campo</th><th>linhas em "não sei"</th></tr>
%(campos)s
</table>
<p class="mut">Uma visita por carta traz <b>todos</b> esses campos de uma vez. A ficha vem
inteira e crua — quem escolhe o que aproveitar é o programa de entrada, depois. Coletar
cru uma vez serve para todo campo novo; coletar recortado obriga a voltar na fonte.</p>

<h2>O passo a passo</h2>
<ol>
<li>Abra o efHub no Chrome:
    <a href="https://efhub.com/pt-BR/players" target="_blank">efhub.com/pt-BR/players</a>
    <br><span class="mut">tem que ser essa página — de outro site o navegador bloqueia</span></li>
<li>Aperte <b>F12</b> e clique na aba <b>Console</b>.</li>
<li>Volte aqui e clique no botão verde.</li>
<li>No Console: <b>Ctrl+V</b> e <b>Enter</b>.
    <br><span class="mut">se ele pedir para digitar <code>allow pasting</code>, digite e dê Enter</span></li>
<li><b>Não feche a aba.</b> Pode usar outras normalmente. Leva ~%(min)d minutos.</li>
<li>Quando terminar ele <b>baixa sozinho</b> o <code>efhub_fichas.json</code> na sua pasta
    Downloads.</li>
<li>Recorte esse arquivo e cole em<br>
    <code>%(casa)s</code></li>
<li>Dê dois cliques no <b>ENTRAR-COM-O-EFHUB.bat</b>.</li>
</ol>

<p style="text-align:center;margin:26px 0">
<button onclick="copiar()">📋 Copiar o bloco para o Console</button>
<span id="msg" class="ok" style="margin-left:14px"></span>
</p>

<div class="card">
<b class="er">Se encher de 429 e parar de andar</b><br>
É o limite de velocidade do site. Feche a aba, espere 5 minutos e comece de novo — ele
libera sozinho. O bloco já vai devagar (2 pedidos por vez) e recua sozinho quando leva 429.
</div>

<pre id="js">%(js)s</pre>

<script>
function copiar(){
  var t = document.getElementById('js').innerText;
  navigator.clipboard.writeText(t).then(function(){
    document.getElementById('msg').textContent = '✅ copiado — agora cole no Console';
  }, function(){
    var r = document.createRange(); r.selectNode(document.getElementById('js'));
    window.getSelection().removeAllRanges(); window.getSelection().addRange(r);
    document.getElementById('msg').textContent = 'selecionei — aperte Ctrl+C';
  });
}
</script>
</div></body></html>
""" % {'quando': datetime.now().strftime('%d/%m/%Y %H:%M'),
       'n': len(ids),
       'campos': campos_txt,
       'min': max(1, int(len(ids) * 0.42 / 60) + 1),
       'casa': CASA,
       'js': JS.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}

with open(os.path.join(CASA, SAIDA), 'w', encoding='utf-8') as f:
    f.write(HTML)

P('  gravei .................... %s' % SAIDA)
P('')
P('  CONFERENCIA')
t = open(os.path.join(CASA, SAIDA), encoding='utf-8').read()
falta = [x for x in ('const IDS =', 'efhub_fichas.json', 'players/') if x not in t]
if falta:
    P('  ⛔ o arquivo saiu incompleto: falta %s' % ', '.join(falta))
    sys.exit(1)
quantos = t.count('","') + 1 if '","' in t else 0
P('  ✅ a pagina tem o bloco, a lista de ids e o download')
P('')
P('  O QUE FAZER AGORA:')
P('     abra o %s e siga os 8 passos' % SAIDA)
P('')
P('  PRONTO.')
