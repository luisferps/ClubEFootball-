# Cartas excluídas e orçamento aguardando divulgação

Decisão de Luis em 13/09/2026: carta excluída não é defeito nem pendência.
Levantamentos operacionais devem usar `clube_novo.carta_operacional_v1`.
Não contabilizar `jogador_indisponivel=true` nem `tipo_carta_id=player_delete_list`.
Uma eventual volta depende de nova extração, não de recuperação automática.

Criadores integrais v5/v6 passaram a selecionar a fonte operacional.
Foram removidas desta fila 12.892 linhas não calculadas e suas candidatas,
correspondentes a 1.563 cartas excluídas. Registros históricos de outras
operações não são população para relatórios de pendências atuais.
A retirada foi transacional; tentativas anteriores com falha foram revertidas.
Índice da FK origem_linha_id do reaproveitamento adicionado para evitar
varreduras repetidas durante exclusões.

Conferência: fila 39da8ff4-7a4a-4ec7-8641-e81b5677ad4c mantém 193.543 linhas
para execução, 19.205 cartas, e 87 linhas de 10 cartas aguardando orçamento.
Zero cartas excluídas permanecem nela. Pacote selado da Máquina 2 preservado.

As dez cartas foram identificadas por Luis como campanha cujo orçamento
não foi divulgado. Não estimar valores, não interpretar levelCap=0 como
orçamento zero e não repetir a investigação nesta mesma atualização.
A tabela carta_orcamento_aguardando_v1 registra a decisão e seus IDs.
A Ficha pública mostra: "Orçamento ainda não divulgado. Aguardando uma
próxima atualização do eFootball." O aviso é devolvido pelo contrato público
e consumido pelo componente de mensagem já publicado, sem novo deploy.
Só deixa de aparecer quando existir evidência coerente de nível/orçamento.
Consulta de pendências: clube_novo.pendencia_nivel_operacional_v1.

Técnicos: régua selada comparada ao cadastro atual: 1.479 técnicos idênticos.
Mourinho 17608560707469 incluído, proficiência máxima 90, +1 Finalização e
+1 Contato Físico. Não alterar o Bonificador por causa de técnicos.

PDF de identificação: DEZ-CARTAS-PARA-CONFERENCIA.pdf.
