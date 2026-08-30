-- Rollback do fluxo: repõe somente a política de metadados anterior, sem tocar dados do jogo.
begin;
create table if not exists clube_novo.contrato_leitura_politica_revisao (
 contrato_id text primary key references clube_novo.contrato_leitura_jogo(contrato_id) on delete restrict,
 revisao_humana_obrigatoria boolean not null default true,
 cobertura_aprovada boolean not null default false,
 carga_autorizada boolean not null default false,
 promocao_snapshot_autorizada boolean not null default false,
 decisao jsonb not null default '{}'::jsonb, proveniencia text not null, atualizado_em timestamptz not null default now(), check(jsonb_typeof(decisao)='object')
);
insert into clube_novo.contrato_leitura_politica_revisao (contrato_id,revisao_humana_obrigatoria,cobertura_aprovada,carga_autorizada,promocao_snapshot_autorizada,decisao,proveniencia,atualizado_em)
values ('clubef-dt870-2026-r1',true,false,false,false,jsonb_build_object('estado','aguarda_revisao','regra','diferenças são classificadas por chave e procedência; nenhuma promoção é automática'),'política inicial criada para separar classificação técnica da decisão humana','2026-08-30T00:15:27.219335+00:00')
on conflict (contrato_id) do nothing;
create or replace function clube_novo.obter_pedido_leitura_tipado_ativo()
returns jsonb language plpgsql security invoker set search_path = clube_novo, pg_temp as $$
declare pedido jsonb; cid text;
begin
 pedido := clube_novo.obter_pedido_leitura_tipado_sem_revisao_v1(); cid := pedido->>'contrato_id';
 if cid is null or cid='' then raise exception 'pedido tipado sem contrato_id'; end if;
 if not exists(select 1 from clube_novo.contrato_leitura_politica_revisao where contrato_id=cid) then raise exception 'pedido tipado sem política de revisão versionada'; end if;
 return pedido || jsonb_build_object('politica_revisao',(select jsonb_build_object('revisao_humana_obrigatoria',p.revisao_humana_obrigatoria,'cobertura_aprovada',p.cobertura_aprovada,'carga_autorizada',p.carga_autorizada,'promocao_snapshot_autorizada',p.promocao_snapshot_autorizada,'decisao',p.decisao,'proveniencia',p.proveniencia,'atualizado_em',p.atualizado_em) from clube_novo.contrato_leitura_politica_revisao p where p.contrato_id=cid));
end; $$;
commit;
