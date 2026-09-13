# CADERNO DE IMPLEMENTAÇÕES — arquitetura do sistema

## Extrator 5.4.0.3: Sobreposição e conferência manual, 12/09/2026

Sobreposição corrigida de bit135 para bit192/largura7, comprovada em 65/65
técnicos contra a referência eFHUB. Conte=69. Contrato do banco e núcleo
atualizados; teste físico passou; 130 proteções manuais para os 65 técnicos
registradas e relidas. Níveis distinguem prova física de valor manual na
conferência. Executável 5.4.0.3 compilado e janela conferida. Veja
[Evidência de Sobreposição](EXTRATOR/SOBREPOSICAO-192-1209.md).

A varredura 224315 concluiu sem importar: 184 cartas novas e 375 alteradas.
Nova rodada pelo aplicativo foi iniciada com o endereço corrigido. Recarga,
boosts, molde v6 e fila integral permanecem etapas em execução.

## Implementação principal iniciada em 12/09/2026

Banco, código, manuais e tela são critérios obrigatórios em cada etapa.
Extrator 5.4.0.2: estado da carga corrigido para só concluir após leitura
independente; proteção `valor_do_dono` ampliada aos 33 destinos; diagnóstico
de fonte atualizada incluído. Veja
[Prioridade manual](EXTRATOR/PRIORIDADE-CORRECOES-MANUAIS.md) e
[Manual do Extrator](../7-VARREDURA-DO-JOGO/DOCUMENTACAO/MANUAL-DO-EXTRATOR.md).

O CPK baixado em 12/09 foi examinado pelo próprio aplicativo. Contrato de
leitura atualizado com hashes observados e autorização anterior invalidada;
comparação integral ainda em execução. Isso não encerra importação, v6,
reaproveitamento dos bônus, fila nova nem entrega da Máquina 2.

## Enviador e critério de encerramento V12 — 09/09/2026

O critério aprovado é terminar com toda linha vigente correta e gravada em `clube_novo`, reaproveitando o que já está correto e refazendo somente o necessário. Não declarar encerramento a partir de instalação, JSON local ou ausência de linhas elegíveis de um lote. Preservar históricos, antecessores e a ordem existente. A normalização permanece inalterada.

O operador confirmou a instalação do reparo anterior `REPARO-MOTORES-V12` (backup `motores-retomada-v12-9866126a7fa84046b2e713e53878ce31`). O **novo REPARO-ENVIADOR-V12** corrige a leitura de fotografias antigas e preserva JSONs de outra fórmula sem enviá-los. Atualiza fonte e EXE com backup; mesmos BATs. 44 testes e instalador/EXE conferidos. A instalação deste novo reparo na Máquina 2 ainda não foi confirmada.

Correção de terminologia dos registros anteriores: `lotes_sem_pendentes` significa **sem linhas elegíveis na fotografia atual**, não necessariamente lote inteiro concluído. Dos 1.220 IDs antigos, 1.138 têm resultado e 82 já estão no prefixo. Os demais seis lotes têm 126.318 elegíveis esperando V12. Os 28 antecessores com bloqueios já têm substitutas V12; as seis exclusões anteriores por falta de evidência são cartas removidas, sem publicação. Não reabrir antecessores nem inventar entradas de cartas removidas.

Detalhes e limites da conferência: `4-DOCUMENTOS/OTIMIZADOR/HABILIDADES-0909/AUDITORIA-ENVIO-E-COBERTURA-V12.md`. Esta auditoria foi somente leitura; não declara que a produção ou o envio terminaram.


## Reparo de retomada HTTP 403 e encerramento — 09/09/2026

A execução na Máquina 2 expôs uma permissão ausente na consulta da carta V3, após a preparação já validada. Corrigido o acesso restrito ao catálogo no banco; HTTP e gravação testados. A única falha 488143 foi recuperada, com prioridade preservada. Bonificador agora retorna código 2 em falha e não anuncia conclusão indevida. Novo pacote único `REPARO-MOTORES-V12` inclui também a correção de prioridade do Otimizador; instalar em `2-MOTORES` por `APLICAR.cmd`, preservando os BATs anteriores. Ver `4-DOCUMENTOS/BONIFICADOR/REPARO-RETOMADA-403-V12.md`. Os registros de prontidão anteriores descrevem a conferência parcial daquela etapa.


## Reparo de prioridades concluídas — 09/09/2026

