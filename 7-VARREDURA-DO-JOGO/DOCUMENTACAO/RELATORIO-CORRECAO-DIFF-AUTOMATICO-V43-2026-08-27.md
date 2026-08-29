# Correção do fluxo “Atualização por diff” — versão 4.3

**Data:** 27 de agosto de 2026  
**Estado:** corrigido, instalado e validado sem escrita no banco

## Causa

A tela ainda escondia uma dependência manual: era obrigatório escolher `carta_jogo_completo.csv`. Sem esse arquivo, o botão permanecia desabilitado. Por isso o clique em **Atualização por diff** parecia não produzir nenhuma ação.

Também foi identificado que objetos JSON vindos do PostgreSQL podiam ter uma ordem interna diferente da extração física. A comparação textual dessa ordem criava alterações falsas em `aptidoes`.

## Correção

- a base atual agora é carregada automaticamente de `clube_novo.carta_jogo` em transação somente leitura;
- o seletor de CSV foi removido do fluxo incremental;
- a aba inicia a comparação automaticamente assim que banco e DT870 estiverem prontos;
- a tela sempre mostra **NOVA CARGA IDENTIFICADA**, **SEM MUDANÇAS** ou **COMPARAÇÃO BLOQUEADA**;
- a comparação de campos JSON passou a usar conteúdo canônico, ignorando apenas diferenças irrelevantes de ordem de chaves;
- quando existem diferenças, aparece o botão **OK — preparar envio ao clube_novo**;
- o mecanismo de confirmação final e a proteção do schema `clube` foram mantidos.

## Resultado no executável instalado

- versão do arquivo: `4.3.0.0`;
- horário do binário: `27/08/2026 18:48:00`;
- tamanho: `103.936` bytes;
- SHA-256: `050920a93c963ee0a0ec1fd4cee6f7514a3ca320616c290fd3ae32eed02d478c`;
- resultado visível: 43.072 cartas atuais, 269 novas, 34 atualizadas, zero possíveis inativas e zero duplicadas;
- o botão de preparar envio ficou visível e habilitado;
- após o pré-voo, o botão de aplicação final continuou desativado sem a confirmação exigida.

## Segurança comprovada

Antes e depois do teste, `clube.carta_jogo` e `clube_novo.carta_jogo` permaneceram com 42.803 linhas e fingerprint `ff67b8a2e544570dae42ed71d8428821`. O endpoint de aplicação não foi acionado.

## Passo exato para testar

1. Feche qualquer janela antiga do Extrator.
2. Dê dois cliques em `Extrator eFootball.exe`.
3. Clique em **Atualização por diff**.
4. Aguarde aparecer **NOVA CARGA IDENTIFICADA — 269 novas, 34 atualizadas e 0 possíveis inativas**.
5. Confirme que o botão seguinte é **OK — preparar envio ao clube_novo**.

Não clique em **Aplicar esta carga no clube_novo** durante este teste, salvo se houver uma autorização específica para escrita.
