# Relatório final — Sobreposição de técnicos

**Data:** 28/08/2026  
**Escopo:** DT870 atualizado, família Técnicos, schema `clube_novo` e fonte do Extrator.  
**Exclusões respeitadas:** nenhum acesso ao executável do jogo, nenhum uso do `Extrator eFootball.exe`, nenhuma alteração em `clube`, cartas, Link-up ou estruturas não relacionadas.

## Resultado

Sobreposição foi localizada e comprovada no `Coach.bin` do DT870 atualizado. Ela usa
um campo próprio de proficiência, fisicamente separado dos cinco estilos históricos:

- arquivo: `Coach.bin`;
- registro: 176 bytes;
- bit inicial: **135**;
- largura: **7 bits**;
- leitura: inteiro sem sinal, little-endian por bits;
- distribuição integral: **1.477 registros com 0 e um registro com 96**;
- único registro não zero: Antônio Conte, ID físico `17609097478250`, índice 1.476;
- controle negativo: Fabio Capello, ID `17601312850052`, índice 1.453, valor 0.

O DT870 auditado tem SHA-256
`44df868c2613d532292d87072c0863a907d6a5f0cc40f914d355e56d74edfcc5`.
O `Coach.bin` descompactado tem SHA-256
`092a07c62d1df0f19da6ad0e4e1252de07e5e1df8e9090760734829044c0d42a`.

O campo fica imediatamente após o código físico de Link-up, mas não foi modelado
como Link-up nem como sexta coluna fixa. O texto oficial `Any10T:793` resolve para
`Sobreposição`, e `Any7T:255` descreve seis estilos de jogo do time. Os arquivos
`CoachTactics.bin` e `CoachTacticsFormation.bin` são entradas vazias de 16 bytes;
`CoachVariationDetail.bin` guarda somente ID e rótulo de pacote/variação, sem payload
numérico adicional. A proficiência reproduzível está no `Coach.bin`.

## Modelo aplicado

Não foi criada tabela nem coluna nova.

- `clube_novo.estilo_jogo_tecnico`: o registro existente `overload` foi promovido
  para `bit=135`, `largura=7`, `pode_rodar=true`, sem lacuna pendente.
- `clube_novo.tecnico_estilo_jogo`: foi inserida somente a relação
  Antônio Conte × `overload` × proficiência 96, com índice do registro, bit, largura,
  fonte e hash.
- valor zero representa ausência legítima; portanto os outros 1.477 técnicos não
  receberam relação artificial.
- `clube_novo.mapa_do_jogo`: foi acrescentado o assunto
  `tecnico.estilo.sobreposicao` com a prova física completa.

## Validação do banco

| verificação | antes | depois |
|---|---:|---:|
| estilos no catálogo | 6 | 6 |
| estilos aptos | 5 | 6 |
| relações técnico × estilo | 7.390 | 7.391 |
| relações de Sobreposição | 0 | 1 |
| relações históricas preservadas | 7.390 | 7.390 |
| órfãos de FK | 0 | 0 |

A migração foi executada em transação, com trava consultiva, verificações antes e
depois e reconciliação idempotente. Uma segunda execução produziu o mesmo estado
semântico. O fingerprint das 7.390 relações históricas permaneceu idêntico.

O readback do Otimizador por `public.regua_pacote()` confirmou:

- Conte: `overload=96`, `proficiencia_maxima=96`, principal `overload`, sem gêmea;
- Capello: sem chave `overload`, máxima 89, principal `longBallCounter` e gêmea
  `longBall`.

## Extrator e referência interna

O núcleo-fonte do Extrator foi atualizado para o contrato
`clubef-tecnicos-carga-v4-sobreposicao`:

- lê o bit 135/largura 7;
- inclui `overload` em `proficiencias` somente quando o valor é maior que zero;
- mantém o campo e a transformação na proveniência do registro;
- bloqueia duplicidade e continua comparando 1.478 IDs únicos.

A referência interna vigente passou a
`meta-ref-eba124d25472-9db3bc3ebba1`, com SHA do manifesto
`0d011072d3b03e6eb582cd49655cae68ac6c83247022b0b1618927a39ffa977a`.
A comparação do fonte operacional contra essa referência terminou com zero novo,
zero alterado, zero ausente e zero registro sem fingerprint em técnicos,
nacionalidades e afinidades.

O `Extrator eFootball.exe` não foi aberto, alterado nem recompilado. O núcleo
operacional `app/extrator-core.js` foi instalado diretamente e validado. A cópia
anterior está em
`RECUPERACAO/2026-08-28-ANTES-SOBREPOSICAO-TECNICOS/app/extrator-core.js`.

## Documentação e pendência separada

Foram atualizados:

- `4-DOCUMENTOS/MANUAL-DAS-TABELAS.md`;
- `4-DOCUMENTOS/MANUAL-DO-OTIMIZADOR.md`;
- `4-DOCUMENTOS/MAPA-DO-CODIGO-DO-JOGO.md`;
- `7-VARREDURA-DO-JOGO/DOCUMENTACAO/MANUAL-DO-EXTRATOR.md`.

Link-up foi explicitamente adiado para uma frente futura e não bloqueia a conclusão
de Técnicos. Nenhum dado ou relação de Link-up foi criado nesta operação.

## Recuperação

O pacote contém `ROLLBACK-20260828_tecnico_sobreposicao.sql`. Ele remove somente a
relação Conte/Sobreposição, volta o registro `overload` ao estado bloqueado anterior e
remove somente o mapeamento físico correspondente. Não toca em identidades, cinco
estilos históricos, boosts, cartas ou schema legado.

## Encerramento da frente Técnicos

A conferência final de 28/08/2026 executou novamente o núcleo operacional contra o
DT870 atualizado e comparou integralmente o resultado com a referência vigente e com
`clube_novo`, em transação somente leitura. O resultado foi aprovado:

- 1.478 IDs atuais coincidentes, sem divergência de identidade, idade,
  nacionalidade ou afinidade;
- 7.391 relações de estilo coincidentes, incluindo Sobreposição 96 somente em
  Antônio Conte;
- 104 boosts coincidentes em atributo, ordem, delta, bit e proveniência;
- 214 nacionalidades e 8 códigos de afinidade coincidentes;
- zero órfão e zero divergência campo a campo;
- referência `meta-ref-eba124d25472-9db3bc3ebba1`, ponteiro, manifesto e snapshot
  íntegros.

O núcleo operacional recebeu posteriormente alterações fora da família Técnicos.
Por isso seu hash integral difere da fotografia anterior, mas o bloco do extrator de
Técnicos é byte a byte idêntico ao validado, com SHA-256
`8b8d22bee2c4bd7eca16436e46135634972d7d7d5ad7121dd527fb012d049ed1`.
Ele foi executado com sucesso a partir da instalação operacional; não houve
reinstalação nem sobrescrita desnecessária.

As provas finais estão em
`VALIDACAO-FINAL-ENCERRAMENTO-TECNICOS-2026-08-28.json` e
`MANIFESTO-ENCERRAMENTO-TECNICOS-2026-08-28.json`. Nenhuma escrita no banco foi
feita nesta conferência. Link-up permanece como frente futura separada; a frente
Técnicos está encerrada.
