# Contrato de materialização da completude dos motores V1

Status deste pacote: `prepared_not_enabled`. Os SQL foram preparados e testados
offline, mas não foram aplicados no banco vivo. O worker não deve chamar estes
RPCs nem liberar Otimizador/Bonificador enquanto a migração, o seed e o
`VALIDAR-COMPLETUDE-MOTORES-CARTA-V1.sql` não terminarem com sucesso.

## O que esta regra controla

Controla apenas entrada em fila, início e conclusão do Otimizador e do
Bonificador. Não controla a inserção da carta, Home, box, foto, novidade ou
publicação. Uma carta incompleta pode entrar e aparecer normalmente; os motores
ficam fechados até existir uma versão vigente e apta.

## Como não enviar todas as cartas todos os dias

1. **Seed inicial, uma vez:** usar o artefato físico de base já revisado para
   materializar os 11 componentes de todas as cartas. Não reconstruir o seed a
   partir de `NULL`, `[]` ou `0` do banco.
2. **Rodadas seguintes:** depois da aplicação explícita e do readback do pacote,
   passar a `clube_novo.planejar_completude_motor_v1(text[])` somente os
   `card_id` novos ou tocados naquele pacote.
3. O planejador devolve:
   - `materializar`: carta sem versão ou `input_fingerprint` alterado;
   - `revisao_manual`: input igual, mas bloqueio já registrado;
   - `nenhuma`: input igual e validação vigente;
   - `erro`: `card_id` não existe.
4. Chamar `clube_novo.registrar_completude_motor_v1` somente para
   `materializar`. `revisao_manual` nunca vira liberação automática.

O planejador calcula o fingerprint do input dentro do banco. O cliente não
envia um hash para ser aceito como verdade.

## Envelope do registrador

RPC: `clube_novo.registrar_completude_motor_v1(text,bigint,jsonb)`

- `p_card_id`: identidade real de `clube_novo.carta_jogo`.
- `p_aplicacao_id`: aplicação auditada do Extrator com estado `aplicado`.
- `p_componentes`: exatamente os 11 objetos abaixo, sem duplicatas.

Exemplo reduzido, mas estruturalmente completo:

```json
[
  {"componente":"dados_basicos","estado_coleta":"conferido_com_valor","estado_resolucao":"resolvido","apto_motor":true,"quantidade_valores":10,"proveniencia":{"arquivo":"Player.bin","trecho":"registro da carta"},"evidencia":{}},
  {"componente":"dimensoes","estado_coleta":"conferido_com_valor","estado_resolucao":"resolvido","apto_motor":true,"quantidade_valores":6,"proveniencia":{"arquivo":"Player.bin","trecho":"códigos brutos"},"evidencia":{}},
  {"componente":"atributos","estado_coleta":"conferido_com_valor","estado_resolucao":"resolvido","apto_motor":true,"quantidade_valores":26,"proveniencia":{"arquivo":"Player.bin","trecho":"26 atributos"},"evidencia":{}},
  {"componente":"corpo","estado_coleta":"conferido_com_valor","estado_resolucao":"resolvido","apto_motor":true,"quantidade_valores":12,"proveniencia":{"arquivo":"Appearance.bin","trecho":"12 medidas usadas"},"evidencia":{}},
  {"componente":"posicoes","estado_coleta":"conferido_com_valor","estado_resolucao":"resolvido","apto_motor":true,"quantidade_valores":12,"proveniencia":{"arquivo":"Player.bin","trecho":"aptidões"},"evidencia":{}},
  {"componente":"posicao_principal","estado_coleta":"conferido_com_valor","estado_resolucao":"resolvido","apto_motor":true,"quantidade_valores":1,"proveniencia":{"arquivo":"Player.bin","trecho":"posição principal"},"evidencia":{}},
  {"componente":"habilidades","estado_coleta":"conferido_sem_valor","estado_resolucao":"nao_aplicavel","apto_motor":true,"quantidade_valores":0,"proveniencia":{"arquivo":"Player.bin","trecho":"lista fisicamente lida e vazia"},"evidencia":{}},
  {"componente":"estilos_ia","estado_coleta":"conferido_sem_valor","estado_resolucao":"nao_aplicavel","apto_motor":true,"quantidade_valores":0,"proveniencia":{"arquivo":"Player.bin","trecho":"bits fisicamente lidos e vazios"},"evidencia":{}},
  {"componente":"pes","estado_coleta":"conferido_com_valor","estado_resolucao":"resolvido","apto_motor":true,"quantidade_valores":3,"proveniencia":{"arquivo":"Player.bin","trecho":"três campos de pé"},"evidencia":{}},
  {"componente":"playstyles","estado_coleta":"conferido_com_valor","estado_resolucao":"resolvido","apto_motor":true,"quantidade_valores":2,"proveniencia":{"arquivo":"Player.bin","trecho":"dois slots brutos"},"evidencia":{}},
  {"componente":"impetos","estado_coleta":"conferido_sem_valor","estado_resolucao":"nao_aplicavel","apto_motor":true,"quantidade_valores":0,"proveniencia":{"arquivo":"PlayerBooster.bin","trecho":"dois slots lidos como vazios"},"evidencia":{}}
]
```

