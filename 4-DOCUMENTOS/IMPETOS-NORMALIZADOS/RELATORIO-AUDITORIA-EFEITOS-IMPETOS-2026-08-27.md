# Auditoria e normalização dos efeitos de ímpetos — 27/08/2026

## Resultado objetivo

A origem física foi mapeada e reconciliada sem escrever no banco. O catálogo usa
o `codigo_jogo` completo como identidade da variação do ímpeto. Não existe, no
contrato de carga, decomposição da carta em família visual + grau.

- catálogo físico unido: 440 códigos;
- receitas com dicionário comparável: 350/350 conferidas;
- relações físicas ímpeto × atributo: 1.542;
- deltas observados: 1 a 6;
- relações aptas agora: 488;
- relações bloqueadas: 1.054;
- divergências entre dicionário e bytes: zero;
- divergências semânticas DT200 × DT870 atualizado: zero.

Nenhuma migração foi aplicada: o PostgreSQL ficou sem espaço, entrou em recuperação
e não aceita conexões. `clube`, `clube_novo`, cartas, interface, Extrator e
Otimizador não foram alterados por esta frente.

## Fontes e prioridade

| fonte | SHA-256 | registros | papel |
|---|---|---:|---|
| DT200 `PlayerBooster.bin` | `fd920cd8e7f3f1089892ef4051c68c1c5c56c49000ecf6f751025a0ae2c94a50` | 195 | receita atual e conferência |
| DT870 Steam original | `ae0d8cef26804439e9930ef8959f8d9425754d0e290d056b3e4d1f7b999edd5c` | 102 | identidade/procedência; layout legado |
| DT870 atualizado | `44df868c2613d532292d87072c0863a907d6a5f0cc40f914d355e56d74edfcc5` | 408 | fonte autoritativa atual |

O DT870 original não foi decodificado com offsets do registro atual: seu
`PlayerBooster.bin` tem tamanho legado. Isso eliminou uma falsa divergência que a
primeira versão do validador poderia produzir.

## Contrato físico comprovado

O registro atual de `PlayerBooster.bin` tem 40 bytes. O código fica no bit 112,
largura 10; o nível no bit 212, largura 3. Os deltas são campos de 5 bits. Há
endereços individuais comprovados para 23 atributos.

Os três campos de goleiro nos bits 192, 197 e 256 permanecem bloqueados. Embora
fisicamente distintos, nos 350 códigos conhecidos eles aparecem sempre juntos e
com o mesmo delta; os dados disponíveis não provam qual campo corresponde a cada
uma das três chaves canônicas de goleiro.

O marcador físico separa 131 códigos sem condição de 219 códigos com condição.
Para os 219, a existência da condição é provada, mas sua semântica e parâmetros
não são. Portanto não foi criada entidade de condição nem inferência por nome.

## Slots da carta

No `Player.bin`, o slot condicional está no bit 288 e o principal no bit 308,
ambos com largura 10. `0` significa sem ímpeto; `136`, vaga. A carga atual contém
2.324 slots principais e 57 condicionais preenchidos. Há 270 atribuições acima de
255; a leitura de 8 bits converte uma delas em `0` e duas em `136`.

Exemplos físicos:

- Nesta `88036360701097`: principal 30 (`Duelo +3`), condicional 136;
- Desailly `89138288270047`: principal 207, condicional 136;
- Messi `89138556575063`: principal 199, condicional 507; a leitura antiga retorna 251.

A correção dos slots em carta/Extrator é pré-requisito futuro da relação
`carta_impeto_jogo`, mas está fora do escopo desta frente.

## Aplicação parcial preparada

O SQL preparado adiciona `delta` numérico e proveniência física à relação e
registra o estado de condição no catálogo. Somente 488 relações incondicionais,
com atributo individual comprovado, ficam `confirmado=true`. As 1.054 restantes
continuam bloqueadas. `pode_rodar` não é promovido.

A migração exige o preflight local em modo somente leitura e inclui contagens,
órfãos, trava consultiva, constraints, readback e rollback. Ela não deve ser
executada enquanto `PREFLIGHT-BANCO-READONLY.json` não existir com
`preflight_ok=true`.

## Estado do banco e espaço

A tarefa paralela de relações de cartas carregou quatro famílias e confirmou
1.267.352 linhas. A tentativa de atributos abortou integralmente com erro 53100;
readback registrou zero linhas, mas a relação vazia ficou com cerca de 89 MB
físicos. Os logs do PostgreSQL confirmaram falha ao criar `pg_wal/xlogtemp` por
falta de espaço. Nenhuma ação de manutenção ou limpeza foi feita por esta auditoria.

**Histórico revogado:** houve autorização temporária para remover a tabela legada,
mas o usuário a revogou antes da execução. `clube.carta_jogo` deve ser preservada.
O script destrutivo foi retirado para impedir execução acidental.

## Artefatos e hashes

- `ARTEFATOS/MANIFESTO-AUDITORIA-FISICA.json` — SHA-256 `8D2730365A9B6192AC50E6AE0F9CEE82C8F52965EF879863613DDB884063CD46`;
- `ARTEFATOS/MATRIZ-RECEITAS-CANDIDATAS.csv` — SHA-256 `C25A0103EE3FD470B0AE0E14D7460C8C705F31A6BBA80FBF8D11BF7F0414D251`;
- `ARTEFATOS/VALIDACAO-DICIONARIO-X-FISICO.csv` — SHA-256 `AD1BFBE94CE297BF2C10B5673CED1289268A72C06BA2270071A8F33D359205AB`;
- `ARTEFATOS/AMOSTRAS-SLOTS-CARTA.json` — SHA-256 `9646C586421202049D64EB9A70C4BD26EC1517EEAFF9CB2F04B01B8F172F71CA`;
- `preflight-banco-impetos.py` — auditoria live somente leitura;
- `SQL/20260827_normalizar_efeitos_impetos_parcial.sql`;
- `SQL/VALIDAR-20260827_normalizar_efeitos_impetos_parcial.sql`;
- `SQL/ROLLBACK-20260827_normalizar_efeitos_impetos_parcial.sql`;
- `SQL/REVOGADO-NAO-REMOVER-CLUBE-CARTA-JOGO.md` — registro da revogação.
