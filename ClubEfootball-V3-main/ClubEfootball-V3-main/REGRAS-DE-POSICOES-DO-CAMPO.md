# Regras de posições do campo

**Criado/atualizado em:** 22/08/2026 às 19:38:59 (America/Sao_Paulo, UTC−03:00)  
**Escopo:** regras de ocupação das vagas do campo, usando as siglas exibidas na interface.

## 1. Estrutura da matriz

A matriz do campo é formada, nesta ordem, por:

1. uma faixa de goleiro;
2. uma faixa de defesa;
3. duas faixas de meio-campo;
4. uma faixa de ataque.

Em cada faixa:

- a vaga extrema esquerda é considerada **esquerda**;
- a vaga extrema direita é considerada **direita**;
- todas as demais vagas são consideradas **centrais**, independentemente de existirem duas ou três vagas centrais.

## 2. Goleiro

| Tipo de vaga | Posições aceitas |
| --- | --- |
| Goleiro | **GO** |

Nenhuma outra sigla pode ocupar a faixa de goleiro.

## 3. Defesa

| Tipo de vaga | Posições aceitas |
| --- | --- |
| Extrema esquerda | **LE** ou **ZC** |
| Central | somente **ZC** |
| Extrema direita | **LD** ou **ZC** |

Regras adicionais da linha defensiva:

- podem existir, no máximo, **três ZC** em toda a linha defensiva;
- ao atingir o limite de três ZC, nenhuma vaga adicional pode receber ZC;
- portanto, toda vaga extrema ainda desocupada deve usar **LE** à esquerda ou **LD** à direita.

## 4. Meio-campo

As duas faixas de meio-campo são intercambiáveis: as mesmas regras valem em qualquer uma delas.

| Tipo de vaga | Posições aceitas |
| --- | --- |
| Extrema esquerda | **MLE**, **MLG**, **MAT** ou **VOL** |
| Central | **VOL**, **MLG** ou **MAT** |
| Extrema direita | **MLD**, **MLG**, **MAT** ou **VOL** |

Regras adicionais das duas faixas de meio-campo:

- **MLE** pode existir somente uma vez em todo o meio-campo e apenas em uma vaga extrema esquerda;
- **MLD** pode existir somente uma vez em todo o meio-campo e apenas em uma vaga extrema direita.

## 5. Ataque

| Tipo de vaga | Posições aceitas |
| --- | --- |
| Extrema esquerda | **SA**, **PTE** ou **CA** |
| Central | **CA** ou **SA** |
| Extrema direita | **SA**, **PTD** ou **CA** |

Regras adicionais da linha de ataque:

- **PTE** é único e só pode ocupar a vaga extrema esquerda;
- **PTD** é único e só pode ocupar a vaga extrema direita;
- **SA** pode ocupar qualquer vaga do ataque;
- **CA** pode ocupar qualquer vaga do ataque, limitado a **dois CA no total**.

## 6. Aplicação às formações

Estas regras valem para qualquer formação disponível ou manipulada no sistema, sem exceção, incluindo expressamente:

- **4-2-4**;
- **3-3-4**.

A quantidade de vagas de uma faixa não altera a classificação espacial: apenas a primeira vaga é esquerda, apenas a última é direita e todas as vagas intermediárias são centrais.
