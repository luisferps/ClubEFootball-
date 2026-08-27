# RELATÓRIO DA OBRA — fases 0 a 7 EXECUTADAS (25/08, madrugada)

**A casa está de pé.** O schema `clube` existe no Supabase, ao lado do legado
(que não foi tocado em nada — só a staging morta do GPT foi apagada, por tua
ordem, liberando 951 MB). Nove migrações registradas em `clube.migracao`.

## O que foi construído e carregado

| camada | tabela | linhas | fonte |
|---|---|---:|---|
| 0 | coleta (assinaturas) + fotografia das 23 fontes | 3 + 23 | — |
| 1 | funcao (POR CÓDIGO) · atributo · impeto · impeto_efeito · habilidade · tecnico · estilo(+valor) · box | 19 · 26 · 350 · 1.540 · 65 · 1.664 · 25(144) · 2.014 | funcoes, insumos, **efootballdb** |
| 2 | carta · carta_impeto · carta_habilidade | 6.953 · 13.904 · 128.574 | cards_base + **canônico v2** |
| 3 | receita v1 (molde 494 + parâmetros 13), VIGENTE | 507 | insumo_molde |
| 4 | build ÚNICA (builds⋈bonus), nota_final GERADA pelo banco | 17.798 | builds + bonus |
| 5 | tela = VIEW · topo_funcao · mediana_funcao | views | build |
| 6 | usuario_estado (RLS por auth.uid), vazia | 0 | — |

## A PROVA DOS NOVE — todas verdes ✅

1. **Contagem por função** novo × legado: diferença **ZERO** nas 19.
2. **O teste do Neymar 87**: a melhor função dele **APARECEU** — Atacante
   criador, b1 441,4, nota final 442,95 (94,29% do topo). Era invisível no site.
3. **100 pares sorteados**, b1 campo a campo novo × legado: **0 divergências**.
4. **% do topo**: **nenhuma** linha acima de 100 (o "110%" morreu).
5. **Cartas** (nome/ovr/tier × cards_base): **0 divergências**.
6. **Molde v1** × insumo_molde: Σ|Δalvo| = **0,0** · pesos diferentes = **0**.
7. **A MED duplicada morreu**: mediana MEDIDA por função — Falso nove e
   Centroavante móvel agora têm números PRÓPRIOS e diferentes.
8. **As 6.824 cópias não existem** na casa — por construção (17.798 = builds).
9. **Velocidade da view**: top-100 de uma função em **20 ms** — não precisa
   materializar nada.

## Os ganhos que vieram junto

- **As 870 cartas com ímpeto divergente estão marcadas**: `recalcular = true`
  em **5.119 builds** (teu palpite estava certo: não eram 870 linhas, eram
  5.119) — prontas pra UMA rodada de motor, quando você mandar, com o motivo
  gravado linha a linha (699 divergentes / 44 pendentes / 127 ambíguos).
- **O estilo de jogo da IA — o buraco dos 93% — praticamente fechou**: o
  canônico do GPT tinha o dado (`ai_playstyle`) e agora **6.445 de 6.953
  cartas (93%) TÊM o estilo da IA** na casa nova. Antes: 1.606 de 6.469.
- **A verdade dos ímpetos por carta**: 13.904 slots com estado
  (preenchido / vaga explícita / sem ímpeto e sem vaga), direto do efootballdb.
- Banco: **1.472 → 612 MB** (a casa inteira pesa 91 MB).

## Pendências anotadas da carga (nenhuma trava)

- 1 carta sem informação de ímpeto no canônico (fallback legado disponível).
- `tipo_carta` vazio (o card_type do universo v2 está nulo — vem no marco zero).
- `impeto_efeito` cobre 1.540 pares (o resto está no `deltas` jsonb de cada
  ímpeto, que é a fonte da verdade).

## O QUE FALTA — e onde VOCÊ entra

A fase 8 (a virada: o site passa a ler a casa) é a próxima. Ela mexe no
sistema que você abre — então **preciso do teu aval em cima deste relatório**
pra começar a reescrever a carga do site contra a view `clube.tela`.
O legado continua intacto e servindo o site até lá.
