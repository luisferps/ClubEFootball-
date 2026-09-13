# Registro operacional — correção do bônus de estilo V11

**Aberto e encerrado em 07/09/2026.** Este registro documenta a correção da
parcela de estilo e o readback observado. O estado vivo do lote deve ser lido por
`public.bonificador_correcao_status_v1(uuid)`.

> **Nota de 09/09/2026:** este arquivo preserva a regra e o readback da V11.
> A nova política aprovada, ainda não implantada, está em
> [Regra de estilos aprovada em 09/09](REGRA-ESTILOS-APROVADA-0909.md).
> Ela define o principal pela função e limita a promoção do secundário às duas
> exceções expressas. Os resultados históricos abaixo não validam essa nova política.

## Regra da V11 registrada em 07/09

O Bonificador verifica se cada playstyle ativa na **posição escolhida no jogo**.
A função interna do ClubEfootball e a casa do molde não participam dessa decisão.

- slot dominante ativo: `+1,0`;
- outro slot ativo: `+0,5`;
- teto agregado: `1,5`;
- se o slot dominante for Básico, o outro estilo assume a parcela cheia;
- estilo que não ativa na posição: zero nessa parcela.

Não houve mudança em molde, corpo, pé ruim, IA, pesos, cortes, Otimizador ou
Extrator.

## Identidade selada

- motor: `v11-0709-estilo-posicao-oficial-v1`;
- fórmula:
  `2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879`;
- régua: `bonificador-regua-v3`;
- contexto de fila: `public.bonificador_contexto_fila_v6`;
- writer normal: `public.gravar_build_bonificador_v5(jsonb)`;
- writer do lote corretivo:
  `public.gravar_build_bonificador_correcao_v1(uuid,jsonb)`;
- EXE: `2.0.28.0`;
- componente SHA-256:
  `B8F237AA4825267D759B2E206B2E572D23D91A9FDB78DDABB5D3515AC6B31CB3`;
- EXE SHA-256:
  `B4A74773E8839627E52E4819B36B671D69AE7905BAF5EA4CFD6CAAC24ECBC7FA`.

## Lote integral

- UUID: `0ddaa775-24c1-4293-86ca-77fe698aa044`;
- tipo: `integral`;
- snapshot: 192.635 linhas;
- ordem: grupo prioritário, overall decrescente, carta, função e posição;
- o processamento não depende de o Otimizador já ter terminado;
- a publicação acontece por linha quando os dois resultados compatíveis existem.

O início na Máquina 2 é feito por
`2-MOTORES/BONIFICADOR/OPERACAO-CORRECAO-FISICA/INICIAR-REPROCESSAMENTO.bat`.
O console correto mostra `BONIFICADOR v11 — estilo oficial por posição`.

## Reaproveitamento sem recalcular tudo

Os resultados V10 existentes não foram apagados nem recalculados por inteiro. A
migração criou resultados V11 imutáveis reaproveitando corpo, pé ruim e IA e
substituindo somente `bonus_playstyle_1`, `bonus_playstyle_2`, `b_estilo`, totais e
selos derivados. A fila restante passou a ser calculada diretamente pelo motor V11.

Arquivo de migração:
`4-DOCUMENTOS/BONIFICADOR/SQL/20260907090000_CORRIGIR-BONUS-ESTILO-POR-POSICAO-V11.sql`.

## Provas concluídas

- [x] seis relações incompatíveis com o texto do jogo foram desligadas;
- [x] Editor de Build deixou de exigir igualdade entre playstyle e função;
- [x] 88.951 resultados já preparados foram convertidos inicialmente para V11;
- [x] zero divergência de parcelas de estilo na auditoria integral convertida;
- [x] zero divergência de `b_estilo` e `b_total` na auditoria integral convertida;
- [x] 21.223 publicações cujo componente de estilo mudava foram priorizadas;
- [x] zero publicação permaneceu com valor de estilo diferente do V11;
- [x] zero item prioritário aguardando e zero item prioritário com erro;
- [x] linha `405776` confirmada no banco com motor V11, `b_estilo=1,0` e
  `b_total=2,0958`;
- [x] arquivos oficiais da Máquina 1 conferidos por hash;
- [x] Máquina 2 abriu o EXE V2.0.28 e iniciou o lote em V11.

No readback após o início da Máquina 2, o lote estava `rodando`, com 91.657
preparadas e 100.978 pendentes. Esses números são fotografia operacional e mudam
enquanto o worker continua.

## Itens fora desta correção

As publicações ainda seladas como V10, mas numericamente iguais às V11, não são
erro de pontuação; o finalizador pode renovar esses selos gradualmente. Também
ficaram fora desta correção os itens de finalização referentes a revisões de
orçamento, revisões sem evolução e 335 divergências de selo do Otimizador.
