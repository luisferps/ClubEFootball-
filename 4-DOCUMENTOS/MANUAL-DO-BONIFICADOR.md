# Manual do Bonificador — ClubEfootball

**Versão 1.4 · 31/08/2026**

**Aplicativo local atual: V2.0.15.** Há um único ícone para o operador:
`2-MOTORES/BONIFICADOR/Bonificador ClubEfootball.exe`.

## Fila canônica V3

O Bonificador usa `public.bonificador_contexto_fila_v3`, contrato privado que
expõe 613 linhas de teste canônicas: 50 cartas e 19 funções. A projeção própria
`clube_novo.bonificador_par` contém os 345 pares carta×função distintos; as
linhas repetidas permanecem identificadas por `build_linha_card.id`.

Motor e aplicativo local leem `bonificador_regua_v2`, `bonificador_carta_v2`
e a fila V3. O escritor `gravar_build_bonificador_v3` é transacional, aceita
somente esse lote de teste e confere identidade, gates, versões, fingerprints
e a soma das parcelas. Ele não publica nem aceita lote produtivo.

Recuperação: `BONIFICADOR/SQL/ROLLBACK-FILA-BONIFICADOR-V3.sql`, antes de
haver resultado. Snapshot: `BONIFICADOR/RECUPERACAO/2026-08-31-ANTES-FILA-BONIFICADOR-V3`.

> Este é o manual oficial de funcionamento do Bonificador. O checklist e a pasta
> `4-DOCUMENTOS/BONIFICADOR` guardam a prova técnica, SQL de recuperação e auditorias;
> este documento explica o que o motor faz no jogo e como ele opera com segurança.

## Leitura rápida

O **Bonificador** acrescenta quatro parcelas de bônus a uma carta quando ela é usada
numa função de jogo: leitura corporal, pé ruim, estilo de jogo e estilos de IA. Ele não
cria atributos novos nem muda a carta. Ele apenas lê a fotografia canônica da carta,
aplica a régua vigente e prepara o resultado para a build do Otimizador.

O pipeline do Bonificador está pronto para operar junto do Otimizador, mas **nenhuma
carta foi gravada durante esta migração**. Ele só toca uma linha depois que o Otimizador
a confirmou e os gates canônicos a devolverem como apta.

### O que ele lê da carta

| família da carta | leitura em linguagem de jogo | para que serve no bônus |
|---|---|---|
| corpo | as 12 medidas físicas da carta | compara cada medida com o molde da função e calcula a parcela corporal |
| pé ruim | frequência de uso e precisão do pé não dominante | determina a parcela de pé ruim pela régua vigente |
| posição principal | a posição principal da carta, como GO ou CA | escolhe qual dos dois slots de estilo manda naquela posição |
| dois playstyles | o playstyle físico de cada slot | decide a casa do estilo e a ativação complementar do outro slot |
| estilos de IA | os bits de IA ativos na carta | soma a parcela de IA conforme a régua |

**Não entram no cálculo atual:** os 26 atributos de carta, habilidades, posições
secundárias, técnico, clube, liga, nacionalidade, tipo de carta e ímpetos. Eles não são
tratados como zero: simplesmente não pertencem a esta fórmula.

### O papel das regras do Bonificador

- **Régua** é a receita publicada para o motor: reúne os parâmetros, as regras de
  playstyle, os slots dominantes por posição e os gates.
- **Molde corporal** é o perfil de uma função. Ele diz como as 12 medidas são lidas,
  com direção, pesos e cortes já aprovados. O Bonificador não altera esse conteúdo.
- **Parâmetros** são os valores da régua, como tetos e escalas do pé ruim, estilo e IA.
- **Regra de playstyle** liga um playstyle físico a uma posição e, quando houver casa,
  à função canônica correspondente. A comparação é feita por ID, não por nome.

### Uma carta só segue quando é segura

O Bonificador trabalha em modo **fail-closed**: se uma relação estiver incompleta, sem
catálogo apto ou sem regra comprovada, a carta fica marcada como “não sei” e não entra
no payload de gravação. Ele nunca consulta a fotografia legada para completar um dado e
nunca inventa zero para uma ausência.

