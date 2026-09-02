# Snapshot anterior — fila direta do Otimizador V6

Antes da mudança, a V5 e o writer exigiam `lote_estado='concluido'`,
`estado='pendente'` e o marcador `bonificador_nao_executado`. A esteira V6 do
Otimizador não materializava esses campos, embora já tivesse concluído o resultado.

Preflight: 10.540 linhas do lote integral tinham resultado concluído do Otimizador,
sem resultado Bonificador e permaneciam invisíveis à V5. A alteração aplicada é
somente `CREATE OR REPLACE FUNCTION`: não criou nem modificou dados.

Recuperação lógica: restaurar os três filtros anteriores nas duas RPCs
`public.bonificador_contexto_fila_v5` e `public.gravar_build_bonificador_v4`; para o
writer, remover o retorno idempotente e recusar vínculo `build_bonificador_id` já
existente. O histórico remoto da alteração é `bonificador_fila_direta_otimizador_v6`.