`conferido_sem_valor` é completo e exige quantidade zero mais proveniência.
`nao_conferido` e `leitura_com_problema` bloqueiam o motor. Pendência de nome
ou catálogo não entra em `missing_inputs`; fica em `estado_resolucao`.

Isso preserva os fatos do snapshot de base: 9.551 listas de habilidades vazias,
18.218 listas de estilo de IA vazias e 40.748 slots de Ímpeto vazios foram
fisicamente conferidos e não são faltas. Da mesma forma, código bruto lido com
rótulo pendente é pendência de resolução, não falha de coleta.

## Decisão manual separada

Uma pendência conhecida só pode ser não bloqueante por ação explícita do
operador/política versionada. O componente conserva a pendência e inclui:

```json
"evidencia": {
  "decisao_motor": {
    "tipo": "politica_versionada",
    "motivo": "código bruto foi lido; o rótulo não participa do cálculo",
    "referencia": "politica-catalogos-v1"
  }
}
```

A decisão é persistida separadamente em
`clube_novo.carta_completude_motor_decisao`. Ela não apaga o aviso nem substitui
a coleta. Para clube que perdeu licença, usar
`estado_resolucao="orfao_catalogo_atual"` no componente `dimensoes`, preservar
o código bruto/proveniência e registrar a decisão. O motor trata o vínculo
atual como ausente, sem inventar outro clube.

## Fechamento do escritor legado do Bonificador

`public.gravar_bonus(jsonb)` escreve em `clube.build` e contorna a conclusão
versionada. Na aplicação desta migração:

1. proprietário, retorno, grantees e grant option atuais são fotografados em
   `clube_novo.migracao_gravar_bonus_grant_snapshot_v1`;
2. a implementação original é preservada como
   `public.gravar_bonus_sem_completude_v1(jsonb)`, sem grants de execução;
3. o nome `public.gravar_bonus(jsonb)` passa a ser um bloqueador que sempre
   falha e informa que nenhuma linha foi gravada;
4. `PUBLIC`, `anon`, `authenticated`, `service_role`, o proprietário e todos os
   grantees capturados ficam sem `EXECUTE` nas duas portas.

Não existe redirecionamento automático para outra tabela. Para o Bonificador
voltar a gravar, deve existir um escritor novo e explícito em
`clube_novo.build_bonificador` + `build_linha_card`, passando pelos fingerprints
e pelos gates de conclusão. Isso não interfere na publicação/Home/box da carta.
O rollback remove o bloqueador, devolve o nome à implementação original e
restaura exatamente os grantees e grant option fotografados.

## Readback independente

Depois de cada materialização, em uma nova leitura:

1. conferir a linha vigente e os 11 componentes;
2. conferir que `input_fingerprint_sha256` coincide com o input canônico atual;
3. chamar novamente o planejador: o resultado esperado é `nenhuma` ou
   `revisao_manual`, nunca `materializar`;
4. conferir `public.otimizador_carta_v2` e `public.bonificador_carta_v1`;
5. somente habilitar workers depois que o SQL de validação integral passar.

Se o input mudar depois, os triggers invalidam a versão e a linha ativa. A nova
conclusão exige novo `carta_versao` + `carta_fingerprint`; um resultado antigo
não pode parecer calculado para o dado novo.
