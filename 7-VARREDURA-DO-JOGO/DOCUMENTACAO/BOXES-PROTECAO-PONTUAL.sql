create trigger zzzz_valor_do_dono before insert or update or delete on clube_novo.box_contexto_contratacao_v1 for each row execute function clube_novo.tg_valor_do_dono();
create trigger zzzz_valor_do_dono before insert or update or delete on clube_novo.box_card_em_andamento_v1 for each row execute function clube_novo.tg_valor_do_dono();
