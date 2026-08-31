# Pré-voo e readback — fila produtiva V3

Estado deste diretório: **preparado localmente, não aplicado**. Este documento
não autoriza a execução da migração nem a criação de um lote.

## Antes da aplicação autorizada

1. Confirmar que a credencial local do servidor loopback consegue executar
   `otimizador_regua_v2`. A checagem desta preparação recebeu HTTP 401 da
   credencial atualmente configurada; nenhuma chave foi exibida, alterada ou
   substituída.
2. Preservar o snapshot
   `../RECUPERACAO/20260831-antes-fila-producao-v23/`.
3. Confirmar que não existe um lote V3 anterior. A criação e o rollback falham
   fechados quando há histórico V3, para não misturar ou apagar execução real.
4. Confirmar novamente o selo de fórmula:
   `7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad`.

## Depois da aplicação autorizada

O readback deve comprovar, antes de qualquer clique de início:

- quatro tabelas V3 existentes em `clube_novo`, com RLS;
- todas as RPCs `otimizador_producao_*_v3` existentes, com `SECURITY DEFINER`
  e `search_path` vazio;
- `anon`, `authenticated` e `PUBLIC` sem execução; somente `service_role`;
- `otimizador_producao_status_v3()` retornando `sem_lote`,
  `pode_publicar=false` e ação `criar=true`;
- a interface V23 em loopback recebendo esse estado, sem credencial no browser;
- nenhum registro novo em `build_linha_card`, `build_otimizador` ou
  `build_bonificador` antes de **Criar e iniciar**.

## Primeiro lote

O botão **Criar e iniciar** deve formar uma única fila completa das cartas aptas,
em ordem de overall decrescente. Toda linha usa IDs canônicos, snapshots e selos;
cartas com Ímpeto condicional continuam fora. Um piloto só pode ser iniciado após
o readback acima, e deve validar reserva exclusiva, pausa após a linha atômica,
resultado persistido e estado `bonificador=pendente`. O Bonificador continua um
passo manual separado; não há publicação nesta cadeia.

## Recuperação

Antes de existir lote V3, pode-se usar
`ROLLBACK-FILA-PRODUCAO-V3.sql`. Depois que um lote existir, o rollback é
propositalmente recusado: retenção/arquivamento deve ser uma decisão explícita.
