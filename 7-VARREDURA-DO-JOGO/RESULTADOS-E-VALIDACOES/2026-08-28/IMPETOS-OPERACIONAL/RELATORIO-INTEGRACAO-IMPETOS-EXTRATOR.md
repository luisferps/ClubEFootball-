# Integração operacional de Ímpetos no Extrator

## Snapshot e preservação

Snapshot integral anterior: `RECUPERACAO/2026-08-28-ANTES-IMPETOS-OPERACIONAL`, 897 arquivos, com manifesto SHA-256.

Permaneceram byte a byte idênticos:

- `app/extrator-ui.js`;
- `executor/card_relations.py`;
- `executor/card_dimensions.py`;
- `executor/texto_do_jogo.py`;
- `Extrator-ClubEfootball.html`.

O teste cumulativo do núcleo confirmou ainda 1.478 técnicos e 11.679 textos. Nenhuma UI, motor, schema legado ou banco foi escrito.

## O que foi acrescentado

- `app/extrator-core.js`: contrato `clubef-impetos-physical-v1`; 26 efeitos, tipo, alvos, classes 299/302, corte207, nível212, faixas e expansão de ligas por `CompetitionUnit.bin`.
- `executor/impetos.py`: comparação simétrica read-only com `clube_novo`.
- `executor/executor_local.py`: endpoint `POST /api/impetos/validate`.
- Testes permanentes em `RESULTADOS-E-VALIDACOES/TESTES`.
- Checklist definitivo em `4-DOCUMENTOS/CONTRATO-VALIDACAO-FINAL-EXTRATOR.md` e manual operacional atualizado.

## Prova física

- 440 códigos na união; 408 atuais, 407 efeitos reais e uma vaga raw4.
- 2.072 relações físicas ímpeto→atributo.
- Messi507: Argentina, faixas 1–7/+1, 8–10/+2, 11–23/+3.
- Neymar170: alvo149, membros físicos `[588,149]`, faixas 1–13/+1, 14–19/+2, 20–23/+3.

## Readback contra clube_novo

Passaram integralmente:

- condições: 407/407;
- faixas: 696/696;
- membros de liga: 35/35;
- slots: 3.748, sendo 2.381 preenchidos e 1.367 vagas;
- consumidor: zero condições aptas.

Falhou de forma fechada:

- fonte: 2.072 efeitos;
- banco: 1.556 efeitos;
- faltam no banco: 516;
- extras no banco: zero;
- deltas divergentes nas relações comuns: zero.

Duas reexecuções produziram o mesmo SHA-256 `2594B998F5D7266FFF21B0A92FB25E6320CC5A130044EB612AC7BE7A7B2AAF97`. Ambas foram `transaction_read_only=true`, `database_write=false`, `preserved_schema=clube` e retornaram corretamente `reabrir_frente`.

## Rollback

O script `ROLLBACK-IMPETOS-OPERACIONAL.ps1` restaura os três arquivos cumulativos alterados a partir do snapshot e remove somente os novos arquivos da frente. Não existe rollback de banco porque nenhuma escrita foi realizada.

## Correção e readback definitivo

A causa das 516 ausências foi comprovada: a carga anterior havia limitado as receitas aos códigos usados pelos slots atuais. Ficaram fora 52 receitas inteiras sem uso atual — 38 com quatro efeitos e 14 com 26 efeitos (`38×4 + 14×26 = 516`).

Somente `clube_novo.impeto_atributo_jogo` foi completada. O ensaio integral foi revertido; o commit posterior inseriu 516 linhas, sem órfãos, colisões de PK/ordem ou FK e sem modificar as 1.556 linhas existentes.

Readback final: fonte 2.072, banco 2.072, ausentes 0, extras 0 e deltas divergentes 0. Duas reexecuções do validador produziram o mesmo SHA-256 `A309374CF4C94C8FD0B87D8ED31C9EFAFE52A0E3D9891B7A119934B2BFF21125`, ambas `passed=true` e `result=aprovado`.

## Resultado

O Extrator relê e testa integralmente Ímpetos e a base canônica corresponde exatamente à fonte física. A frente pode encerrar. Consumidor e motor continuam desligados e sua liberação não foi autorizada por esta validação.
