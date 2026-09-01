# Checklist de estabilidade do produto — Otimizador V44 / contrato único V19

Data: 01/09/2026  
Escopo: uma fonte privada por linha para o painel e o worker, correção do
contador de estados e recuperação estrita da falha pré-reserva já comprovada.

## Travas preservadas

- [x] Fórmula aprovada inalterada: barras (teto 99) -> proficiência (piso/teto
  40/99) -> boost técnico -> ímpetos; regressão Messi/Capello = 104.
- [x] Pesos, moldes, regra de negócio, Ímpetos condicionais, Bonificador e
  publicação não foram alterados.
- [x] `clube_novo` continua a única autoridade operacional; não há leitura,
  fallback ou escrita em `clube.*`.
- [x] Browser permanece loopback sem credencial; somente o serviço local chama
  RPCs allowlisted.

## Contrato único

- [x] View privada `clube_novo.otimizador_entrada_linha_v1` criada com
  `security_invoker=true`; `public`, `anon` e `authenticated` não recebem
  acesso.
- [x] `otimizador_producao_reservar_entrada_v7` lê essa view, valida fórmula,
  versão, gates, carta e Ímpetos desligados antes de reservar.
- [x] `otimizador_producao_fila_operacional_v4` lê a mesma view para a tela;
  ela entrega IDs para vínculo e rótulos canônicos apenas para apresentação.
- [x] Worker integral V3 usa V7 para receber a régua e a carta da própria linha;
  não consulta contexto/carta em fonte paralela.
- [x] Resultado permanece gravado pela conclusão V6 na estrutura existente de
  builds e retorna à aba Resultados por essa mesma view.

## Confiabilidade da fila

- [x] Trigger/cache de status V19 não tenta inserir delta negativo sujeito a
  `CHECK` antes do `ON CONFLICT`; aplica delta sob trava ou recalcula o lote.
- [x] Correção V19 do fingerprint final do preparador junta
  `otimizador_lote_producao_linha_v3` a `build_linha_card` para obter função e
  posição física; não referencia colunas inexistentes na linhagem.
- [x] Exceção do worker integral antes da reserva não chama `falhar_lote_v3`.
  Depois da reserva, a linha fica sob controle do banco para recuperação
  explícita, sem marcar todo o lote como falho.
- [x] `otimizador_producao_recuperar_falha_pre_reserva_v2` aceita somente a
  falha histórica exata, lote integral, fórmula aprovada, publicação desligada,
  pendências existentes e zero linha ativa.
- [x] A Data API é o caminho padrão do aplicativo; ponte privada V6 só é
  contingência de erro transitório e não mascara recusa determinística.

## Provas executadas

- [x] Reserva V7 em transação revertida: linha 3399, card `52781926899717`,
  função 12, posição 6, contrato `otimizador_entrada_linha_v1`, Ímpetos
  condicionais desligados.
- [x] Durante a prova, cache e tabela física coincidiram em 184.456 pendentes,
  1 processando e 245 concluídas.
- [x] Readback após rollback: lote intacto em `falhou`, 184.457 pendentes,
  zero processando, 245 concluídas e sem publicação.
- [x] Recuperação V19 em transação revertida confirmou `falhou -> rodando`,
  zero linha ativa, contagens preservadas e `pode_publicar=false`.
- [x] Executável portátil recompilado: launcher 1.7.4.0, interface
  `20260901-v44`, runtime completo com `_internal`.
- [x] Loopback real do pacote V44: saúde, status de recuperação e primeira
  página da fila pela view canônica; worker/preparador permaneceram desligados.
- [x] Testes offline: fila V3 (8), esteira V6/V19 (9), preparação V5 (7),
  interface (28), além de `py_compile` para worker e servidor.

## Operação e rollback

- [x] Abrir somente `2-MOTORES/OTIMIZADOR/Otimizador ClubEfootball.exe` com a
  pasta `runtime/_internal/` ao lado. Não executar `runtime/OtimizadorServico.exe`
  manualmente.
- [x] O primeiro clique abre o painel; o cálculo só começa após o botão
  **Iniciar** confirmar o contrato no banco.
- [x] Snapshot: `RECUPERACAO/20260901-v46-contrato-unico-antes/`.
- [x] Migração aplicada:
  `FILA-PRODUCAO-V3/MIGRACAO-CONTRATO-UNICO-V19.sql`.
- [x] Rollback:
  `FILA-PRODUCAO-V3/ROLLBACK-CONTRATO-UNICO-V19.sql`. Ele não apaga builds,
  linhas ou eventos e requer o aplicativo V44 parado.
