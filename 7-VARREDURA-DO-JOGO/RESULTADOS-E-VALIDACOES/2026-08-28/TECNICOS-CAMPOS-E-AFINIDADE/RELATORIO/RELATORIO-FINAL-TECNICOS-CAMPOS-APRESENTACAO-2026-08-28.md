# Relatório final — idade, nacionalidade e afinidade de técnicos

Data: 28/08/2026  
Escopo de banco: exclusivamente `clube_novo`  
Legado `clube`: preservado, sem escrita  
Otimizador e executável: não usados nem alterados

## Resultado

A migração `tecnico_idade_nacionalidade_afinidade_v1` foi aplicada e reexecutada
com sucesso. Ela acrescentou os campos de apresentação às 1.478 card-versões de
técnico existentes no DT870 atualizado, manteve 116 identidades históricas sem
preenchimento inventado e criou os catálogos canônicos:

- `clube_novo.nacionalidade_jogo`: 214 linhas;
- `clube_novo.afinidade_tecnico_jogo`: 8 linhas, códigos 0–7;
- `clube_novo.tecnico_jogo`: 1.594 IDs distintos, sendo 1.478 atuais completos e
  116 históricos com os três campos nulos.

Foram criadas duas FKs `ON DELETE RESTRICT`, checks de domínio e completude e os
índices das FKs. As 7.390 relações de estilo e as 104 relações de boost anteriores
foram preservadas.

## Contrato físico reproduzível

| campo | fonte | endereço | transformação |
|---|---|---|---|
| ID da card-versão | `Coach.bin` do DT870 atualizado | byte 0, u64 little-endian; registro 176 bytes | nenhuma |
| idade | `Coach.bin` | bit 231, largura 7 | valor físico + 14 |
| nacionalidade | `Coach.bin` | bit 170, largura 8 | resolve por FK em `Country.bin` |
| afinidade | `Coach.bin` | bit 187, largura 3 | código 0 é ausência legítima |
| código de nacionalidade | `Country.bin` | bit 10, largura 9; registro 1.488 bytes | nenhuma |
| sigla | `Country.bin` | offset 708, largura máxima 10 | ASCII/UTF-8 terminado por NUL |
| nome pt-BR | `Country.bin` | offset 788, largura máxima 70 | UTF-8 terminado por NUL |
| rótulo da afinidade 5 | `all.str` | `Any1W:495` | `Jogadores de AT`; tela: `Atacantes` |

Hashes das fontes físicas:

- CPK DT870 atualizado: `44df868c2613d532292d87072c0863a907d6a5f0cc40f914d355e56d74edfcc5`;
- `Coach.bin`: `092a07c62d1df0f19da6ad0e4e1252de07e5e1df8e9090760734829044c0d42a`;
- `Country.bin`: `6dcb876a1922281cc5bf513f8ee117846fbeed42e48936f40af2007232c1b0a7`;
- `all.str`: `306741adab8376ed64620b618ae9721d316ae548b126419730b9bd5ff5f525a9`.

O `Country.bin` é byte-idêntico nas três versões auditadas: DT200, DT870 original e
DT870 atualizado. O banco registra índice do registro, fonte, CPK, arquivo, endereço,
largura, transformação, hash, versão do contrato e presença por versão. Sete linhas
granulares foram acrescentadas a `clube_novo.mapa_do_jogo`, totalizando 28.

## Readback e idempotência

A mesma migração foi executada uma segunda vez sobre o pacote já carregado. Contagens
e fingerprints semânticos antes/depois permaneceram idênticos:

| conjunto | contagem | fingerprint SHA-256 |
|---|---:|---|
| técnicos | 1.594 | `509273e2eee7e97bf1c6767de4e7bb6668c8211bceec9c0ba506b9cb3ffb07a0` |
| nacionalidades | 214 | `5dae7a63b49cb914d7b6d4793a0e0438c5ba3a84bf327d6ad89a20e0cb633933` |
| afinidades | 8 | `98cb27f2edad4384cd2743b9f6de9982ea99223cb074dba7d7af1b7db0397f4d` |
| sete linhas do mapa | 7 | `1b8c90033c257ce11c23d72cb477a776a66a4e7fc93f46c30435b8ce7a0b1dbe` |