### Origem canônica e contratos

O motor de lote não abre tabelas diretamente. Ele lê `bonificador_regua_v2`,
`bonificador_carta_v2` e `public.bonificador_contexto_fila_v3`, e grava somente
por `public.gravar_build_bonificador_v3`. Esses contratos usam
IDs físicos/canônicos para carta, posição, playstyle, corpo e função. A referência
legada sobrevive apenas como fotografia de auditoria e recuperação, fora de gates e da
decisão do motor.

O motor de lote permanece em `2-MOTORES/BONIFICADOR/motor_bonus.py`. O ponto normal de
uso é o aplicativo local `2-MOTORES/BONIFICADOR/Bonificador ClubEfootball.exe`: seus
botões iniciam, acompanham e param o processo local do motor sem expor a chave ou o
schema à janela. Testes, SQL e recuperação permanecem em
`4-DOCUMENTOS/BONIFICADOR`, fora do runtime.

### Auditoria, paridade e recuperação

Antes de uma troca de origem, a versão anterior é fotografada. A auditoria compara
cardinalidades, gates, fingerprints e resultado das regras contra a referência de
sombra; divergências são registradas por carta e campo. A aplicação e o rollback são
ensaiados em transação antes do readback. As rotinas e os artefatos estão em
`4-DOCUMENTOS/BONIFICADOR/SQL` e `4-DOCUMENTOS/BONIFICADOR/RECUPERACAO`.

## 1. Finalidade e nome

O **Bonificador** calcula quatro parcelas separadas para cada par `card_id × função`:
corpo, pé ruim, estilo de jogo e estilos de IA. O runtime V9 preserva exatamente essas
parcelas, mas prepara a saída para `clube_novo.build_bonificador`. O estilo agregado é
acompanhado das duas contribuições dos slots físicos que já formavam o mesmo total;
isso não muda a fórmula.

`motor_bonus.py` e `motor dos bônus` são nomes técnicos históricos. O nome de produto
e de documentação é **Bonificador**.

O Bonificador não escolhe barrinhas, técnico, habilidades ou ímpetos. Essas famílias
podem existir na carta e no modelo novo, mas não são entradas da fórmula atual do
Bonificador.

## 2. Arquitetura ativa

| responsabilidade | origem ativa em 31/08/2026 |
|---|---|
| motor de lote incremental | `2-MOTORES/BONIFICADOR/motor_bonus.py` |
| aplicativo local de consulta e controle | `2-MOTORES/BONIFICADOR/Bonificador ClubEfootball.exe` |
| payload interno de compilação | `2-MOTORES/BONIFICADOR/windows-app/assets/BonificadorComponente.bin` |
| receita | `public.bonificador_regua_v2()` |
| carta | `public.bonificador_carta_v2(card_id)` |
| fila canônica | `public.bonificador_contexto_fila_v3(limit, offset)` → linhas pendentes e selos calculados pelo banco |
| gravação preparada | `public.gravar_build_bonificador_v3(p_resultado jsonb)` |
| destino | `clube_novo.build_bonificador` ligado à linha exata em `build_linha_card` |

`RODAR-O-MOTOR.bat` e `RODAR-TUDO.bat` executam somente o Otimizador
(`roda_lote_v6.py`). Eles não executam o Bonificador.

O arquivo executava tudo no corpo do módulo. A chave vinha de `config.txt`, não era
gravada nem impressa. O lote produtivo não foi executado nesta migração.

## 3. Mapa técnico das entradas e sua proveniência histórica