O processador aceita lotes prioritários que a fotografia declarou sem pendências, mantendo-os na seleção histórica. A execução filtra somente esses lotes já concluídos; prioridades desconhecidas/repetidas continuam bloqueadas. Fonte e EXE oficiais atualizados, 36 testes aprovados e instalador/EXE conferidos em espelho isolado. Ordem, resultados e recibos preservados. Entrega incremental `REPARO-PRIORIDADE-V12`; copiar para `OPERACAO-LOCAL-JSON` e executar `APLICAR.cmd`. Os BATs principais permanecem iguais. O pacote consolidado REFILA-V12 também incorpora o reparo. A instalação incremental na Máquina 2 ainda depende do operador. Registro: `4-DOCUMENTOS/OTIMIZADOR/HABILIDADES-0909/REPARO-PRIORITARIOS-CONCLUIDOS.md`.


## Retomada V12 conferida — 09/09/2026

Pacote do Bonificador completo validado (15 arquivos). Retomada, controle e primeira reserva passaram em transação revertida; lote continua pausado, com 14.107 pendentes. Corrigidos no banco o filtro da auditoria e as restrições de versão do lote, agora compatíveis com os conjuntos coerentes V11/V12. Usar o mesmo `OPERACAO-CORRECAO-FISICA/INICIAR-REPROCESSAMENTO.bat`. Nenhuma nova cópia necessária por esses ajustes. Detalhes em `4-DOCUMENTOS/BONIFICADOR/RETOMADA-CONFERIDA-0909.md`.


## Encerramento confirmado em 09/09/2026

A correção seletiva dos bônus de estilo terminou: **67.795 resultados e 7.455 publicações concluídos, zero pendências e erros nessa operação**. O banco e o painel confirmaram o encerramento em 2026-09-09T08:13:50.106412+00:00. As nove publicações finais foram conferidas no contrato da Ficha, preservando a revisão de habilidades do Otimizador e a ordem dos lotes. A falha do UPDATE de encerramento foi corrigida no banco e no SQL oficial.

Evidência e alcance: [Conclusão dos bônus de estilo](BONIFICADOR/CONCLUSAO-BONUS-ESTILOS-0909.md). A produção geral do Bonificador e as execuções do Otimizador têm estados próprios; este encerramento não significa que seus lotes foram executados. Os registros de andamento abaixo são históricos.

## Política vigente de habilidades — 09/09/2026

A política `habilidades-funcao-20260909-v1` está aplicada no `clube_novo` e no runtime oficial da Máquina 1. A matriz vigente tem 325 pares habilidade/função. O motor conserva de zero a cinco adicionais úteis; não preenche vagas sem ganho. Todas as sugestões automáticas, inclusive gêmeas de builds antigas, respeitam os bloqueios atuais da função. A escolha manual do usuário e as habilidades nativas continuam livres desses vetos estratégicos.

Banco, fontes, executável e fotografias locais foram sincronizados; lotes continuam pausados e na mesma ordem. A normalização da nota não mudou. A revisão local identificou 4.509 linhas para análise posterior; nenhum resultado antigo foi regravado ou despublicado nesta etapa. A instalação na Máquina 2 e a publicação do frontend são estados separados.

Regra completa, matriz, migrações, testes e evidências: [Habilidades por função V12](OTIMIZADOR/HABILIDADES-0909/REGRA-APROVADA.md). Os registros anteriores abaixo conservam o contexto da época e não substituem esta revisão.

## Retomada futura na Máquina 2 — arquivos preparados

Os arquivos V12 do Bonificador completo estão preparados para cópia direta.
O operador usa o mesmo INICIAR-REPROCESSAMENTO.bat após terminar a correção de
estilos. Antes disso, o comando não inicia nem reserva linhas. A versão do lote
e a política geral só serão atualizadas no início solicitado pelo operador.
Detalhes: [Entrega da Máquina 2](BONIFICADOR/ENTREGA-MAQUINA-2-V12.md). Os registros anteriores abaixo são históricos.

## Operação atual — correção seletiva de estilos V12

