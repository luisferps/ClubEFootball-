set local lock_timeout = '5s';
set local statement_timeout = '30s';

alter table clube_novo.valor_do_dono enable row level security;
create table clube_novo.valor_do_dono_historico (
  id bigint generated always as identity primary key,
  operacao text not null,
  anterior jsonb,
  atual jsonb,
  autor text not null default session_user,
  registrado_em timestamptz not null default now()
);
alter table clube_novo.valor_do_dono_historico enable row level security;
revoke all on clube_novo.valor_do_dono_historico from public, anon, authenticated;

create or replace function clube_novo.tg_valor_do_dono_so_onde_o_jogo_nao_diz()
returns trigger language plpgsql set search_path=pg_catalog,clube_novo as $$
declare
  destino regclass;
  chaves text[];
  recebidas text[];
  linha jsonb;
  expressao text;
begin
  if new.destino_schema <> 'clube_novo' then raise exception 'Destino manual fora de clube_novo'; end if;
  destino := to_regclass(format('%I.%I',new.destino_schema,new.destino_tabela));
  if destino is null or not exists (
    select 1 from pg_trigger where tgrelid=destino and not tgisinternal
      and tgfoid='clube_novo.tg_valor_do_dono()'::regprocedure
  ) then raise exception 'Destino sem proteção manual instalada: %',new.destino_tabela; end if;
  select array_agg(a.attname::text order by a.attname)
    into chaves from pg_index i
    join pg_attribute a on a.attrelid=i.indrelid and a.attnum=any(i.indkey)
    where i.indrelid=destino and i.indisprimary;
  select array_agg(k order by k) into recebidas from jsonb_object_keys(new.chave) k;
  if chaves is null or recebidas is distinct from chaves then
    raise exception 'Informe exatamente a chave primária de %: %',new.destino_tabela,chaves;
  end if;
  if new.coluna=any(chaves) or not exists (
    select 1 from pg_attribute where attrelid=destino and attname=new.coluna
      and attnum>0 and not attisdropped and attgenerated='' and attidentity=''
  ) then raise exception 'Coluna manual inexistente, calculada ou parte da identidade: %',new.coluna; end if;
  select string_agg(format('t.%1$I = k.%1$I',k),' and ') into expressao from unnest(chaves) k;
  execute format('select to_jsonb(t) from %s t cross join jsonb_populate_record(null::%s,$1) k where %s for update of t',destino,destino,expressao)
    into strict linha using new.chave;
  -- Canonicaliza tipos de chave e de valor; null JSON continua sendo valor explícito.
  select jsonb_object_agg(k,linha->k) into new.chave from unnest(chaves) k;
  execute format('select to_jsonb(jsonb_populate_record(null::%s,$1))->$2',destino)
    into new.valor using jsonb_build_object(new.coluna,new.valor),new.coluna;
  new.posto_em := now();
  return new;
end;
$$;

create or replace function clube_novo.tg_valor_do_dono()
returns trigger language plpgsql set search_path=pg_catalog,clube_novo as $$
declare linha jsonb; protegido record;
begin
  linha := case when tg_op='DELETE' then to_jsonb(old) else to_jsonb(new) end;
  if tg_op='UPDATE' and exists (
    select 1 from clube_novo.valor_do_dono d
    where d.destino_schema=tg_table_schema and d.destino_tabela=tg_table_name
      and to_jsonb(old) @> d.chave and not linha @> d.chave
  ) then raise exception 'Identidade protegida por correção manual em %',tg_table_name; end if;
  for protegido in select d.coluna,d.valor from clube_novo.valor_do_dono d
    where d.destino_schema=tg_table_schema and d.destino_tabela=tg_table_name and linha @> d.chave
  loop
    if tg_op='DELETE' then raise exception 'Registro protegido por correção manual em %',tg_table_name; end if;
    linha := jsonb_set(linha,array[protegido.coluna],protegido.valor);
  end loop;
  if tg_op='DELETE' then return old; end if;
  return jsonb_populate_record(new,linha);
end;
$$;

