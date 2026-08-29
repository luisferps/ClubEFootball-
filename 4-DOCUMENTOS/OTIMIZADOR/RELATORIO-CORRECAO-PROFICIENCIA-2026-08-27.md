# Relatório histórico — tentativa de alteração da proficiência

**Data da tentativa:** 27/08/2026  
**Estado desde 28/08/2026:** **REPROVADA E REVOGADA**  
**Escopo:** código e documentação; nenhuma execução de lote e nenhuma escrita no banco.

## O que foi tentado

Foi replicada localmente a sequência `base+barras → ímpetos → proficiência sem teto →
boost`. A justificativa usava Alessandro Nesta em 102 e Marcel Desailly em 100. Esses
dois casos não distinguiam a tentativa da regra anterior: ambas as fórmulas produziam
os mesmos inteiros visíveis.

Este relatório registrava a tentativa como correção antes de existir autorização e um
caso discriminante. Essa conclusão estava errada. O conteúdo permanece apenas como
histórico para impedir que a hipótese seja reintroduzida como se tivesse sido provada.

## Experimento que decidiu

- Lionel Messi `89138556575063`;
- 19 níveis em Chute, Finalização 99 antes do campo;
- Fabio Capello, Contra-ataque com bolas longas 89, boost `+1` em Finalização;
- ímpeto fixo Precisão `+4` em Finalização;
- resultado real exibido no campo: **104**.

A regra anterior reproduz 104: proficiência limitada a 99, boost para 100 e Precisão
para 104. A tentativa posterior previa 107 com o truncamento codificado ou 107,708
antes da apresentação. Mesmo admitindo valor interno fracionário e apresentação
inteira, 107/108 não corresponde a 104.

## Decisão vigente

Por autorização expressa do usuário em 28/08/2026, foi restaurada a sequência:

```text
base+barras, teto 99 → proficiência, teto 99 → boost do técnico → ímpetos
```

A tentativa posterior está revogada. Nenhum trecho deste relatório autoriza sua volta.
Uma mudança futura exige nova autorização e evidência discriminante própria.

## Preservações

- dados e relações canônicas de Técnicos não foram revertidos;
- nenhuma rodada do Otimizador ou recálculo de builds foi iniciado;
- nenhum banco, schema, Extrator ou consumidor foi ativado ou alterado.
