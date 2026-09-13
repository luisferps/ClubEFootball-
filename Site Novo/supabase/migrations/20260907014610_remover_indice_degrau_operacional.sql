-- O degrau agora pertence ao read model publicado; este indice temporario na
-- tabela operacional deixou de ter consumidor.
drop index if exists clube_novo.build_linha_card_publicacao_degrau_v1_idx;
