# Contexto da sessão de 08/09/2026 — Site Novo entregue e a habilidade "Volta para marcar" em aberto

> **Complemento obrigatório de 09/09:** a decisão de bônus de estilos está em
> [Regra de estilos aprovada em 09/09](4-DOCUMENTOS/BONIFICADOR/REGRA-ESTILOS-APROVADA-0909.md)
> e no banco `clube_novo.bonificador_politica_estilo`, versão
> `estilos-funcao-20260909-v1`. Registro e conferência executável concluídos;
> integração produtiva pendente. Ler também `AGENTS.md`. Não rediscutir a regra
> por falta de contexto nem considerar a V11 como implementação desta decisão.

Documento de passagem para outra sessão. Escrito por Claude a pedido do Luis.
Ambiente: Cowork, pasta ligada `C:\Users\Luis Fernando\Downloads\ClubEFootball--main\ClubEFootball--main`,
Supabase `trqqpsnafpbudtvvicch`, esquema ativo `clube_novo`.

---

## 1. Regras que valem e não se discutem

- **Só `clube_novo` é ativo.** Todo o resto do Supabase é legado, serve para comparativo.
- **O site antigo (`1-SISTEMA`) está aposentado.** O trabalho é no `Site Novo`. O *design* continua o mesmo.
- **A tela nunca recalcula nota.** `nota_final = nota_do_motor + nota_bonus_total`. O site só lê o que o banco publicou.
- **Rótulo é dado do banco.** Nome de função se muda em `clube_novo.funcao_sistema.rotulo`, fonte única lida por todas as telas. Não se mapeia nome na tela.
- **"Função" é termo interno.** Não aparece em tela nenhuma. Na tela chama-se **especialidade**.
- **Comparar molde é comparar os 26 atributos com peso E alvo**, nunca só o topo. (Erro já cometido e registrado.)
- Netlify trata warning de ESLint como erro fatal (o Site Novo é HTML/CSS/JS puro, então não passa por isso, mas vale para CRM/Estoque).
- Netlify Drop: arrastar o zip **dentro do projeto existente**, senão cria site novo.

---

## 2. O que esta sessão ENTREGOU (fechado, já na pasta do Luis)

### 2.1 Faixa do Ranking: "EXIBIR RANKING POR"

Substituiu a barra de setores, o botão Filtros, o painel escondido e a faixa "Filtros ativos" — tudo removido.
Também substituiu uma versão intermediária de três colunas combináveis, descartada por correção do Luis.

Três abas de largura cheia, nesta ordem exigida por ele:

**POSIÇÃO · ESTILO DE JOGO · ESPECIALIDADE**

- Posição vem primeiro porque é como o jogador pensa o campo.
- **Uma exibição por vez.** Trocar de aba zera `p_posicao_nativa_id`, `p_estilo_id` e `p_funcao_id`. Escolher item de um eixo zera os outros dois. Não existe estado com dois eixos ativos.
- Posição (13) e especialidade (19) usam chips; estilo de jogo usa `<select>` porque são 36 opções.
- Linha curta de ajuda ao lado do cabeçalho, explicando o eixo aceso.
- Abas empilham abaixo de 640px.
- **Cuidado:** `p_setor` perdeu o controle na tela. O estado restaurado força `p_setor='geral'` e valida `eixo`, aceitando estado antigo sem esse campo.

### 2.2 A palavra "função" saiu da tela

Trocada por **especialidade** (palavra do próprio Luis) em:

| Arquivo | O que mudou |
|---|---|
| `ranking.js` | array `eixos`, linha 11 — **único lugar** do rótulo da aba |
| `home.js` | "a especialidade em que rende mais" |
| `boxes.js` | ajuda da etiqueta: "os melhores da mesma especialidade" |
| `ficha.js` | "Especialidade não publicada" |
| `site-shell.js` | seção "Como funciona" reescrita inteira |

**Não** foi trocado em `ficha-editor.js` / `ficha-editor-api.js` — editor interno, uso próprio.

### 2.3 Arquivos gravados na pasta (08/09, ~08:00)