Validações adicionais:

- IDs únicos: 1.594/1.594;
- idade dos registros atuais: 28–80;
- nacionalidades órfãs: zero;
- afinidades órfãs: zero;
- distribuição da afinidade: 0=1.456, 1=2, 2=3, 3=4, 4=4, 5=3, 6=2, 7=4;
- Fabio Capello `17601312850052`: idade 44, Itália/ITA (215), afinidade 5/Atacantes.
- readback final somente leitura: `clube.carta_jogo` 42.803,
  `clube_novo.carta_jogo` 43.072, `clube.tecnico` 1.664 e
  `clube_novo.tecnico_jogo` 1.594; o legado permaneceu intacto.

O arquivo de prova é `READBACK-IDEMPOTENCIA-CAMPOS-TECNICO.json`, SHA-256
`ce3a2f0cdfc4f2c1a2dcf180977e25a2e102559e5de37d2a28e828e7bc283552`.

## Extrator

O núcleo-fonte passou a:

1. exigir e validar `Coach.bin` e `Country.bin` no DT870 atualizado;
2. extrair automaticamente idade, nacionalidade e afinidade de 1.478 técnicos;
3. extrair as 214 nacionalidades e os oito códigos de afinidade com procedência;
4. falhar fechado se houver ID duplicado, nacionalidade órfã, formato incompatível
   ou ausência do texto oficial que comprova o código 5;
5. comparar as três famílias contra a referência interna selada.

Referência vigente: `meta-ref-eba124d25472-8a7735bee1b6`; a anterior
`meta-ref-eba124d25472-b64fc205c8b2` foi mantida. O teste do núcleo operacional
resultou em 0 novas, 0 alteradas, 0 ausentes e 0 sem fingerprint nas três famílias.

Fonte instalada: `app/extrator-core.js`, SHA-256
`f1a5255da12f9c5f174350d0054547913ac57000a76ced693320d4ad67fc8e90`.
A descrição da fonte automática foi atualizada em `app/extrator-ui.js`, SHA-256
`df48adeb691d6675dcd2a89575a5ba387d531c5e205e69c7226cc031a3427153`.
A versão anterior está em
`RECUPERACAO/2026-08-28-ANTES-CAMPOS-APRESENTACAO-TECNICOS/extrator-core.js`,
SHA-256 `4ab07c6e25f712e75411fc9ea4d89cfd3f0ea15b00685e015413f217134afe77`.
O `Extrator eFootball.exe` permaneceu com 103.936 bytes e data 27/08/2026 19:34:32.

## Segurança e limites

As duas novas tabelas não concedem `USAGE` de schema nem `SELECT` a `anon`,
`authenticated` ou `service_role`; embora RLS esteja desligada, elas não estão
expostas por esses papéis. O Security Advisor também mantém avisos preexistentes em
outros objetos do projeto; nenhuma política ou permissão fora deste escopo foi mudada.

Somente o código 5 de afinidade recebeu rótulo. Os códigos 1, 2, 3, 4, 6 e 7
permanecem sem nome e `pode_rodar=false`; nenhum texto foi inferido. Link-up e
Sobreposição/Overload continuam fora desta carga. A escrita automática de metadados
continua desabilitada.

## Recuperação

- rollback estrutural e de dados: `ROLLBACK-20260828_tecnico_idade_nacionalidade_afinidade.sql`;
- migração reproduzível: `20260828_tecnico_idade_nacionalidade_afinidade.sql`;
- validação SQL: `VALIDAR-20260828_tecnico_idade_nacionalidade_afinidade.sql`;
- fonte anterior do Extrator: pasta `RECUPERACAO` citada acima;
- referência anterior: preservada em `artefatos/referencias-metadados/versoes`.

O rollback não deve ser executado automaticamente: requer autorização específica,
pré-voo e novo readback.
