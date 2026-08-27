# A AUDITORIA DA MIGRAÇÃO — a trava que roda depois de TODA implementação
**Criada em 25/08 por ordem do Luis**, depois que ele achou um erro que eu deixei passar.

## Como chamar (uma linha, no SQL Editor do Supabase)

```sql
select * from clube.auditoria_completa() order by status desc, grupo, item;
```

Só o que está errado:
```sql
select * from clube.auditoria_completa() where status <> 'OK';
```

👉 https://supabase.com/dashboard/project/trqqpsnafpbudtvvicch/sql/new

## A REGRA (do Luis, 25/08)

> *"Toda implementação que você fizer, depois você valida e testa. Compara com o
> que a gente já sabe que é verdade."*
>
> *"Quando migrar, é importantíssimo comparar com o estado anterior — com o jeito
> que a tela do site puxa as informações hoje. Se der divergência, a gente tem que
> PARAR, ver o porquê, e chegar ao ponto verdadeiro."*

Nenhuma fase avança com `FALHA` na auditoria. Divergência não se contorna: se
investiga até o fim e o resultado é registrado em `clube.divergencia_conhecida`
com veredicto — aí, e só aí, ela deixa de ser FALHA e vira CONHECIDA.

## O que ela confere — 31 conferências, cada uma contra uma fonte da verdade

**Dicionários (10):** funções · 26 atributos · catálogo de ímpetos · efeitos ·
ímpetos fabricáveis · habilidades · técnicos · estilo×valor · boxes · traduções.

**Receita (6):** a versão vigente é a MESMA do legado · o molde vigente tem
Σ|Δalvo| = 0 · zero pesos diferentes · parâmetros · bloqueios · regra posição→função.

**Carta (4):** total · os 26 atributos NA ORDEM · posições secundárias separadas
de verdade · ímpetos por carta ≥ o legado.

**Resultado (6):** total de builds · b1 idêntico em amostra de 200 · contagem por
função · % do topo ≤ 100 · marcadas para recálculo ≥ a lista dos ímpetos ·
medianas próprias (Falso nove ≠ Centroavante móvel).

**O ESPELHO DA TELA DE HOJE (5)** — a regra nova:
pares cobertos · **b1 da tela = b1 da casa** · nome do card · **ovr do card** ·
nenhuma carta que a tela vê e a casa não tem.

## Placar de hoje: 29 OK · 2 CONHECIDAS · 0 FALHAS

---

# OS ERROS QUE ELA ACHOU (e que eu tinha deixado passar)

## 🔴 1 · O molde estava rotulado como v1 — e o vigente é o **v5**
**Quem achou: o Luis.** Eu carreguei o molde e chamei de "versão 1" sem olhar a
`molde_versao`. O molde vigente é o **v5** (12/08 — criação do Falso nove e
Centroavante móvel refeito). O conteúdo estava certo (Σ|Δ| = 0 contra o v5),
mas o número mentia — exatamente o tipo de erro de rótulo que passamos o dia
consertando.
**Corrigido:** a linhagem real 1→5 foi carregada com a origem de cada versão,
v5 marcada vigente, os moldes históricos v2 e v3 preservados, e as 17.798 builds
apontando para a v5.

## 🔴 2 · As posições secundárias estavam GRUDADAS — 2.090 cartas
Eu separei por vírgula; o legado usa **barra**. Resultado: `CA/MC/MLD/MO/PD/PE/SA`
virou UM item só em vez de sete. Posição secundária é o que define quais funções
a carta pode disputar — isso quebraria o motor e o Elenco.
**Corrigido:** 2.090 cartas refeitas com o separador certo.

## 🔴 3 · Faltavam insumos que o MOTOR precisa pra rodar
| o que | tinha | agora |
|---|---:|---:|
| catálogo de ímpetos | 350 | **430** (faltavam 80, sendo 25 em uso por cartas) |
| efeitos de ímpeto | 1.540 | **2.158** (faltavam 618) |
| ímpetos fabricáveis | **0** | **58** ← o motor fabrica ímpeto com isto |
| bloqueios (habilidade × função) | **0** | **246** ← o motor precisa pra não sugerir habilidade proibida |
| regra posição → função | **0** | **24** |
| tipo da carta | **0** | 137 |
| traduções (de-para de nomes) | **0** | **438** |

Sem os três primeiros, o motor **não rodaria** contra a casa nova.

---

# AS 2 DIVERGÊNCIAS CONTRA A TELA DE HOJE — investigadas até o fim

## ⚖️ 1 · `b1`: 1.324 pares onde a tela discorda — **PRÉ-EXISTENTE**
A investigação separou as águas:

```
casa nova  ×  builds legada .......... 0 divergências   ← a migração está limpa
tela_encaixe × builds legada ..... 1.324 divergências   ← a briga é entre elas
tela_encaixe × casa nova ......... 1.324 (as mesmas)
```

**Não foi a migração.** A `tela_encaixe` é alimentada por caminho paralelo (o
`gera_encaixe.py` lê arquivo local, não o banco), e por isso os dois depósitos
andaram separados. O padrão medido:
- nas **8 funções de rótulo**: tela de 17/08 × build de 21/08 → a build é mais nova;
- nas demais: tela de 19/08 × build de 11-15/08 → a tela é mais nova.

Diferença média: **54,9 pontos de b1**. Não dá pra cravar qual é a verdade sem
rodar o motor — então, pela tua regra de nunca inventar número, **os 1.324 pares
(639 cartas) foram marcados para recálculo**. O motor decide.

## ✅ 2 · `ovr`: 205 divergências — **a casa está certa, a tela mente**
A tela grava **`ovr = 0`** em 51 cartas onde o `cards_base` tem **NULL**. Isso
viola a regra da casa: *quando não se sabe, mostra "não sei" — nunca zero*.
A casa preserva o NULL. Nada a corrigir aqui: é a tela velha que está errada.

---

# O EFEITO NA FILA DO MOTOR

```
antes da auditoria ......   870 cartas ·  5.119 builds
depois .................. 1.321 cartas ·  5.711 builds
                          (870 dos ímpetos + 639 da divergência tela × build,
                           com sobreposição de 188)
```

Cada linha carrega o motivo escrito (`impeto_divergente_v1`,
`divergencia_tela_x_build`, ou os dois). Continua sendo **uma rodada só**,
quando você mandar.