O executor autônomo foi instalado e iniciado na máquina oficial. Corrige somente
os estilos de 67.795 resultados e atualiza 7.455 publicações, mantendo as notas
anteriores disponíveis até cada troca ser confirmada. Não declarar conclusão
antes do readback final do banco. Apenas o schema clube_novo é operacional.
A fila geral permanece pausada; a Máquina 2 será atualizada depois.
Código/EXE V12 estão preparados localmente. A política permanece com implantação
geral pendente; a execução seletiva já aplica a regra.
Fonte operacional: [Executor de estilos V12](BONIFICADOR/EXECUTOR-ESTILOS-V12.md).
Os registros anteriores abaixo descrevem etapas históricas.

## Atualização de 09/09 — decisão de bônus de estilo preservada

**Decidido por Luis, registrado no banco e no manual; integração produtiva pendente.**
Referência: [Regra de estilos aprovada em 09/09](BONIFICADOR/REGRA-ESTILOS-APROVADA-0909.md).
Banco: `clube_novo.bonificador_politica_estilo`, versão
`estilos-funcao-20260909-v1`. Principal definido pela função vale 1,0; secundário
0,5; cada um depende de ativação na posição. Somente Defensor Criativo e Lateral
Defensivo têm a promoção excepcional descrita na regra.

25 casos numéricos, quatro pendências de ativação e duas entradas inválidas
foram conferidos no banco. Falta integrar a execução e corrigir os resultados;
o item V11 abaixo descreve a entrega de 07/09 e não conclui esta nova implantação.
Os quatro estilos sem definição permanecem pendentes de extração futura.

**Aberto 25/08 · atualizado 27/08 (sessão da carga nova + motores no banco)**

Estados: `ANOTADO` (a discutir) · `DECIDIDO` (Luis cravou, falta executar) · `FEITO`.
Só o Luis muda estado. Sessão nenhuma executa item `ANOTADO`.

---

# 🔥 27/08 — O QUE FECHOU HOJE

| item | estado | prova |
|---|---|---|
| **Carga nova completa** | ✅ FEITO | 42.803 cartas · **todas** com corpo, aptidões, habilidades, estilos de IA e pé ruim |
| **Estilo defensivo (slot 2)** | ✅ FEITO | bit **440** largura 6, no arquivo certo (`ST\Download`). Era 72%, agora fechado. 4.100 cartas com o 2º slot |
| **Habilidades / aptidões / IA** | ✅ FEITO | eram 0 de 42.803. O extrator lia e descartava na exportação |
| **Corpo (12 medidas)** | ✅ FEITO | `PlayerAppearance.bin`, registro de 64 bytes. Antes vinha do site |
| **Pé ruim · lesão · forma** | ✅ FEITO | bits 478, 578, 542/543, 582 |
| **Level cap** | ✅ RESOLVIDO POR DERIVAÇÃO | `(card_id >> 38) & 255` = o tipo da carta. Separa cresce/não-cresce com **98,12%** |
| **A fila** | ✅ FEITO | `clube.fila`, **125.932 linhas** · 6,04 funções por carta (o arquivo morto tinha 6,28) |
| **Motores lendo do banco** | ✅ FEITO | `fonte_unica.py` v2 · `roda_lote_v6.py` sem interruptor · `motor_bonus.py` v7 |
| **Bônus de estilo por POSIÇÃO** | ✅ FEITO na V11 em 07/09 | 1,0 no slot dominante ativo + 0,5 no outro slot ativo, teto 1,5; função/molde não ligam o bônus |
| **`clube.build` truncada** | ✅ FEITO | arquivo morto em `clube.build_arquivo_2608` (17.798) |

**Auditoria depois de tudo: 0 FALHA · 15 CONHECIDA · 36 OK.**

## O achado do dia: o tipo da carta mora no card_id

```
(card_id >> 38) & 255

grupos 71, 192, 196, 200, 204  →  NÃO CRESCEM (cap 1, orçamento 0)  · 935 cartas, 934 acertos
grupos 0, 64, 68, 128, 129, 132 → CRESCEM (cap 29 a 35)             · 2.309 cartas, 2.150 acertos
```

Sai de uma conta no id. Sem arquivo, sem coleta, sem efHUB.

## A fila agora confere a migração

```
prioridade 0 →  16.381 linhas · 2.756 cartas  ← JÁ RODARAM ANTES, vão primeiro
prioridade 1 →  lançamentos (furam a fila)
prioridade 5 → 109.551 linhas · 18.669 cartas · por overall desc
```

Ordem do Luis, 27/08: *"é importante a gente rodar primeiro as que a gente já rodou antes,
pra ver se está certo. Se estiver errado, a gente para nas primeiras."*

## Automático, sem ninguém apertar nada