| entrada do cálculo | origem antiga | significado | fonte canônica nova | chave/gate |
|---|---|---|---|---|
| corpo da carta | `clube.carta_jogo.corpo` via `carta_do_motor` | 12 medidas usadas pela régua física | `clube_novo.carta_corpo_jogo` + `corpo_ordem` | (`card_id`,`codigo_corpo`); 12 relações; catálogo `pode_rodar` |
| ordem do corpo | `clube.corpo_ordem` via `regua_bonus` | posição de cada medida no vetor | `clube_novo.corpo_ordem` | `codigo`; `pos`; `usado_pelo_motor`; `pode_rodar` |
| molde do corpo | `clube.molde_corpo` | regra ClubEfootball por função, medida, peso e cortes | `clube_novo.bonificador_molde_corpo` | (`funcao_id`,`corpo_pos`); 228 regras operacionais, 12 por função; valores copiados fielmente |
| referência externa do molde | rótulo humano de `molde_corpo.funcao` | liga o par técnico ao molde, sem participar da matemática | `clube_novo.funcao_sistema.id` | 19 IDs aptos; motor, molde e regra de estilo comparam somente o ID |
| índice da medida no molde | ausente no JSON antigo | localiza a mesma medida no vetor corporal | `clube_novo.corpo_ordem.pos` | 228/228 regras resolvidas; 12 índices únicos por função |
| uso do pé ruim | `clube.carta_jogo.pe_ruim_uso` | valor físico do bit 478, largura 2 | `clube_novo.carta_pe_jogo` | (`card_id`,`campo=pe_ruim_uso`); valor 0–3; catálogo `clube_novo.pe` apto |
| precisão do pé ruim | `clube.carta_jogo.pe_ruim_precisao` | valor físico do bit 578, largura 2 | `clube_novo.carta_pe_jogo` | (`card_id`,`campo=pe_ruim_precisao`); valor 0–3; catálogo `clube_novo.pe` apto |
| pesos do pé ruim | `clube.bonus_parametro` | conversão dos dois valores e teto | `clube_novo.pe.valor_bonus` | (`campo`,`valor`); nove valores aptos; igualdade comprovada com a régua antiga |
| posição principal | `clube.carta_jogo.posicao` + `clube.posicao` | posição que escolhe o slot de estilo | `clube_novo.carta_posicao_principal_jogo` + `posicao_jogo` | (`card_id`,`posicao_id`); exatamente uma relação; catálogo apto |
| playstyle do slot 1 | `slot_ofensivo_id` + `clube.estilo_jogo` | estilo físico gravado no primeiro slot | `clube_novo.carta_playstyle_jogo` + `playstyle` | (`card_id`,`slot_fisico=1`); `playstyle_id=id_jogo`; catálogo apto |
| playstyle do slot 2 | `slot_defensivo_id` + `clube.estilo_defensivo` | estilo físico gravado no segundo slot | `clube_novo.carta_playstyle_jogo` + `playstyle` | (`card_id`,`slot_fisico=2`); `playstyle_id=id_jogo`; catálogo apto |
| regra de estilo | `clube.estilo_regra` + `posicao_slot` | regra ClubEfootball de casa/ativação e slot dominante | `clube_novo.bonificador_regra_playstyle` + `bonificador_posicao_slot` | `playstyle.id_jogo`, `posicao_jogo.id`, `funcao_sistema.id`; 90 regras, incluindo 291 físico |
| estilos de IA | JSON `clube.carta_jogo.estilos_ia` | quantidade de bits de IA ligados na carta | `clube_novo.carta_estilo_ia_jogo` + `estilo_ia` | (`card_id`,`bit_estilo_ia`); catálogo pelo bit físico e `pode_rodar` |
| pares card × função | `clube.build` | universo já calculado pelo Otimizador | `clube_novo.bonificador_par` | projeção privada com FKs (`card_id`,`funcao_id`); está vazia, pois não houve lote autorizado |
| parâmetros não físicos | `clube.bonus_parametro` | tetos e pesos da regra ClubEfootball | `clube_novo.bonificador_parametro` | 14 valores preservados, sem semântica por texto legado |
| saída | `clube.build.b_*` via writer legado | fotografia histórica | `clube_novo.build_bonificador` via `gravar_build_bonificador_v3` | writer canônico; nenhuma execução produtiva autorizada |

