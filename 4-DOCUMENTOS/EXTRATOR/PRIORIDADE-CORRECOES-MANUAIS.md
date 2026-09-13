# Prioridade das correções manuais

Decisão atual de Luis: qualquer valor corrigido manualmente prevalece sobre
o Extrator, inclusive quando o arquivo do jogo fornece outro valor.

## Banco

A estrutura existente `clube_novo.valor_do_dono` foi ampliada. Não há uma
segunda tabela concorrente de valores vigentes. Os 33 destinos protegidos
abrangem todos os destinos ativos declarados pelo Extrator e os catálogos
que já tinham proteção.

Cada decisão informa `destino_schema`, `destino_tabela`, `chave` (a chave
primária completa), `coluna`, `valor` JSON e `porque`. Inserir ou atualizar
essa decisão valida o tipo, aplica o valor e registra a alteração em
`valor_do_dono_historico`, com autor da conexão e horário, atomicamente.

O trigger de validação conserva seu nome histórico
`tg_valor_do_dono_so_onde_o_jogo_nao_diz`, mas a restrição antiga foi removida:
não exige campo ausente nem recusa campos lidos pelo Extrator. Valida
existência do destino protegido, identidade completa e coluna gravável.
Colunas geradas e chaves primárias exigem alteração da fonte ou da identidade
correspondente, não uma sobreposição inválida sobre uma coluna calculada.

`zzzz_valor_do_dono` preserva o valor em INSERT/UPDATE e bloqueia DELETE ou
troca da identidade de registros protegidos. Remover explicitamente uma
decisão de `valor_do_dono` libera o campo e mantém o último valor aplicado.
A remoção também fica no histórico; não restaura silenciosamente valor antigo.

UPDATE direto em uma tabela não registra automaticamente uma nova decisão
manual. Quem executar uma correção pedida por Luis deve usar o registro
de decisão acima. Não retirar a proteção para fazer a extração passar.

As tabelas de decisões e histórico não têm acesso público. A operação utiliza
a conexão administrativa protegida, sem credenciais no frontend público.

## Aplicativo e tela

O pacote físico conserva os valores extraídos e sua procedência. O banco
aplica a prioridade manual. A conferência por lote e a conferência final
comparam os valores persistidos com a composição de fonte física e decisões
manuais atuais. Uma divergência não coberta por decisão continua sendo erro.

O relatório de insumos mostra os campos protegidos e explica que a correção
prevalece mesmo quando o jogo informa outro valor. Outros campos do mesmo
registro podem ser atualizados. Essa tela informa decisões já registradas;
não é um editor genérico novo.

## Verificação desta implantação

- Migração `valor_do_dono_prioridade_integral` aplicada no Supabase.
- Ensaio transacional em atributo real: registro manual aceito, tentativa de
  sobrescrita preservou o valor, exclusão protegida foi recusada. Todo o
  ensaio foi revertido, sem alteração permanente do atributo.
- Leitura posterior: 33 tabelas protegidas, zero destino ativo sem proteção,
  sete decisões anteriores preservadas, zero registro de teste residual.
- Testes locais cobrem identidade exata, proteção por campo, null explícito
  e preservação do pacote físico.

A conferência de níveis separa agora a prova coletada dos valores efetivos
de level_cap, orcamento e cap_estimado. A migração
`extrator_conferencia_niveis_manuais` ajustou o writer de memória; a releitura
Python e a consulta de confirmação eFHUB respeitam o registro por carta e
campo. Os relatórios explicam essa distinção. Onze testes de níveis e nove
de eFHUB passaram; os testes de níveis incluem rejeição de prova divergente
mesmo quando há valor manual. A consulta efetiva foi executada no banco.

Em 13/09, o aplicativo aplicou 23.797 envelopes e releu integralmente os
valores persistidos. As 455 decisões registradas, incluindo técnicos,
foram comparadas campo a campo com seus destinos: todas preservadas.
O botão de níveis aplicou 42 cartas com prova física e releitura confirmada.
A seleção de orçamento usa os valores efetivos, conservando separadamente
a prova física. A coleta eFHUB terminou com 176 leituras válidas e dez pendências sem nível válido na fonte. Posição e slots passam a espelhar as relações normalizadas; o trigger de proteção manual continua prevalecendo.