- Gatilho `carta_entrou`: carta nova entra → a fila se enche sozinha. Carta que mudou →
  a build velha é apagada e ela volta pra fila.
- Gatilho `cap_do_id`: deriva `grupo_id`, `level_cap` e `orcamento` do próprio `card_id`.
- `gravar_build()`: grava na `clube.build` **e tira a linha da fila**, no mesmo comando.

---

# 👉 A PRÓXIMA COISA — RODAR O MOTOR

Tudo pronto. Falta o Luis rodar o `roda_lote_v6.py` na máquina dele.

**A conferência:** as 2.756 primeiras já rodaram antes. Comparar o `b1` novo com
`clube.build_arquivo_2608` nas primeiras dezenas. Divergiu → para.

`marcar ≠ rodar`. O motor só dispara sob ordem do Luis.

---

# 📌 O QUE AINDA FALTA

## 1 · Limpeza do banco — `DECIDIDO`, falta rodar
Blocos 1 a 4 do `4-DOCUMENTOS\LIMPEZA-DO-BANCO.sql`. Tira 21 tabelas do `clube` (76 → 55).
O bloco 5 depende de reescrever 3 funções de auditoria. O bloco 6 (schema `public` inteiro)
só depois que o motor estiver rodando pelo banco e provado.

## 2 · Etapa 7 — a conta sai do navegador
O `arows` que a tela recebe carrega **peso e alvo** — que *são* o molde. Com a chave que
está no próprio JS, as 19 funções se reconstroem em 2,4 segundos. Só fecha quando a conta
for pro servidor e o `arows` parar de sair do banco. **É um deploy só, atômico.**

## 3 · O Railway roda um arquivo que não está na pasta
`servidor:app` no Custom Start Command; a pasta tem `app.py`. O serviço responde `POST /nota`,
rota que não existe no `app.py`. **Baixar do repositório o que está realmente no ar.**

## 4 · A validação do /avaliar recusa as builds do próprio motor
**Não é decisão do Luis — é conserto, e ele já está pronto no banco.**