As dimensões de nacionalidade, clube, liga e tipo, as habilidades, as posições
secundárias, os técnicos e os ímpetos foram inventariados e deliberadamente não entram
na fórmula vigente. Sua existência no modelo novo não autoriza adicioná-los ao cálculo.

## 4. Contratos seguros e versionados

A aplicação não lê `clube_novo` diretamente. A migração cria somente três portas
allowlisted em `public`, todas `SECURITY DEFINER`, com `search_path` vazio, referências
qualificadas e `EXECUTE` apenas para `service_role`:

- `bonificador_regua_v2()` — receita allowlisted, chaves estáveis e gates;
- `bonificador_carta_v2(card_id)` — somente os campos usados pelo Bonificador, com
  proveniência, cardinalidades, completude vigente, versões, fingerprints e
  `pode_rodar`;
- `public.bonificador_contexto_fila_v3(limit, offset)` — identidade exata da
  linha pendente, card, função, posição e fingerprints calculados pelo banco.

`PUBLIC`, `anon` e `authenticated` não recebem execução. Nenhuma tabela de
`clube_novo` é exposta e nenhuma policy/RLS existente é alterada.

O runtime produtivo não chama mais `public.gravar_bonus` e não escreve em
`clube.build`. Para cada resultado apto ele chama exclusivamente
`public.gravar_build_bonificador_v3`, que relê a completude, confere identidade,
selos, parcelas, total e ligação, tudo na mesma transação. O retorno só é aceito se
trouxer `readback=ok`, a mesma linha, os mesmos selos e um fingerprint SHA-256.
`bonus_fisico_detalhe` leva a contribuição efetiva de cada medida e sua soma decimal
precisa ser exatamente igual a `bonus_fisico_total`. A última medida recebe somente o
residual de arredondamento. `bonus_posicao` é zero porque posição condiciona a regra
atual, mas não soma uma quinta parcela; as contribuições dos slots 1 e 2 somam
exatamente o mesmo bônus de estilo agregado da V8.

## 5. Gates e ausência de fallback

Uma carta só pode ser gravada quando todos estes gates passam:

1. a carta existe em `clube_novo.carta_jogo`;
2. há exatamente 12 medidas corporais usadas pelo Bonificador;
3. pé, posição principal e playstyles têm cardinalidades normalizadas `3/1/2`;
4. corpo, pé, posição, playstyles e IA resolvem em catálogos com `pode_rodar=true`;
5. os dois valores de pé ruim resolvem na régua física nova;
6. a regra do playstyle possui ponte estável;
7. todas as quatro parcelas são numéricas;
8. a carta está apta na completude vigente e os fingerprints coincidem;
9. o par traz o ID da linha, função e posição exigidos pelo writer novo.

Falha de RPC, relação incompleta, catálogo bloqueado ou regra sem ponte deixa a carta
em `NAO-SEI.txt` e exclui todos os seus pares da chamada ao writer novo. O código
não volta a `carta_do_motor`, não usa o JSON antigo e não transforma ausência em zero.

## 6. Divergências conhecidas da fotografia antiga

No universo comum há 42.803 cartas antigas e 43.072 novas; 269 existem somente no
modelo novo. A comparação integral encontrou:

- corpo: 23 valores divergentes, distribuídos em 12 cartas;
- pé ruim: uma precisão divergente (`176844`);
- IA: duas cartas com cardinalidade nova maior (`155498` e `176844`);
- posição principal: três cartas divergentes;
- slot 1: três cartas divergentes;
- slot 2: oito cartas divergentes.

Essas divergências são registradas por `card_id`, campo, origem e valor no checklist e
na auditoria. A fonte nova é a fotografia física/canônica atual; a fotografia antiga é
referência de sombra, não fallback.

As relações normalizadas foram auditadas mesmo quando não participam da fórmula:

