# Checklist oficial — reversão da fórmula do Otimizador

**Data:** 28/08/2026  
**Decisão:** fórmula posterior reprovada e revogada; fórmula anterior restaurada.  
**Escopo executado:** somente trechos de fórmula, regressões e documentação do
Otimizador. Nenhum banco, esquema, Extrator, lote, dado de jogo ou ativação de
consumidor foi alterado.

## Regra vigente

```text
base + barras, com teto 99
→ proficiência, com piso 40 e teto 99
→ boost do técnico
→ ímpetos
→ efeito de habilidade, quando a régua o utiliza
```

O incremento da proficiência continua truncado pela implementação do Otimizador. O
boost e os ímpetos entram depois do teto da proficiência e podem produzir resultado
final acima de 99.

## Prova que decidiu

- Lionel Messi `89138556575063`;
- 19 níveis em Chute, Finalização 99 antes do campo;
- Fabio Capello, Contra-ataque com bolas longas 89, multiplicador `1,036` e boost
  `+1` em Finalização;
- ímpeto fixo Precisão `+4` em Finalização;
- resultado real exibido no campo: **104**.

A regra vigente reproduz `99 → 99 → 100 → 104`. A tentativa posterior — ímpetos
antes da proficiência e ausência de teto nessa etapa — previa 107 com o truncamento
codificado, ou 107,708 antes de uma possível apresentação inteira. Portanto ela não
explica o 104 observado e está **REPROVADA E REVOGADA**.

Limite da prova: o experimento decide entre essas duas hipóteses no cenário descrito.
Ele não prova como o videogame representa internamente frações em todos os demais
casos. A tela exibir inteiro, sozinha, não autoriza concluir que não existam valores
internos fracionários.

## Arquivos com hunk de fórmula restaurado

- `2-MOTORES/OTIMIZADOR/equacao.py`;
- `2-MOTORES/OTIMIZADOR/motor.py`;
- `6-AVALIADOR-NO-RAILWAY/avaliador.py`;
- `6-AVALIADOR-NO-RAILWAY/otimizador.py`;
- `6-AVALIADOR-NO-RAILWAY/servidor.py`;
- `1-SISTEMA/motor-e-ficha-base.js`;
- `SITE-ATUALIZADO-2026-08-24/motor-e-ficha-base.js`;
- `SITE-ATUALIZADO-2026-08-24/TELA-CLUBEFOOTBALL-UNICA.html`.

## Integrações preservadas

A comparação byte a byte com o snapshot anterior confirmou que estes arquivos não
foram modificados pela reversão:

- `2-MOTORES/OTIMIZADOR/roda_lote_v6.py`;
- `6-AVALIADOR-NO-RAILWAY/app.py`;
- `6-AVALIADOR-NO-RAILWAY/monta_regua.py`;
- `6-AVALIADOR-NO-RAILWAY/regua_do_banco.py`;
- `4-DOCUMENTOS/MANUAL-TECNICO.md`.

Também foram preservados os vetores separados de ímpeto e boost, a leitura canônica
de Técnicos, maior proficiência, estilos gêmeos, boosts canônicos e as demais mudanças
preexistentes do worktree. A reversão não trocou fontes de entrada.

## Regressões permanentes

- [x] `teste_formula_aprovada.py`: fórmula real local, Otimizador local, avaliador,
  otimizador do servidor, encaminhamento separado de boost/ímpeto e contrato canônico
  de Capello;
- [x] `teste_interface_formula_aprovada.js`: três cópias da interface com a mesma
  ordem e resultado 104;
- [x] `_mult(98, 1,036) = 99`;
- [x] `_mult(99, 1,036) = 99`, nunca 102 nessa etapa;
- [x] Messi: `99 → proficiência 99 → boost 100 → Precisão 104`;
- [x] Capello: maior proficiência 89, estilos gêmeos `longBallCounter` e `longBall`,
  boosts canônicos `[6, 10]`, sem soma de proficiências empatadas;
- [x] sintaxe Python validada em dez arquivos da cadeia;
- [x] sintaxe JavaScript validada nas duas cópias modulares; o HTML único foi coberto
  pela extração e execução da função no teste das interfaces;
- [x] busca por hunk executável da hipótese revogada sem ocorrência fora do pacote de
  recuperação e dos registros históricos;
- [x] nenhuma execução de lote, gravação de banco ou ativação de consumidor.

Resultado dos testes em 28/08/2026: **todos aprovados, código de saída zero**.

## Recuperação e rollback

O estado anterior à reversão foi capturado antes dos hunks de código em:

`4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/2026-08-28-ANTES-REVERSAO-FORMULA`

Arquivos de recuperação:

| arquivo | bytes | SHA-256 |
|---|---:|---|
| `arquivos-antes-com-caminhos.zip` | 1.183.924 | `1012FF3F60D19B26CD1340F449343B7527A513BFC2193AAFF711D1165F0FD776` |
| `arquivos-antes.zip` | 1.183.293 | `D72BB671B484394AD771A60C7457B7856DCF5C72E61AD543AE84BC66BB5EEEF5` |
| `worktree-rastreado-antes.patch` | 205.024 | `F9DD8E4913F7D6F7CDBCEECCE624C82418401D2DDD9D8CCD97942EF213788A8B` |

O arquivo `arquivos-antes-com-caminhos.zip` é a cópia preferida para recuperação:
preserva os caminhos relativos do projeto. Suas 16 entradas foram comparadas byte a
byte com o snapshot original. Restaurá-lo reintroduziria a fórmula reprovada; portanto
esse rollback só pode ser executado mediante nova autorização expressa.

## Trava contra reintrodução acidental

- [x] regra anterior marcada como vigente no Manual do Otimizador;
- [x] tentativa posterior registrada como hipótese, não como descoberta;
- [x] cenário Messi/Capello/Precisão registrado como teste discriminante obrigatório;
- [x] testes que aprovavam proficiência sem teto removidos e substituídos;
- [x] qualquer futura mudança da ordem ou do teto exige nova autorização e nova prova
  física que realmente diferencie as hipóteses.
