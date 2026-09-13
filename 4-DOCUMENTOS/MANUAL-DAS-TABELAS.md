# Tabelas e contratos operacionais

Autoridade: `clube_novo`. Este índice descreve os papéis; a definição vigente de
colunas, tipos e permissões é a do banco e dos SQLs versionados. Não congelar contagens
de linhas como contrato nem usar tabelas históricas para preencher dados ausentes.

| Domínio | Objetos principais | Responsabilidade |
|---|---|---|
| Carta | `carta_jogo`, `carta_operacional_v1` | Cadastro e universo disponível |
| Prova | `carta_nivel_evidencia_v1` | Evidência de nível/orçamento |
| Espera | `carta_orcamento_pendente_automatico_v1` | Aviso derivado, sem lista fixa |
| Decisão manual | `valor_do_dono`, `valor_do_dono_historico` | Valor protegido e histórico |
| Leitura física | `contrato_leitura_arquivo`, `contrato_leitura_campo` | Fonte, hash, tipo, endereço e destino |
| Endereços | `catalogo_endereco_leitura_extrator_v1` | Consulta ao contrato físico |
| Textos | `texto_do_jogo` | Chave oficial seção/id, rótulo por idioma |
| Catálogos | `atributo_jogo`, `habilidade_jogo`, `impeto_jogo`, `playstyle`, `estilo_ia`, `posicao_jogo`, `pe`, `corpo_ordem`, `tecnico_jogo` | Identidade e apresentação |
| Sistema | `funcao_sistema`, `funcao_alias`, `otimizador_molde` | Funções e molde versionado |
| Fila | `build_linha_card` | Uma linha de cálculo e vínculo ao lote |
| Resultado do motor | `build_otimizador` | Saída e provas do Otimizador |
| Publicação | `build_publicacao_linha_ativa_v1` | Composição ativa por linha |
| Exposição | `build_publicacao_exibivel_v3` | Publicações aptas à tela |

`build_linha_card` vincula o lote por `lote_producao_id`; não confundir com tabelas
de candidatas que usam `lote_id`. O contrato do lote inclui `regua_snapshot`; mudar
a régua viva não atualiza automaticamente um pacote já selado.

## Portas de consumo

Otimizador: `otimizador_carta_v3`, `otimizador_cartas_v3`, `otimizador_regua_v2`,
`otimizador_pool_habilidades_v3`. Bonificador: `bonificador_contexto_fila_v7` e
`gravar_build_bonificador_v6`. Publicação: `finalizar_publicar_linha_v1`.
Frontend: funções públicas dedicadas, incluindo `site_novo_ficha_v2` e
`site_novo_ranking_v1`. Examinar funções/RPCs além de tabelas/views numa auditoria.

## Regras de integridade

- Usar a chave completa, inclusive em relações compostas. Nomes não são chaves.
- Extrator preserva prova física; decisões manuais prevalecem no valor efetivo.
- Relacionamentos normalizados alimentam posições, habilidades, ímpetos e estilos.
- Filtrar `jogador_indisponivel=true` e `player_delete_list` antes de contar operação.
- Nível ausente/estimado sem prova não vira orçamento zero. Nível 1 comprovado é válido.
- `carta_orcamento_aguardando_v1` registra a decisão histórica das dez cartas;
  a fonte automática é quem governa o aviso atual.
- Publicação exige resultados compatíveis dos dois motores e confirmação persistida.
- Guardar credenciais administrativas fora do frontend e do GitHub.

[Mapa físico](MAPA-DO-CODIGO-DO-JOGO.md) ·
[Dicionário de textos](MANUAL-DOS-TEXTOS-DO-JOGO.md) ·
[Prioridade manual](EXTRATOR/PRIORIDADE-CORRECOES-MANUAIS.md) ·
[Integração](MANUAL-DE-INTERLIGACAO-DE-SISTEMAS.md).

[Endereços e identidades preservados](REFERENCIA-MAPEAMENTOS-FISICOS.md).
