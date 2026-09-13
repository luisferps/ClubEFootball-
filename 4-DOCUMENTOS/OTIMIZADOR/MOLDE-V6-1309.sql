-- Preparado; aplicar somente depois da incorporação dos novos dados.
begin;
set local lock_timeout='5s';
do $pre$
begin
 if (select max(versao) from clube_novo.otimizador_molde)<>5
 or (select count(*) from clube_novo.otimizador_molde where versao=5)<>494
 then raise exception 'Molde base mudou: reconferir antes de implantar'; end if;
end $pre$;
insert into clube_novo.otimizador_molde(versao,funcao_id,codigo_atributo,alvo,peso)
select 6,funcao_id,codigo_atributo,alvo,peso from clube_novo.otimizador_molde where versao=5;
update clube_novo.otimizador_molde set alvo=89,peso=7 where versao=6 and funcao_id=8 and codigo_atributo='PB:530:6';
update clube_novo.otimizador_molde set peso=3 where versao=6 and funcao_id=8 and codigo_atributo='PB:486:6';
update clube_novo.otimizador_molde set alvo=85,peso=7 where versao=6 and funcao_id=10 and codigo_atributo='PB:434:6';
update clube_novo.otimizador_molde set alvo=85,peso=3 where versao=6 and funcao_id=10 and codigo_atributo='PB:486:6';
update clube_novo.otimizador_molde set peso=3 where versao=6 and funcao_id=10 and codigo_atributo='PB:428:6';
do $consumers$
declare d text; anchor text; target regprocedure;
begin
 for target,anchor in select * from (values
 ('public.complemento_contexto_v14()'::regprocedure,'where m.versao=5'),
 ('build_editor.avaliar_v1(jsonb)'::regprocedure,'and mo.versao=5')) x loop
 d:=pg_get_functiondef(target);
 if (length(d)-length(replace(d,anchor,'')))/length(anchor)<>1
 then raise exception 'Âncora não é única: %',target; end if;
 execute replace(d,anchor,replace(anchor,'=5','=(select max(versao) from clube_novo.otimizador_molde)'));
 end loop;
end $consumers$;
update clube_novo.regua_vigente_v1
set contrato_fingerprint=clube_novo.otimizador_producao_contrato_fingerprint_v3(public.otimizador_regua_v2()),
vigente_desde=clock_timestamp(),motivo='Molde v6 e técnicos conferidos; recálculo integral';
do $checks$
declare r jsonb;
begin
 if (select count(*) from clube_novo.otimizador_molde where versao=6)<>494
 then raise exception 'Molde v6 incompleto'; end if;
 if (select count(*) from clube_novo.otimizador_molde a join clube_novo.otimizador_molde b using(funcao_id,codigo_atributo)
 where a.versao=5 and b.versao=6 and (a.alvo,a.peso) is distinct from(b.alvo,b.peso))<>5
 then raise exception 'Esperadas exatamente cinco alterações'; end if;
 if exists(with ranked as(
 select m.*,row_number() over(partition by m.funcao_id order by ceil(m.alvo) desc,a.indice_otimizador) pos
 from clube_novo.otimizador_molde m join clube_novo.atributo_ordem_otimizador a using(codigo_atributo)
 where m.versao=6 and m.funcao_id in(8,10) and ceil(m.alvo)>=80)
 select 1 from ranked where peso<>case when pos<=5 then 12 when pos<=9 then 7 when pos<=13 then 3 else 1 end)
 then raise exception 'Pesos divergentes da regra 5/4/4/resto'; end if;
 r:=public.otimizador_regua_v2();
 if (r->>'versao_molde')::integer is distinct from 6 or (r#>>'{gate,pode_rodar}')::boolean is distinct from true
 then raise exception 'Régua v6 recusada: %',r->'gate'; end if;
 if (select count(*) from clube_novo.regua_vigente_v1 where contrato_fingerprint=clube_novo.otimizador_producao_contrato_fingerprint_v3(r))<>1
 then raise exception 'Selo divergente'; end if;
end $checks$;
commit;