-- Mesma proteção para todos os destinos do Extrator e catálogos já protegidos.
do $$
declare alvo record;
begin
  for alvo in
    select distinct destino_schema esquema,destino_tabela tabela
    from clube_novo.contrato_leitura_escritor_destino where ativo and destino_schema='clube_novo'
    union
    select n.nspname,c.relname from pg_trigger t join pg_class c on c.oid=t.tgrelid
      join pg_namespace n on n.oid=c.relnamespace
      where t.tgfoid='clube_novo.tg_valor_do_dono()'::regprocedure
  loop
    execute format('drop trigger if exists valor_do_dono_bi on %I.%I',alvo.esquema,alvo.tabela);
    execute format('create trigger zzzz_valor_do_dono before insert or update or delete on %I.%I for each row execute function clube_novo.tg_valor_do_dono()',alvo.esquema,alvo.tabela);
  end loop;
end;
$$;

create function clube_novo.tg_aplicar_e_auditar_valor_do_dono_v2()
returns trigger language plpgsql set search_path=pg_catalog,clube_novo as $$
declare destino regclass; expressao text; quantidade integer;
begin
  insert into clube_novo.valor_do_dono_historico(operacao,anterior,atual)
    values(tg_op,case when tg_op<>'INSERT' then to_jsonb(old) end,case when tg_op<>'DELETE' then to_jsonb(new) end);
  if tg_op='DELETE' then return old; end if;
  destino := to_regclass(format('%I.%I',new.destino_schema,new.destino_tabela));
  select string_agg(format('t.%1$I = k.%1$I',k),' and ') into expressao from jsonb_object_keys(new.chave) k;
  execute format('update %s t set %I=v.%I from jsonb_populate_record(null::%s,$1) v, jsonb_populate_record(null::%s,$2) k where %s',
    destino,new.coluna,new.coluna,destino,destino,expressao)
    using jsonb_build_object(new.coluna,new.valor),new.chave;
  get diagnostics quantidade=row_count;
  if quantidade<>1 then raise exception 'Correção manual não atualizou uma única linha'; end if;
  return new;
end;
$$;
create trigger aplicar_e_auditar_valor_do_dono after insert or update or delete
  on clube_novo.valor_do_dono for each row execute function clube_novo.tg_aplicar_e_auditar_valor_do_dono_v2();
revoke all on function clube_novo.tg_aplicar_e_auditar_valor_do_dono_v2() from public,anon,authenticated;
comment on table clube_novo.valor_do_dono is 'Correção manual prevalece sobre o Extrator em qualquer campo não gerado dos destinos protegidos. Cadastro aplica o valor e grava histórico atomicamente; remoção do registro retira a proteção sem restaurar valores antigos.';

-- Ensaio transacional: altera uma relação real e desfaz o ensaio por completo.
do $$
declare amostra record; observado integer;
begin
  select * into strict amostra from clube_novo.carta_atributo_jogo order by card_id,codigo_atributo limit 1;
  begin
    insert into clube_novo.valor_do_dono(destino_tabela,chave,coluna,valor,porque)
      values('carta_atributo_jogo',jsonb_build_object('card_id',amostra.card_id,'codigo_atributo',amostra.codigo_atributo),
        'valor',to_jsonb(amostra.valor),'Ensaio transacional, revertido na própria migração');
    update clube_novo.carta_atributo_jogo set valor=case when amostra.valor=99 then 98 else 99 end
      where card_id=amostra.card_id and codigo_atributo=amostra.codigo_atributo;
    select valor into observado from clube_novo.carta_atributo_jogo
      where card_id=amostra.card_id and codigo_atributo=amostra.codigo_atributo;
    if observado is distinct from amostra.valor then raise exception 'Teste falhou: extração sobrescreveu valor manual'; end if;
    begin
      delete from clube_novo.carta_atributo_jogo where card_id=amostra.card_id and codigo_atributo=amostra.codigo_atributo;
      raise exception using errcode='ZX002',message='Teste falhou: exclusão de valor protegido foi aceita';
    exception when raise_exception then
      if sqlerrm not like 'Registro protegido por correção manual%' then raise; end if;
    end;
    raise exception using errcode='ZX001',message='Ensaio aprovado; reverter dados de teste';
  exception when sqlstate 'ZX001' then null;
  end;
end;
$$;
