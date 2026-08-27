# BRIEFING PARA A SESSÃO NOVA — ClubEfootball / Sistema Encaixe
**Gerado 26/08/2026.** Mande este documento (e o `ANALISE-ESTILOS-2027.md` que vai junto)
no início da sessão nova. Ele resume onde paramos, o que está decidido e o que falta.

> Contexto do dono: Luis Fernando, dono da Inerente (Goiânia). NÃO é programador, faz tudo
> pelo NAVEGADOR (GitHub online, Netlify, Railway, Supabase dashboard). NUNCA terminal.
> Sempre arquivos completos prontos pra colar, passo a passo numerado com links clicáveis,
> em PORTUGUÊS. O mapa completo está no `ARQUITETURA-INERENTE.md` e no
> `CADERNO-DE-IMPLEMENTACOES` (projeto do Claude + `4-DOCUMENTOS`).

---

## 1 · O QUE ESTA SESSÃO FEZ (a fonte virou o código do jogo)

- **Extrator próprio** (`Downloads\Clubefootball 2026-08-25\VER DADOS DO JOGO\Extrator-ClubEfootball.html`):
  lê os `.cpk` do jogo no navegador (decifra WESYS+CPK localmente, nada sai do PC). Arrasta
  `dt200_console_all.cpk` (2026) + `dt870_console_win.cpk` (2027) da pasta
  `C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\`. Detecta a temporada
  sozinho. Botão **"Baixar CSV"** gera o arquivo de importação.
- **`clube.carta_jogo` carregada: 40.100 cartas** (via import CSV no Table Editor).
  20.660 base · 19.438 colecionável · 2 teste. Chave = `card_id`.
  Traz: `overall` (calculado dos atributos, 94% ±1 vs nosso `ovr`), `tipo`, `estilo_of`
  (PT) + `estilo_of_id` + `estilo_of_pos`, `estilo_def`, ímpeto dos 2 slots, nome latino.
- **Catálogo-tradutor `clube.estilo_jogo`** (id → nome PT + posições, 23 ofensivos) e
  **`clube.estilo_defensivo_ref`** (13 defensivos de 2027, nome PT + posições).
- **29 estilos + 56 ímpetos novos** marcados `novo_2027` nos catálogos.
- **Migrações 0037, 0038, 0039.** Auditoria: **0 falhas.**
- **Cruzamento:** das 3.269 nossas, **1.963 estão no jogo** (1.934 no 2027, refrescáveis);
  1.306 só online (o **jogador** existe em 1.296, é a variante histórica que sumiu; 10 o
  jogador nem existe). **1.884 colecionáveis** pra fila do motor.

## 2 · REGRAS QUE NÃO MUDAM
- Chave é sempre o **código** (`card_id`, `estilo_of_id`, `impeto_s1`, `funcao.codigo`),
  **nunca o nome** (lição do erro da função). Nome é etiqueta.
- `clube` é a casa (só ela é escrita). `public` e `clubef_read_v2` = matéria-prima.
- **O motor só roda com ordem explícita do Luis, na máquina dele.** `marcar ≠ rodar`.
- Rodar a auditoria (`clube.auditoria_completa()`) depois de qualquer mexida; `FALHA` = PARAR.
- O molde é segredo industrial; não sai alvo/peso/pool pra tela.

## 3 · ⭐ DECISÃO PRIORITÁRIA A CONFIRMAR — RODAR TODAS AS LINHAS
O Luis decidiu **rodar o motor em TODAS as linhas de novo** (o banco foi refeito; o único
dado velho é o resultado dos motores). Isso elimina duplicata e carta faltando. **Regras
que ele deu:**
1. **APAGA e coloca — NÃO sobrepõe.** Ao rodar, os resultados anteriores (`clube.build`)
   são **apagados** e reconstruídos do zero. Não é upsert por cima.
2. **Só rodar DEPOIS que a "casca" (o site/tela) estiver PRONTA pra receber** os resultados
   novos. Não apagar os resultados antes do site conseguir consumir os novos — senão a tela
   fica sem nada. Ou seja: a rodada fica atrelada à etapa do simulador/site (etapa 7/10).
3. **Fila ordenada por `overall` desc** (mais fortes primeiro) — o motor roda contínuo e
   sobe direto pro sistema, o site sempre com as cartas mais fortes no topo.

**Pré-requisito técnico da rodada (não pular):** o dado do jogo está na `carta_jogo`
(insumo), **ainda não entrou na `clube.carta`**. Antes de rodar, **aplicar
`carta_jogo → clube.carta`** com as travas (nulo não apaga · valor do dono não se toca)
pra refrescar as 1.963. Senão o motor roda em cima do dado VELHO.

## 4 · PENDÊNCIAS (pra sessão nova pegar)
1. Aplicar `carta_jogo → clube.carta` (as travas).
2. Montar a fila do motor por overall + a rodada de todas as linhas (quando a casca estiver pronta).
3. **Estilo defensivo 2027 não decodificado** — o slot só saiu 72%; 586 cartas ficam
   "Novo (2027)" sem nome até fechar o decode. (Ver ANALISE-ESTILOS-2027.md.)
4. Habilidades (65 skills) em inglês e não carregadas na `carta_jogo` — traduzir + carregar se quiser.
5. 149 cartas sem nome no jogo (menor).

## 5 · ONDE ESTÁ CADA COISA
- Extrator + CSV + relatório: `...\VER DADOS DO JOGO\`
- Manual técnico (atualizado hoje): `...\4-DOCUMENTOS\MANUAL-TECNICO.md`
- Caderno de implementações: projeto do Claude + `...\4-DOCUMENTOS\`
- Supabase projeto `trqqpsnafpbudtvvicch`, schema `clube`.
