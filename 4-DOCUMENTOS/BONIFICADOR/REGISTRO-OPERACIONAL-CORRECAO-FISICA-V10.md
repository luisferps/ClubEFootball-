## Altura independente — etapa estrutural 09/09/2026

Leia [ALTURA-0909/REGRA-APROVADA.md](ALTURA-0909/REGRA-APROVADA.md). Altura separada sem redistribuir pontos das demais medidas. Regra aprovada em sete funções, direção positiva; preparada no banco, ainda sem alterar notas. Não confundir separação neutra com recálculo aplicado. O registro V10 abaixo é a base histórica preservada.

# Registro operacional — correção física V10

**Aberto em 04/09/2026.** Este arquivo é append-only durante a operação. Não
substitui o status vivo das RPCs.

> **REGISTRO HISTÓRICO.** A fórmula física e o caso-ouro desta V10 continuam
> válidos, mas a identidade operacional vigente é a V11. A correção posterior do
> bônus de estilo está em
> `REGISTRO-OPERACIONAL-CORRECAO-ESTILO-V11.md`. Não use o EXE, a fórmula nem os
> gates abaixo para validar a instalação atual.

## Identidade selada

- motor: `v10-0409-fisico-regra-aprovada-v1`;
- fórmula:
  `756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b`;
- régua: `bonificador-regua-v3`;
- EXE: `2.0.27.0`;
- componente incorporado/local SHA-256:
  `49E095E52AEB5900418A295316E15D00B62024F0F4777A2C244D30607C306F4A`;
- EXE SHA-256:
  `7073834620F8467142800CBA97138607F31DDEEC097CA330DFB6F8A147B89C00`.

## Provas concluídas na Máquina 1

- [x] quatro bordas de corte e faixas `-2..+2`;
- [x] direção `+1`, `-1` e neutralidade real de `0`;
- [x] peso `5` da altura;
- [x] máximo variável por função e clamp `±1,5`;
- [x] soma decimal exata das 12 parcelas;
- [x] Messi `89136409091415` × função 14 = `+0,9750`, soma `13`, máximo
  `20`, percentual `0,65`, altura `+0,75`;
- [x] compilação do componente com PyInstaller 6.22.2;
- [x] EXE V2.0.27 recompilado e recurso incorporado com hash idêntico;
- [x] smoke do componente: `/api/ping` devolveu `20260904-fisico-v10`;
- [x] `VALIDAR-MAQUINA-2.bat` executado localmente sem rede produtiva nem writer;
- [x] migração aceita pelo PostgreSQL em transação encerrada por `ROLLBACK`;
- [x] todos os testes Python do Bonificador passaram em conjunto.

## Gates de produção

- [ ] pacote portátil copiado e validado na Máquina 2;
- [x] lote V9 `a69a67b0-7443-45b3-a859-334ab90919af` encerrado pelo contrato
  oficial em 05/09/2026 01:11 UTC: 57.292 concluídas, zero
  pendentes/processando/falhas/interrompidas;
- [x] janela de aplicação conferida: zero sessão ativa e nenhuma migração nova
  depois de `20260904233446`;
- [x] migração `bonificador_correcao_fisica_v10_staging` aplicada e relida;
- [x] piloto `e7cf4b8c-bcde-48b2-8932-fe191a6985e3` preparado com 5 linhas e
  snapshot `c5b2a7a8a6595cc49e7bc09aeb97c1dff4f8f5c7c5102f2010c428865013575a`;
- [ ] piloto processado na Máquina 2 e caso-ouro validado;
- [ ] snapshot integral preparado;
- [ ] integral processado em staging com zero falha;
- [ ] prova de versão única e contagens fechada;
- [ ] corte atômico executado;
- [ ] notas finais e materialized view pública relidas;
- [ ] Messi, Dani Olmo e amostra representativa confirmados na publicação.

Nenhum item não marcado acima pode ser inferido como concluído. Em particular,
compilar o pacote não autoriza aplicar a migração, iniciar o worker ou fazer o corte.

## Readback imediatamente após a migração

Em 05/09/2026 01:11 UTC: 225.274 linhas, 57.950 resultados, 57.582 vínculos,
55.434 publicadas, zero resultado V10 e zero lote corretivo antes da preparação do
piloto. A régua V3 respondeu `pode_rodar=true`; o writer V4 ficou sem `EXECUTE` para
`service_role` e `bonificador_runtime`, e o writer V5 ficou liberado. Preparar o
piloto não alterou nenhum dos cinco vínculos V9 selecionados.
