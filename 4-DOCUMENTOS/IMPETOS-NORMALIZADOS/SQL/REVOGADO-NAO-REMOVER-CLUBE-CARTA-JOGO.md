# Autorização revogada — não executar

Em 27/08/2026 o usuário revogou expressamente a remoção de
`clube.carta_jogo`. O antigo script de `DROP TABLE` foi retirado da pasta SQL
para impedir execução acidental.

Estado obrigatório: preservar `clube.carta_jogo` e todas as demais tabelas do
schema `clube`. Esta frente de Técnicos + Otimizador não possui autorização para
alterar a tabela legada.