`Site Novo\`: `ranking.js`, `ranking.css`, `home.js`, `boxes.js`, `ficha.js`, `site-shell.js`, `index.html`, `ficha.html`, `MANUAL-DO-SITE-NOVO.md`
Raiz: `site-novo-deploy.zip` (22 arquivos, 78 KB)

Versões de cache bumpadas para `2026090802` nos arquivos alterados.

### 2.4 Verificação feita

- `node --check` nos 5 JS alterados: OK
- Testes offline: `home.test.cjs` (7 blocos), `ranking-state.test.cjs`, `site-shell.test.cjs`, `boxes-state.test.cjs`, `site-theme.test.cjs`, os 3 de editor: **todos passam**
- Renderizado a 1440px com fixture real do ranking, console limpo, três abas conferidas visualmente
- Testes que falham são os 6 de rede (PEND-012) — o container não alcança `supabase.co`

---

## 3. Migração de banco já aplicada nesta sequência de trabalho

`rotulo_publico_das_duas_funcoes_de_driblador`:

```sql
update clube_novo.funcao_sistema set rotulo = 'Ala driblador'      where id = 12 and rotulo = 'Ala finalizador';
update clube_novo.funcao_sistema set rotulo = 'Atacante driblador' where id = 15 and rotulo = 'Atacante finalizador';
```

**Motivo, medido no `arows_snapshot`:** as duas funções chamadas "finalizador" eram justamente as que
menos valorizavam Finalização — peso 3 numa escala que vai a 12 — enquanto Controle de bola, Drible,
Condução firme, Velocidade e Aceleração estavam todas no máximo. Id, grupo, ordem, molde, pesos,
alvos e notas ficaram intactos.

> Atenção: fixtures de teste antigas ainda mostram "Atacante Finalizador" nos prints. O banco já devolve o rótulo novo.

---

## 4. O ASSUNTO ABERTO: a habilidade "Volta para marcar" (skill_id 56)

O Luis levantou: *"ela é sugerida em todos os cara e ela vende só a aceleração, eu acho que ela está errada também."*

### 4.1 O que a habilidade é (medido, não suposto)

**Texto do próprio jogo**, extraído em `clube_novo.texto_do_jogo` (seção `Any7T`, id_texto 58, pt-BR):

> `<Volta para marcar>` Permite que o jogador **pressione agressivamente o adversário que estiver com a bola desde o campo de ataque**.

Descrição oficial em inglês (Track Back): *"Improves a player's ability to apply aggressive pressure."*

**Conclusão: é habilidade de quem está À FRENTE.** Pressão a partir do campo de ataque.
Quem já joga recuado não tem de onde "voltar". O Luis apontou isso antes de eu medir, e estava certo.

### 4.2 O efeito registrado no banco

`clube_novo.habilidade_jogo`, skill_id 56:

```
efeito: {"11": {"pct": 1}, "17": {"pct": 1}}
efeito_por_codigo: {"PB:390:6": {"pct":1}, "PB:486:6": {"pct":1}}
efeito_legivel: "Aceleração +1% · Talento defensivo +1%"
```

Índice 11 = Aceleração · Índice 17 = Talento defensivo.
**Então ela TEM a parte de marcação** — o Talento defensivo. Não é só aceleração no dado.

### 4.3 Por que na prática ela "vende só a aceleração"

Porque **Talento defensivo tem peso ZERO em 11 das 19 funções** — justamente as funções ofensivas,
que é onde a habilidade faz sentido:

| Peso de Talento defensivo | Funções |
|---|---|
| **0** | Centroavante fixo, Centroavante móvel, Falso nove, Atacante infiltrador, Atacante criador, Atacante driblador, Meia ofensivo, Meia armador, Meia de arranque, Ala driblador, Ala cruzador |
| 3 | Lateral ofensivo |
| 7 | Volante de construção |
| 12 | Lateral defensivo, Zagueiro de combate, Volante de contenção, Zagueiro de saída |
| 0 (mas aceleração 0 também) | Goleiro ofensivo, Goleiro defensivo |

Medição no Atacante driblador (id 15), ganho bruto da habilidade = **12,12**, e os 12,12 vêm
**inteiros da Aceleração** (101 × peso 12 × 1%). O Talento defensivo é multiplicado por peso 0 e some.

**Este é o achado central:** no lugar em que a habilidade pertence, o molde joga fora metade dela.
É o mesmo tipo de problema do rótulo "finalizador" — o dado não bate com a realidade do jogo.

### 4.4 O buraco no bloqueio

`clube_novo.habilidade_funcao_bloqueio_otimizador` tem 36 habilidades bloqueadas por função.
A "Volta para marcar" é a **única da família defensiva com zero bloqueios**:

| Habilidade | Funções bloqueadas |
|---|---|
| Carrinho (60) | 9 |
| Afastamento acrobático (64) | 9 |
| Interceptação (57) | 8 |
| Bloqueador (58) | 8 |
| Marcação individual (55) | 6 |
| **Volta para marcar (56)** | **0** |

Mas — e aqui está a correção que o Luis fez — as irmãs são bloqueadas **no ataque**, e esta não deveria
seguir o mesmo padrão, porque ela é o oposto delas: é habilidade DE atacante.

### 4.5 Onde ela aparece hoje (54.360 linhas publicadas, 9.821 com as 5 habilidades adicionais)

| Função | % das builds com 5 habilidades | nº de builds |
|---|---|---|
| Zagueiro de combate | 77,8% | 186 |
| Lateral defensivo | 73,3% | 165 |
| Zagueiro de saída | 73,2% | 175 |
| Centroavante móvel | 51,5% | 202 |
| Lateral ofensivo | 47,6% | 107 |
| Atacante driblador | 33,2% | 267 |
| Centroavante fixo | 32,1% | 158 |
| Meia de arranque | 24,3% | 105 |
| Falso nove | 20,1% | 198 |
| Atacante infiltrador | 16,5% | 177 |
| Meia ofensivo | 13,4% | 144 |
| Ala driblador | 12,6% | 102 |
| Atacante criador | 12,5% | 101 |
| Ala cruzador | 7,3% | 59 |
| Volante de contenção | 5,5% | 16 |
| Volante de construção | 3,7% | 11 |
| Meia armador | 1,9% | 8 |
| Goleiros | 0% | 0 |

Total: **2.181 builds publicadas** carregam a habilidade.

Ironia medida: ela aparece MAIS nos zagueiros (78%), onde não faz sentido nenhum, porque lá o
Talento defensivo tem peso 12 e a metade defensiva dela conta.

### 4.6 A PERGUNTA QUE ESTÁ NA MESA (o Luis ainda não respondeu)

Onde bloquear a habilidade. Opções apresentadas, com o custo de rebuild:

| Opção | Funções | Builds invalidadas |
|---|---|---|
| A — só os zagueiros | Zagueiro de combate, Zagueiro de saída | 361 |
| B — zagueiros + Lateral defensivo + Volante de contenção | 4 funções | 542 |
| C — toda a defesa e o meio recuado | + Volante de construção, Meia armador | 561 |

Invalidar significa que essas linhas voltam para a fila do Otimizador.

### 4.7 A pergunta MAIOR, que ninguém respondeu ainda

Se a habilidade é de atacante que pressiona, e nas funções de atacante o Talento defensivo tem peso 0,
**o molde das funções ofensivas está certo em dar peso 0 a Talento defensivo?**
Ou existe uma classe de habilidade — comportamento defensivo de jogador ofensivo — que o modelo atual
não consegue valorar de jeito nenhum?

Isso não foi decidido. É decisão do Luis, é conhecimento de jogo, e mexe em molde, não em bloqueio.

### 4.8 Mecanismos disponíveis para agir (todos no banco, nenhum na tela)

1. `clube_novo.habilidade_funcao_bloqueio_otimizador` — bloqueio cirúrgico por função. É o lugar certo para "não faz sentido aqui".
2. `habilidade_jogo.vetada = true` + `vetada_motivo` — tira de todas as funções, continua na sugestão. Precedente: skill 48 "Especialista em pênalti" e skill 69 "Super substituto", ambas com motivo *"Luis 10/08: nao pode vir como adicional; continua na sugestao"*.
3. Mexer no molde (`arows_snapshot` / peso de Talento defensivo nas funções ofensivas) — decisão pesada, invalida muito mais coisa.

### 4.9 Outras habilidades sem bloqueio nenhum (conferidas, todas OK)

Passe em profundidade, Passe de primeira, Passe na medida, Passe aéreo baixo, De letra, Controle da
cavadinha — passe e finalização são legitimamente universais.
Liderança (67) se comporta sozinha: só entra em defensores, porque Dedicação defensiva tem peso 0 no ataque.
Espírito guerreiro (70) é universal mas mexe em Cabeceio/Resistência, que valem para todos.
**Só a 56 é anômala.**

---

## 5. Pendências que continuam abertas

| Código | O que é | Estado |
|---|---|---|
| PEND-011 | Tema claro completo da Ficha — ~286 cores fixas no `ficha.css` | Espera aval visual do Luis. A moldura da página já acompanha o tema; o painel mantém a paleta aprovada. |
| PEND-012 | 6 testes de rede não rodados | O container não alcança `supabase.co` |
| PEND-013 | Tela Elenco | Espera decisão do Luis — ele disse que vai fazer, é página muito mais complexa |
| — | Bloqueio da "Volta para marcar" | **Pergunta na mesa, item 4.6** |
| — | Peso 0 de Talento defensivo nas funções ofensivas | **Pergunta na mesa, item 4.7** |

### Suspensos por decisão do Luis
- Contexto/régua da nota na tela ("não quero muita poluição")
- Comparador de dois cards (vai ser aba separada, só depois de fechar o que já existe)
- "Publicados nas últimas horas" (não faz sentido, ele só lança o site depois de publicar tudo)
- Filtro dentro da busca (muita informação que não vai ser usada — "todo mundo busca pela foto do card")
- Abrir ficha por ID (ele concordou que não precisa ter)

### Achado estrutural anterior, ainda de pé
MLD/LD não somem por bug de tela: as linhas existem com Bonificador mas sem Otimizador, então nunca
selam. **122.590 linhas** estão nesse estado globalmente. O Otimizador é o gargalo.

---

## 6. Como o Luis trabalha (obrigatório)

- Não é programador. **Nunca usa terminal.** Tudo por navegador: GitHub online, Netlify dashboard/Drop, Railway dashboard, Supabase dashboard.
- **Arquivos completos, prontos pra copiar e colar.** Nunca trecho solto, nunca diff.
- Passo a passo numerado, com links clicáveis.
- Comando já montado, pronto pra colar — ele não edita código na mão.
- **Sempre em português.**
- Mínimo de comentário na janela, execução sem enrolação.
- Quando formos mexer num módulo, ele manda os arquivos atuais na hora — não trabalhar em cima de código velho.
- Ele corrige quando a conclusão está errada, e costuma estar certo. Medir antes de propor.
