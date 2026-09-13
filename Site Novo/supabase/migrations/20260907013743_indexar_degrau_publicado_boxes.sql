-- Evita buscar as duas colunas de degrau na linha completa (tabela larga)
-- para cada uma das dezenas de milhares de publicacoes exibidas nas boxes.
create index if not exists build_linha_card_publicacao_degrau_v1_idx
on clube_novo.build_linha_card (id)
include (impeto_condicional_codigo,impeto_condicional_nivel);
