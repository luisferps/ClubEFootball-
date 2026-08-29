# Manual de Interligação de Sistemas

Estado em 28/08/2026: destino enxuto da Build criado e validado no banco. Extrator, Otimizador, Bonificador, lotes e UI ainda não estão interligados.

## Em linguagem de jogo

Uma Build publicada é uma linha da carta em um contexto específico:

```text
carta + função + posição = uma linha campeã ativa
```

Exemplo: Lionel Messi como centroavante móvel em uma posição determinada é uma linha. Messi em outra função ou posição é outra linha possível.

A linha só fica pronta ou publicada quando contém, ao mesmo tempo:

- o resultado vencedor do Otimizador;
- o resultado do Bonificador;
- a mesma versão e o mesmo fingerprint da carta nos dois resultados.

Não existe Build final somente do Otimizador nem somente do Bonificador. A tela futura lerá exclusivamente a linha completa e publicada.

## Fluxo futuro

```text
Arquivos do jogo
      |
      v
Extrator -> carta versionada no banco
                     |
             +-------+-------+
             |               |
             v               v
     build_otimizador   build_bonificador
             |               |
             +-------+-------+
                     |
       gate de versão + fingerprint
                     |
                     v
            build_linha_card
           pronta -> publicada
                     |
                     v
                 tela online
```

## As três tabelas

### `clube_novo.build_otimizador`

Guarda somente o resultado devolvido pelo Otimizador:

- `id`;
- `tecnico_id` canônico;
- `barras`, com a distribuição vencedora;
- `impeto_adicional_codigo`, opcional;
- `habilidades_adicionais`, com no máximo cinco IDs;
- `pontuacao`;
- `motor_versao`;
- versão e fingerprints do contrato, carta/entrada, fórmula e resultado;
- datas de criação e conclusão.

Não guarda parcelas do Bonificador e não publica tela sozinho.

### `clube_novo.build_bonificador`

Guarda somente o resultado devolvido pelo Bonificador:

- `id`;
- `bonus_pe`;
- `bonus_fisico_total`;
- `bonus_posicao`;
- `bonus_playstyle_1`;
- `bonus_playstyle_2`;
- `bonus_ia`;
- `bonus_total`;
- `bonus_outros`, apenas para outra parcela real já produzida pela fórmula;
- `motor_versao`;
- versão e fingerprints do contrato, carta/entrada, fórmula e resultado;
- datas de criação e conclusão.

`bonus_fisico_detalhe` é um snapshot estruturado dentro da própria linha. Cada chave identifica uma medida corporal real — por exemplo, comprimento de perna ou largura de ombro — e cada valor registra a contribuição numérica daquela medida. Esse campo apenas explica o total já calculado; não muda peso, ordem, molde ou fórmula.

### `clube_novo.build_linha_card`

É a única unidade pronta para publicação e leitura da tela. Contém:

- `card_id`;
- `funcao_id`;
- `posicao_id`;
- `build_otimizador_id`;
- `build_bonificador_id`;
- versões do motor e do contrato dos dois resultados ligados;
- versão e fingerprint da carta;
- `atributos_snapshot`, com a fotografia estruturada das colunas exibidas;
- fingerprints do snapshot e dos dois resultados que o produziram;
- estado, pendências e selos de publicação;
- datas de criação, montagem, atualização e publicação.

Um índice único impede duas linhas campeãs ativas para a mesma combinação `(card_id, funcao_id, posicao_id)`. Uma linha marcada como `invalida` deixa de ser a campeã ativa e permite a substituição versionada.

### Formato do snapshot de atributos

O objeto é indexado pelo código canônico de `atributo_jogo`. Cada atributo conserva a sequência que a tela realmente mostra, sem recalcular depois:

- classe/peso exibido para a função;
- Base, que é o valor inicial extraído;
- `+barras`;
- `+ímpeto`;
- `+técnico`;
- `Na tela`, valor depois dessas etapas;
- `+hab. nativas`;
- `+hab. adicionadas`;
- Total final;
- Ideal;
- `vs alvo`;
- parcela de pontuação, quando a tela a exibir.

No armazenamento, `valor_inicial`, `etapas[]` e `valor_final` são obrigatórios. Cada item de `etapas[]` identifica a etapa real, o valor acumulado e, quando necessário para explicar a coluna, a parcela aplicada. Campos de apresentação como classe, ideal, diferença para o alvo e pontuação parcial acompanham o mesmo item. Etapas ausentes na fórmula real não são inventadas: quando a tela efetivamente apresenta zero, o snapshot registra o zero produzido.

O snapshot é imutável para aquela publicação e precisa carregar `atributos_snapshot_fingerprint`, `snapshot_otimizador_fingerprint` e `snapshot_bonificador_fingerprint`. O gate confere os dois últimos contra os resultados ligados à linha.

## Auditoria e imutabilidade

Cada resultado de motor é append-only: depois de criado, não pode ser alterado. Uma correção produz um novo ID de execução, com seus próprios selos. O banco preenche `criado_em`; a execução informa a versão identificável do motor e os fingerprints canônicos efetivamente usados.

A linha pode receber os dois resultados enquanto está `pendente`. Ao virar `pronta` ou `publicada`, o banco fixa `montada_em` e protege carta, função, posição, IDs dos resultados, versões, fingerprints e snapshot contra alteração. `atualizado_em` é mantido pelo banco. Uma versão superada deve ser marcada `invalida`, nunca reescrita silenciosamente.