Retificado em 25/08: o que se dizia (*"o pool do banco discorda do do motor em 2.681 de
2.836 cartas"*) comparava duas coisas diferentes. O `falta_pool` varia **por função** na
mesma carta (a carta `89130772077328` tem 8 tamanhos em 10 funções, de 22 a 30);
`carta_habilidade` relação `espaco` é outra lista, **por carta**.

**A medida certa:** 6.000 habilidades usadas em builds não marcadas — **6.000 de 6.000
estão no `falta_pool` da própria build. Zero fora.** O motor nunca escolheu fora do pool.

Quem erra é a validação do `/avaliar`, que confere contra `carta_habilidade` — lista mais
curta, onde só 3.552 das 6.000 aparecem.

**Conserto:** o serviço passa a chamar `public.pool_da_funcao(card_id, funcao)`, que
devolve o `clube.build.falta_pool` gravado quando o motor rodou. Nenhuma fórmula a deduzir.
⚠️ **Depende do item 3** — não dá pra consertar um arquivo que não está na pasta.

## 5 · Level cap real — sem pressa
3.243 reais · 39.560 estimados pelo grupo. O coletor do efHUB (`coletor_efhub.js`) roda
quando o Luis quiser e continua de onde parou. Cap real sempre vence o estimado.

## 6 · O site ler os dois estilos
O `motor-e-ficha-base.js` só conhece **um** estilo (`c.modelo`). O `EST_POS` dele tem nomes
velhos (Provocador, Zagueiro ofensivo/defensivo) e nenhum dos 8 de 2027.
⚠️ Mas o bônus **vem pronto do motor** — o JS é rede de segurança. Prioridade baixa.

## 7 · Vaga de habilidade estourada — 2.941 builds
O motor sempre montou 5 habilidades, mas a regra é de 0 a 5 por carta. Medido: cartas com
0 vagas receberam builds com média 4,98 habilidades; com 1 vaga, 4,95. **A nota dessas
está inflada.** São 2.941 builds de 488 cartas, todas já marcadas para recalcular.
**A rodada nova resolve sozinha** — não se conserta na mão.

## 8 · Menores
- 149 cartas sem nome no arquivo do jogo.
- Etiquetas de algumas funções vão mudar (falta a lista de/para do Luis).
- As 720 builds com bônus furado: some na rodada nova.

---

# ⛔ ERROS DESTA SESSÃO — para não repetir

1. **Chamei o slot 1 de "ofensivo".** É o slot **legado**, e nele convivem estilos ofensivos
   e defensivos (*Goleiro defensivo*, *Lateral defensivo*, *O destruidor* moram lá).
   Isso gerou alarme falso de "299 goleiros errados".
2. **Disse que ímpeto e level cap eram "dado de servidor".** Desculpa de quem não achou —
   o ímpeto a gente extrai desde sempre (bits 308/288).
3. **Cacei no arquivo errado** (dt200 do Steam) quando o certo é o `ST\Download\dt870`.
4. **Afirmei `A = B × 4` como regra** dos dois catálogos de estilo. É coincidência —
   o Casillas quebra (64 no A é *Goleiro adiantado*, 16 no B é *Goleiro ofensivo*).
5. **Marquei `regra_funcao` para apagar** — e é ela que define a fila. Por pouco.
6. **Ia coletar 400 fichas no efHUB** quando o banco já tinha 3.165 caps.
7. **Não usei os documentos do projeto antes de medir e opinar.** Sete erros já estavam
   respondidos lá.

**A lição:** ler o caderno e os documentos ANTES. E medir na fonte, nunca supor.

---

# REGRA 00 — ONDE MORAM AS COISAS

```
1-SISTEMA\              a tela que vale (lê casa_tela)
2-MOTORES\              travas.py
4-DOCUMENTOS\           manual e relatórios
5-COLETA-EM-PARALELO\   o coletor V8
6-AVALIADOR-NO-RAILWAY\ o serviço  ⚠️ não é o que está no ar
7-VARREDURA-DO-JOGO\    Extrator-ClubEfootball.html  ← o arquivo do jogo
ClubEfootball-V3-main\...\programas\   ← É AQUI QUE OS MOTORES RODAM
os dados ..............  Supabase, sempre
```

**A tabela principal é a `clube.carta_jogo`** — o cadastro do jogador, 42.803 linhas.
A `clube.carta` (41.404) é a velha; hoje só guarda os 3.243 level_cap reais. Quando eles
migrarem, ela pode ser apagada.

---

# PRINCÍPIO 0 — O BANCO É VIVO

```
EXTRATOR (navegador do Luis) ──grava──► clube.carta_jogo
MOTOR (máquina do Luis, sob ordem dele) ──grava──► clube.build
USUÁRIO (site, com login) ──grava──► a tabela DELE
DERIVADOS (casa_tela, topo, mediana) ── NINGUÉM escreve ──
```

**Chave sempre pelo CÓDIGO, nunca pelo nome:** `card_id`, `slot_ofensivo_id`,
`slot_defensivo_id`, `impeto_s1`, `funcao.codigo`, `posicao.codigo`.
O nome é etiqueta e já quebrou três vezes.

⛔ **Uma sessão por vez escrevendo no banco.** Duas ao mesmo tempo foi como 959 cartas
ganharam id 64/68 numa coluna de 6 bits (máximo 63).

---

# ORDEM DE EXECUÇÃO — onde estamos

```
✅ 1 · a receita completa
✅ 2 · a caixa de entrada        (o Alimentador foi aposentado — a fonte é o jogo)
✅ 3 · o cadastro único           clube.carta_jogo, 42.803
✅ 4 · proveniência + completude
✅ 5 · o que nasce do código
✅ 6 · auditoria dos motores
🔄 7 · O SIMULADOR E A PORTA      o AVALIAR está no ar. Falta a ficha pedir ao servidor
✅ 8 · A FONTE = O JOGO           extrator 29 colunas · carga completa · fila montada
👉 9 · A RODADA DE TODAS AS LINHAS   TUDO PRONTO. Falta o Luis rodar.
  10 · homologação → publicar
  11 · login + comercial → CHAVES → LANÇAR
```

## 09/09/2026 — correcao pontual completa e refila V12

Preparados dois lotes corretivos com 4.475 linhas: 938 recomposicoes completas sem busca e 3.537 buscas integrais. Preservados ordem dos lotes anteriores, historico e publicacoes. Registrados 28 antecessores ja substituidos e seis lacunas de orcamento. Recompositor oficial, console UTF-8 e preservacao de lotes encerrados na renovacao. Estado/provas em `OTIMIZADOR/HABILIDADES-0909/CORRECAO-PONTUAL-E-REFILA.md`.