| relação | linhas | cartas | cardinalidade por carta presente | uso pelo Bonificador |
|---|---:|---:|---:|---|
| atributos | 1.119.872 | 43.072 | 26 | não usa |
| corpo | 516.864 | 43.072 | 12 | usa |
| habilidades | 179.189 | 33.521 | 1–10 | não usa |
| estilo de IA | 54.435 | 24.854 | 1–5 | usa; ausência significa nenhum bit ligado |
| posições | 516.864 | 43.072 | 12 | não usa a lista; usa a relação principal 1/1 |
| ímpetos | 3.748 | 2.641 | 1–2 | não usa |

As relações adicionais efetivamente consumidas têm cobertura integral: pé
`129.216 = 3 × 43.072`, playstyles `86.144 = 2 × 43.072` e posição principal
`43.072 = 1 × 43.072`. Elas têm zero divergência contra os escalares canônicos,
que permanecem somente como contraprova do gate.

## 7. Ponte canônica aplicada aos moldes corporais

O v7 recebe `funcao_codigo` técnico, como `centroavante_fixo`, porém
`regua_bonus()` e o contrato v1 antes da ponte indexavam `molde_corpo` pelo rótulo
`Centroavante fixo`. O match direto é `0/19` funções usadas e, na referência,
os 17.798 pares devolvem corpo ausente. O v7 seguia somando as outras parcelas;
isso era fallback silencioso e não pode ser preservado nesta migração.

O usuário autorizou corrigir exclusivamente essa referência. O contrato agora usa
`clube_novo.funcao_sistema.id` como identidade canônica e publica o mesmo molde sob o
ID esperado pelo motor. A associação histórica
`codigo_legado → nome_legado` foi usada uma única vez para materializar o snapshot;
não é lida em runtime. A medida resolve o índice físico `clube_novo.corpo_ordem.pos`.

Nenhum peso, corte, direção, ordem, composição ou operação matemática foi alterado.
A auditoria confirmou:

- 19/19 funções, com IDs canônicos únicos e `pode_rodar=true`;
- 228/228 regras e índices resolvidos, 12 por função;
- 17.798/17.798 referências externas resolvidas;
- zero divergência estrutural entre o molde por nome e o molde por código/ID;
- zero divergência matemática nos 17.795 pares com carta no modelo novo;
- três referências sem carta nova continuam sem cálculo e sem fallback.

## 8. Playstyle 291 resolvido pelo dado físico

No modelo novo, raw `140 / 4 = índice 35` resolve fisicamente para
`playstyle.id_jogo=291` (`Goleiro adiantado`). A regra foi materializada por esse ID,
não pelo rótulo histórico. Iker Casillas `88045755827028` lê `291` no slot 1 e `336`
(`Goleiro ofensivo`) no slot 2; a posição GO manda no segundo slot e a mesma fórmula
entrega `1,5`. A carta está apta e não há bloqueio por nomenclatura.

## 9. Trava global de fórmula e limites desta migração

É proibido alterar fórmulas matemáticas, pesos, cortes, ordem de cálculo, composição
dos moldes ou regras de negócio do Bonificador e dos demais motores sem nova
autorização explícita e específica do usuário, precedida de prova própria. Esta
migração altera somente referências/origens de entrada.

As operações matemáticas, pesos, cortes, ordem e arredondamentos das funções do arquivo
permanecem iguais ao snapshot. `bonus_do_corpo` trocou apenas a busca de chave do mapa
para aceitar `funcao_id`, e o chamador passa esse ID a `bonus_do_corpo` e
`bonus_do_estilo`; não há alteração aritmética. Três comportamentos pré-existentes ficam
documentados separadamente:

- `regua_bonus()` não devolvia `casa`/`liga`, embora o código as lesse; o resultado era
  zero silencioso. O contrato canônico atual entrega as mesmas regras reindexadas por
  IDs;
- a referência código técnico → rótulo do molde estava quebrada e foi corrigida pela
  ponte canônica autorizada, sem tocar no conteúdo do molde;
- `molde_corpo.direcao` é numérico (`-1/0/1`), enquanto o código histórico testa o
  texto `"-"`. Esta migração não corrige essa fórmula.

Nenhuma UI, Otimizador, Extrator, ímpeto, dado do jogo ou lote produtivo é alterado.

## 10. Auditoria e recuperação

