CREATE OR REPLACE FUNCTION clube_novo.tg_espelhar_posicao_playstyle_v1()
RETURNS trigger LANGUAGE plpgsql SET search_path='' AS $f$
begin
  if tg_table_name='carta_posicao_principal_jogo' then
    update clube_novo.carta_jogo c
      set posicao=p.codigo_en
      from clube_novo.posicao_jogo p
      where c.card_id=new.card_id and p.id=new.posicao_id
        and c.posicao is distinct from p.codigo_en;
  elsif new.slot_fisico=1 then
    update clube_novo.carta_jogo set slot_ofensivo_id=new.valor_raw
      where card_id=new.card_id and slot_ofensivo_id is distinct from new.valor_raw;
  elsif new.slot_fisico=2 then
    update clube_novo.carta_jogo set slot_defensivo_id=new.valor_raw
      where card_id=new.card_id and slot_defensivo_id is distinct from new.valor_raw;
  end if;
  return new;
end $f$;
REVOKE ALL ON FUNCTION clube_novo.tg_espelhar_posicao_playstyle_v1() FROM PUBLIC,anon,authenticated;
CREATE TRIGGER espelhar_posicao_playstyle AFTER INSERT OR UPDATE ON clube_novo.carta_posicao_principal_jogo
FOR EACH ROW EXECUTE FUNCTION clube_novo.tg_espelhar_posicao_playstyle_v1();
CREATE TRIGGER espelhar_posicao_playstyle AFTER INSERT OR UPDATE ON clube_novo.carta_playstyle_jogo
FOR EACH ROW EXECUTE FUNCTION clube_novo.tg_espelhar_posicao_playstyle_v1();
