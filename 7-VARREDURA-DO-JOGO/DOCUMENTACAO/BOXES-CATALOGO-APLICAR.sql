create or replace function clube_novo.aplicar_catalogo_boxes_jogo_v1(p_captura uuid) returns jsonb language plpgsql security definer set search_path='' as $f$
declare b record; bid bigint; n int:=0; criadas int:=0; r jsonb;
begin
 perform pg_advisory_xact_lock(hashtextextended('clube_novo.boxes.jogo',0));
 if not exists(select 1 from clube_novo.box_catalogo_jogo_atual_v1 where captura_id=p_captura) then raise exception 'Catalogo ausente ou ultrapassado'; end if;
 lock table clube_novo.box_contexto_contratacao_v1 in share row exclusive mode;
 for b in select * from clube_novo.box_catalogo_jogo_atual_v1 loop
  bid:=null;
  select box_id into bid from clube_novo.box_contexto_contratacao_v1
  where agente_jogo_id=b.agente_jogo_id
  order by box_id limit 1;
  if bid is null then
   select box_id into bid from clube_novo.box_contexto_contratacao_v1
   where lower(btrim(box_nome))=lower(btrim(b.titulo))
   order by (estado_box='em_andamento') desc,box_id limit 1;
  end if;
  if bid is null then
   select coalesce(max(box_id),0)+1 into bid from clube_novo.box_contexto_contratacao_v1;
   insert into clube_novo.box_contexto_contratacao_v1
   (box_id,box_nome,estado_box,status_origem,origem_fingerprint,capturado_em,oferta_fonte,agente_jogo_id)
   values(bid,b.titulo,'finalizada','anterior',encode(extensions.digest(p_captura::text,'sha256'),'hex'),b.capturado_em,b.fonte,b.agente_jogo_id);
   criadas:=criadas+1;
  end if;
  update clube_novo.box_contexto_contratacao_v1 set
   agente_jogo_id=b.agente_jogo_id,oferta_fonte=b.fonte,capturado_em=b.capturado_em,
   data_oferta=(b.inicio_oferta at time zone 'UTC')::date,fim_oferta=b.fim_oferta,
   estado_box=case when b.situacao='disponivel_na_captura' then 'em_andamento' else 'finalizada' end,
   status_origem=case when b.situacao='disponivel_na_captura' then 'atual' else 'anterior' end,
   origem_fingerprint=encode(extensions.digest(p_captura::text,'sha256'),'hex')
  where box_id=bid;
  n:=n+1;
 end loop;
 update clube_novo.box_contexto_contratacao_v1 x set estado_box='finalizada',status_origem='anterior'
 where x.estado_box='em_andamento'
 and not exists(select 1 from clube_novo.box_catalogo_jogo_atual_v1 c where c.agente_jogo_id=x.agente_jogo_id);
 r:=jsonb_build_object('contextos_atualizados',n,'contextos_novos',criadas);
 update clube_novo.box_captura_jogo_v1 set resultado=resultado||r where captura_id=p_captura;
 return r;
end $f$;
revoke all on function clube_novo.aplicar_catalogo_boxes_jogo_v1(uuid) from public,anon,authenticated;
grant execute on function clube_novo.aplicar_catalogo_boxes_jogo_v1(uuid) to service_role;