O checklist oficial, SQL de aplicação, rollback, readback e auditoria permanente ficam
em `4-DOCUMENTOS/BONIFICADOR`. O snapshot anterior do executável fica em
`4-DOCUMENTOS/BONIFICADOR/RECUPERACAO/2026-08-28-ANTES-REGUA-CANONICA-CLUBE-NOVO`.

O consumidor `casa_tela` permanece intacto. A validação visual do aplicativo local é
registrada em `4-DOCUMENTOS/BONIFICADOR/INTERFACE-LOCAL.md`; ela não toca a UI
principal, o Otimizador ou o Extrator.

## 11. Estado operacional e gates

O caminho efetivo lê `bonificador_regua_v2`, `bonificador_carta_v2` e
`bonificador_contexto_fila_v3`. A gravação, quando autorizada, passa somente por
`gravar_build_bonificador_v3`. As relações de `clube_novo` continuam privadas: a
janela não recebe URL de banco, chave, schema nem acesso direto a tabela.

`funcao_id` é a chave que liga o par, o molde e a regra de playstyle. `funcao_codigo`
e rótulos humanos servem só para mostrar a informação; não escolhem regra nem liberam
gate. Carta incompleta, catálogo sem `pode_rodar`, fingerprint divergente ou contrato
indisponível deixam a linha bloqueada. Não existe fallback legado.

Quando não há linha apta, o motor fica em **aguardando** e consulta a fila novamente.
Ele não fabrica fila, checkpoint, cache ou resultado local. Um lote produtivo continua
dependendo dos gates e da autorização operacional; este manual não autoriza dispará-lo.

## 12. Aplicativo local único

Abra somente **Bonificador ClubEfootball.exe** pelo ícone. Ele é uma janela nativa do
Windows: não abre Edge, navegador nem página web. Ao abrir, o EXE cria um componente
interno temporário em porta livre de `127.0.0.1`, confirma o `ping` e mostra a janela.
O componente não é um segundo aplicativo: fica invisível, é encerrado junto com a
janela e sua cópia temporária é apagada ao fechar.

A raiz `2-MOTORES/BONIFICADOR` contém um único `.exe`. O motor-fonte, o servidor-fonte
e os arquivos de compilação permanecem porque são necessários para manutenção; runtime
portátil, cache Python, interface web, lançadores `.bat` paralelos e logs automáticos
não fazem parte do pacote operacional.

### O que a tela mostra

- **Fila do Bonificador:** estado, progresso, linha atual, pendentes, calculadas,
  confirmadas, eventos e pares retornados pela fila V3.
- **Testar uma carta:** consulta somente leitura de corpo, pé ruim, posição principal,
  slots 1 e 2 de playstyle, IA, molde, régua, parcelas e gates.
- **Auditoria e paridade:** contrato, proveniência, cardinalidades e fingerprints.

As consultas rodam em segundo plano. Se contrato, rede ou banco demorarem, a janela
continua responsiva e informa a falha; ela não fica presa em “Não está respondendo”.
O tempo máximo de uma chamada local é de dez segundos.

## 13. Operação segura

O botão **Iniciar Bonificador** inicia o único processo local do motor. O botão
**Parar normalmente** pede que ele conclua a rodada atual e não inicie outra. Mantenha
um único escritor Bonificador para o mesmo banco.

Falha de rede, contrato ou gate nunca vira sucesso silencioso. A linha sem todos os
insumos canônicos permanece fora da gravação, marcada como ausência conhecida, sem
valor inventado. Fórmulas, pesos, ordem de cálculo, moldes e regras de jogo não são
alterados pela aplicação.

Para recuperação, auditoria e prova de paridade, consulte
`4-DOCUMENTOS/BONIFICADOR/INTERFACE-LOCAL.md`, o checklist oficial e
`4-DOCUMENTOS/BONIFICADOR/RECUPERACAO`. A limpeza do pacote único tem recuperação em
`RECUPERACAO/2026-08-31-ANTES-LIMPEZA-PACOTE-UNICO`.
