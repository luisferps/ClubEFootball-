# Entrega do runtime: orçamento físico e prioridade

Entrega vigente: pasta oficial
`2-MOTORES/OTIMIZADOR/OPERACAO-LOCAL-JSON`, revisão
`df13d573ac8444538d8508107875c31c`.

O ZIP `ATUALIZACAO-OTIMIZADOR-ORCAMENTO-FISICO-2026-09-06.zip` foi superado
pela auditoria completa do eFHUB e não contém a fila corretiva final.

## Instalação na máquina dedicada

1. Feche processador e enviador na máquina dedicada.
2. Copie a pasta oficial `OPERACAO-LOCAL-JSON` inteira por AnyDesk.
3. Preserve o `config.txt` e a pasta `RESULTADOS-JSON` que já existem na
   máquina dedicada.
4. Confirme em `FILA-ATIVA.json` a revisão
   `df13d573ac8444538d8508107875c31c`.
5. Inicie pelo atalho existente `PROCESSAR-FILA-PRINCIPAL.bat`.

A cópia inclui `bin`, `PACOTE-FILA-INTEGRAL`, `FILA-ATIVA.json`, scripts e
documentação. O pacote não inicia o motor durante a transferência.

## Fotografia entregue

- `7581b184-dccb-4a4b-9ad9-c767d4f4947c`: 4.888 linhas de 518 cards.
- `c5e38fd5-877c-416e-8063-977e24d229db`: 19.029 linhas de 1.801 cards.
- `b02cf0df-d271-4659-8e42-64a8b88b0134`: 97.660 linhas de 10.446 cards.
- `1833e4d0-1707-4ea2-8ba3-3733b5101310`: 26 linhas de 3 cards.
- Total: **121.603 linhas, 12.755 cards únicos**.
- Revisão local: `df13d573ac8444538d8508107875c31c`.
- O worker não foi iniciado na máquina oficial.

Dez cards continuam em `clube_novo.carta_nivel_pendente_v1`. Eles não estão
na fila nem nos lotes corretivos e não possuem publicação ativa. Nível zero
significa nível não coletado; nunca é convertido em orçamento válido.

As linhas sem orçamento físico comprovado continuam no banco e ficam fora do pacote. Ausência de prova não vira nível 1 nem orçamento zero. A cobertura da sessão não comprova o restante do catálogo.

A prioridade global é: especiais evolutivos; especiais sem evolução; base. Em cada grupo, cartas novas com overall ainda não coletado vêm primeiro; depois vêm os overalls conhecidos em ordem decrescente, com desempates estáveis por card, função, posição, condição e linha. Overall ausente não representa overall baixo: representa cadastro novo ainda incompleto.

## Código e contratos

- `operacao_local_json.py`: combina os lotes de `FILA-ATIVA.json`, valida prova/orçamento e preserva envelopes/recibos no lote original.
- `renovar_pacotes_prioridade_v1.py`: usa apenas manifesto/cartas/linhas_v2, confere o selo antes/depois e preserva versões anteriores em `RENOVACOES`.
- `APLICAR-PRIORIDADE-ORCAMENTO-V1.sql`: views de elegibilidade, reordenação somente de pendentes pausados, preparo/criação futuros, pacotes e reservas antigas protegidas.
- `APLICAR-REVISAO-ORCAMENTO-V1.sql`: clona contextos divergentes, guarda snapshots anteriores e relaciona pai e filha sem apagar builds.
- Os deltas de eventos, selo do manifesto e fórmula vigente da criação estão incorporados ao SQL principal e também disponíveis separadamente.
- Atualizador e testes ficam na árvore oficial. Os atalhos habituais mantêm seus nomes.

A retomada permanece uma ação separada do operador. Esta entrega não iniciou cálculo, envio ou publicação, nem instalou nada na máquina remota.

## Validação

7 testes da prioridade/renovação, 17 testes existentes da operação JSON e 3 testes do atualizador passaram. Os SQLs foram analisados pelo parser PostgreSQL/PLpgSQL. O EXE recompilado respondeu à ajuda de `renovar`.

O ZIP real foi extraído e instalado em uma pasta temporária: 18 hashes conferidos, backup do EXE anterior confirmado e configuração/resultado de controle preservados. A integridade do ZIP também foi conferida.