## Gate fail-closed

Uma linha só pode virar `pronta` ou `publicada` quando:

1. os dois IDs de resultado estão presentes;
2. ambos os resultados existem;
3. a versão da carta é igual na linha, no Otimizador e no Bonificador;
4. o fingerprint da carta é igual nos três;
5. a lista de pendências está vazia;
6. a publicação possui fingerprint e data.
7. o snapshot de atributos existe, possui códigos canônicos e está selado pelos fingerprints dos dois resultados.
8. as versões de motor e contrato registradas na linha coincidem com cada resultado ligado.

Se qualquer item falhar, o banco recusa a operação. Resultado parcial nunca vira linha publicável.

## Segurança e limites atuais

- As três tabelas têm RLS habilitado.
- `anon` e `authenticated` não receberam acesso.
- Credenciais não são expostas ao navegador.
- Nenhuma linha da `clube.build` legada foi copiada.
- O legado não é fallback, gate ou entrada operacional.
- Fórmulas, pesos, moldes e ordens matemáticas permanecem intactos.
- Motores, UI principal, lotes e consumidor de Ímpetos continuam desligados.

## Desenhos revogados

Estão revogados e não definem mais a arquitetura:

- a relação muitos-para-muitos `build_carta`;
- a regra de uma única Build por `card_id` sem função e posição;
- o conjunto amplo de tabelas de componentes, snapshots e publicação da V1/V2.

Os arquivos históricos permanecem apenas para recuperação e auditoria. No banco operacional existem somente `build_otimizador`, `build_bonificador` e `build_linha_card` com prefixo Build desta frente.

## Evidência de validação

O readback confirmou somente três tabelas, todas vazias após os testes. Ensaios transitórios provaram:

- publicação sem os dois resultados: recusada;
- publicação com fingerprints divergentes: recusada;
- publicação sem snapshot de atributos: recusada;
- publicação com selo de snapshot incompatível: recusada;
- ligação com versão de motor/contrato divergente: recusada;
- tentativa de alterar um resultado já criado: recusada;
- linha completa e da mesma versão: aceita;
- segunda linha ativa para a mesma carta + função + posição: recusada;
- limpeza final: zero linhas nas três tabelas.

## Migrations e recuperação

- `INTEGRACAO-DE-SISTEMAS/MIGRACAO-BUILD-LINHA-MOTORES-V3.sql`;
- `INTEGRACAO-DE-SISTEMAS/ROLLBACK-BUILD-LINHA-MOTORES-V3.sql`;
- `INTEGRACAO-DE-SISTEMAS/MIGRACAO-BUILD-BONIFICADOR-DETALHE-FISICO-V3.sql`;
- `INTEGRACAO-DE-SISTEMAS/ROLLBACK-BUILD-BONIFICADOR-DETALHE-FISICO-V3.sql`;
- `INTEGRACAO-DE-SISTEMAS/MIGRACAO-BUILD-LINHA-SNAPSHOT-ATRIBUTOS-V3.sql`;
- `INTEGRACAO-DE-SISTEMAS/ROLLBACK-BUILD-LINHA-SNAPSHOT-ATRIBUTOS-V3.sql`;
- `INTEGRACAO-DE-SISTEMAS/MIGRACAO-BUILD-METADADOS-AUDITORIA-V4.sql`;
- `INTEGRACAO-DE-SISTEMAS/ROLLBACK-BUILD-METADADOS-AUDITORIA-V4.sql`;
- `INTEGRACAO-DE-SISTEMAS/RECUPERACAO/2026-08-28-ANTES-BUILD-LINHA-V3/SNAPSHOT-ANTES.md`.

## Antes de interligar os aplicativos

Ainda será necessário validar isoladamente os executáveis, definir as funções internas de gravação idempotente, propagar versão/fingerprint em todas as fronteiras e executar uma sombra ponta a ponta sem escrita produtiva. Somente depois disso os três sistemas poderão ser ligados.

## Fila isolada do Otimizador — contrato aplicado

A primeira escrita controlada usa apenas `build_otimizador` e `build_linha_card`.
Ela não toca no legado, nas cartas, no Bonificador nem na publicação. A amostra
reproduzível de 100 cartas gerou 896 contextos de carta + função + posição.

O lote persiste `parado`, `rodando`, `pausando`, `pausado`, `concluido` e
`falhou`. Parar deixa a linha atômica corrente terminar e impede o início da
próxima. Retomar consome somente pendências do mesmo `lote_id`.

A entrada de uma linha em `processando` também é condicionada, na mesma operação
atômica, a `lote_estado='rodando'`. Assim, se a pausa ganhar a corrida, a nova
linha é recusada; se a linha ganhar, a pausa espera essa linha terminar e não
libera a seguinte.

**Pausar** e **Parar** são ações diferentes. Pausar mantém as linhas pendentes e
permite Retomar. Parar exige confirmação local, passa por `encerrando`, preserva
o resultado já concluído e transforma o restante em `interrompido`; o lote vira
`encerrado` e não pode ser retomado. Nenhuma dessas ações publica ou chama o
Bonificador.

O status devolve `acoes` explícitas; a interface nunca deduz autorização. Cada
resultado precisa repetir os selos da carta, lote, contrato, fórmula e motor. Sem
resultado do Bonificador, a linha permanece teste/não publicada.
