# PLANO DE AÇÃO — v3 (25/08) · A CASA PRIMEIRO, OS MORADORES DEPOIS

> Princípio do Luis, na palavra dele: **"a gente vai arrumar a casa primeiro.
> Depois a gente vai colocar os moradores novos. Aproveitando o que a gente já
> tem — refazendo só o que foi feito errado."**

Tradução: NADA novo entra (coleta nova, login, comercial, lançamento) enquanto a
reestruturação não estiver pronta e provada. A casa se constrói com o que JÁ
existe no banco e nas coletas feitas.

---

# FASE 1 · A CASA — reestruturar tudo com o que já temos

## 1A · O banco novo (as nove fases da rota, agora como obra principal)

| passo | o quê | de onde vem o dado (tudo JÁ existe) |
|---|---|---|
| 0 | fotografia (backups das fontes) | — |
| 1 | estrutura das 6 camadas nasce vazia, migração versionada | decisão inicial: fundação = `clubef_read_v2` do GPT ou do zero |
| 2 | dicionários — função por CÓDIGO, ímpeto, habilidade, técnico, estilo, box, atributo | `funcoes` + `insumo_*` + catálogos do efootballdb (410 boosters, 2.014 boxes — lote-0001 validado pelo GPT, entra) |
| 3 | a carta + carta_impeto **já com a verdade dos 870** (699 + os 44 reclassificados) | `cards_base` + canônico v2 + coletas de 23-24/08 |
| 4 | a receita versionada (molde v1 vigente) | `insumo_molde` (494) + `parametros` |
| 5 | o resultado: build ÚNICA (builds ⋈ bonus), `nota_final` gerada pelo banco; as 6.824 cópias ficam de fora por construção; builds das 870 nascem MARCADAS "recalcular" | `builds` + `bonus` |
| 6 | tela = VIEW da build · topos religados · medianas MEDIDAS por função (a MED duplicada de 18/08 morre aqui) | build |
| 7 | **PROVA DOS NOVE**: contagens por função = builds; top-10 por função; Neymar 87 com 441,4 visível; 100 cartas campo a campo; % topo ≤ 100 | tudo |

## 1B · O sistema arrumado (junto com o banco)
- O site passa a consultar a casa nova: por CÓDIGO, mostrando rótulo; a carga
  vira consulta à view (paginada, assíncrona, com erro recuperável — fim da tela
  preta); MED/FILA/ESTV saem do código e vêm do banco; o 1,5 MB congelado vira
  consulta; um `popstate` só; as 13 globais duplicadas limpas.
- `gera_encaixe`/`sobe_a_tela`/`subir_as_linhas_agora` **se aposentam** — tela é
  view, ninguém mais "sobe tela". O motor (`fonte_unica`) passa a ler da casa nova.
- Homologação visual completa (Elenco, Ficha, Ranking, voltar, salvar, celular).

## 1C · A virada e a limpeza
- Acerto de diferença (banco vivo) → site vira a chave → motor → vigia.
- Legado renomeado `_legado` (apagar só com ordem do Luis, um mês depois).
- Limpar os ~950 MB do `clubef_stage_v2` pelo roteiro do GPT: exportar batches
  1,3,4,11,12 com contagem+sha256+leitura conferida, respeitar FKs, conferir
  `pg_total_relation_size` depois.
- Projeção (se a fundação for a v2): rebuild só de elegíveis, canário de 25 →
  lotes de 100 → 250 (recomendação registrada do GPT).

**✅ A CASA ESTÁ PRONTA quando:** prova dos nove fechada + homologação visual
fechada + site inteiro servido pela casa nova + legado aposentado.

---

# FASE 2 · OS MORADORES — só depois da casa pronta

| ordem | morador | detalhe |
|---|---|---|
| 2A | **Marco zero da coleta** | retomar a T7 (`await ClubEFT7.retomar()`, faltam 28.776; ⛔ não limpar o Chrome nem `coleta-efhub-dados-fotos`); os 8.521 completos entram da lista pronta (`IDS-JA-COMPLETOS-EXCLUIDOS.txt`); `player_id` normalizado — tudo entrando pelas portas da casa nova, com assinatura |
| 2B | **A RODADA ÚNICA do motor** | cartas novas + as 870 marcadas + bônus — uma sessão só, na máquina do Luis, sob ordem dele |
| 2C | **O Alimentador** | unifica os coletores; roda SÓ na máquina do Luis; GitHub = backup; assume o incremental diário |
| 2D | **Login + comercial** | auth + camada 6 (RLS) · créditos Stripe · entitlement real · posição grátis (mediana, após estudo) |
| 2E | **Chaves** (por último, ordem do Luis) | rotacionar sb_secret/sb_publishable/ADMIN_TOKEN vazadas em 05/08; atualizar config.txt, Railway, site |
| 2F | **LANÇAR** | gates: casa pronta + 2A + 2B + 2D + 2E |

---

# REGRAS DA OBRA (valem nas duas fases)
1. O legado fica no ar, intocado, até a virada (1C).
2. Cada passo é migração versionada com PROVA medida; o Luis aprova passo a passo.
3. O motor nunca roda sem ordem do Luis — e roda UMA vez no processo todo (2B).
4. Todo documento vivo desta obra mora em `Clubefootball 2026-08-25\4-DOCUMENTOS`.
5. O manual técnico é atualizado a cada passo concluído (Parte B → Parte A).

# PRIMEIRA DECISÃO DA FASE 1 (única coisa pendente pra começar)
**A fundação da casa: aproveitar o `clubef_read_v2` do GPT (42.807 cartas, ímpetos
corrigidos, contrato de projeção pronto) ou nascer limpo no desenho das seis
camadas?** O Claude entrega o comparativo medido dos dois caminhos como primeiro
ato da fase 0 — junto com a fotografia.
