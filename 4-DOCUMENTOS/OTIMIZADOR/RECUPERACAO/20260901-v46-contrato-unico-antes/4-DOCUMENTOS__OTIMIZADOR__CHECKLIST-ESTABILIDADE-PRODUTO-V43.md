# Checklist de estabilidade do produto — Otimizador V43 / V18

Data: 01/09/2026  
Escopo: impedir que queda transitória de contrato, antes de uma reserva, marque
indevidamente a fila integral como falha.

## Travas preservadas

- [x] Fórmula aprovada inalterada: barras (teto 99) -> proficiência (piso/teto
  40/99) -> boost técnico -> ímpetos.
- [x] Pesos, moldes, ordem de cálculo, Ímpetos condicionais, publicação e
  Bonificador não foram alterados.
- [x] Fonte operacional continua `clube_novo`; não há chamada a `clube.*`.
- [x] Browser continua loopback sem credencial; banco só é chamado pelo servidor
  local por allowlist de RPC.

## Gatilho limitado de recuperação

- [x] `otimizador_producao_status_v7` só libera `retomar=true` quando o lote é
  integral, a fórmula aprovada confere, `pode_publicar=false`, há pendências,
  não há linha processando e a falha é exatamente a queda pré-reserva
  comprovada.
- [x] `otimizador_producao_recuperar_falha_transporte_v1` repete todos esses
  gates dentro da transação e bloqueia o cabeçalho do lote antes de alterá-lo.
- [x] Recuperação muda somente `falhou -> rodando` e grava evidência em
  `lote_retomado`; não altera `build_linha_card`, resultados, fórmulas ou
  publicação.
- [x] Timeout ambíguo de reserva não é repetido; rejeição confirmada pode ser
  repetida pelo worker com espera progressiva.

## Provas obrigatórias antes de distribuir

- [x] leitura V7 no contrato real devolveu `retomar=true` apenas para o incidente
  V18 e preserva contagens/zero linha ativa;
- [x] chamada V18 recuperou o lote e readback confirmou `rodando`, nenhuma linha
  nova, publicação desligada e contagens preservadas;
- [x] `python -m py_compile` passa para servidor e worker;
- [x] testes offline de esteira, fila integral e interface passam;
- [x] regressão da fórmula aprovada confirma Messi/Capello = 104;
- [x] serviço portátil e ícone compilados abrem em porta isolada sem iniciar
  worker;
- [x] endpoint loopback devolve o estado e não expõe credencial;
- [x] pacote oficial foi recompilado e verificado antes de qualquer nova
  distribuição da pasta completa do Otimizador.

## Complemento de produto — preparador e abertura portátil

- [x] Erro transitório de conexão (timeout/queda de rede) continua com tentativa
  automática e não marca o lote como falho antes de reservar uma linha.
- [x] Erro determinístico de contrato, configuração ou código não é mais tratado
  como queda de rede: o preparador local para, exibe o motivo real e não altera
  lote, linha, resultado ou publicação.
- [x] O serviço portátil encontra a raiz do aplicativo por locais locais
  confiáveis (lançador, executável, diretório atual ou bootstrap), sem depender
  de uma variável de ambiente herdada por outro computador.
- [x] O ícone oficial e o `runtime\\OtimizadorServico.exe` foram abertos em
  portas isoladas; ambos devolveram saúde e status do lote real sem iniciar
  worker, preparador, reserva, cálculo ou publicação.
- [x] Não restou processo `OtimizadorServico` nem listener de teste após a
  validação.

## Recuperação/rollback

- Snapshot: `RECUPERACAO/20260901-v43-transporte-antes/`.
- Snapshot do complemento de preparador: `RECUPERACAO/20260901-v44-preparo-antes/`.
- Migração: `FILA-PRODUCAO-V3/MIGRACAO-RESILIENCIA-TRANSPORTE-V18.sql`.
- Rollback: `FILA-PRODUCAO-V3/ROLLBACK-RESILIENCIA-TRANSPORTE-V18.sql`.
  Ele remove apenas as portas V18; não apaga evidência operacional e não deve
  ser aplicado enquanto o executável V43 estiver em uso.
