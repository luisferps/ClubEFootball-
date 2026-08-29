-- Normalização parcial e fail-closed dos efeitos físicos de ímpeto.
-- EXECUTAR SOMENTE depois de PREFLIGHT-BANCO-READONLY.json registrar preflight_ok=true.
-- Escopo: clube_novo.impeto_jogo e clube_novo.impeto_atributo_jogo.
-- Não altera clube, cartas, Extrator, técnicos, textos ou Otimizador.

begin;
set local lock_timeout = '5s';
set local statement_timeout = '5min';
select pg_advisory_xact_lock(hashtextextended('clube_novo:impetos_normalizados:v1', 0));

do $$
declare
  v_impetos bigint;
  v_relacoes bigint;
  v_atributos bigint;
  v_orfaos bigint;
  v_legado_casado bigint;
begin
  select count(*) into v_impetos from clube_novo.impeto_jogo;
  select count(*) into v_relacoes from clube_novo.impeto_atributo_jogo;
  select count(*) into v_atributos from clube_novo.atributo_jogo;
  select count(*) into v_orfaos
  from clube_novo.impeto_atributo_jogo r
  left join clube_novo.impeto_jogo i on i.codigo_jogo = r.codigo_impeto
  left join clube_novo.atributo_jogo a on a.codigo = r.codigo_atributo
  where i.codigo_jogo is null or a.codigo is null;
  select count(*) into v_legado_casado
  from clube_novo.impeto_atributo_jogo r
  join clube_novo.atributo_jogo a on a.codigo = r.codigo_atributo
  join clube.impeto_efeito l
    on l.impeto_id = r.codigo_impeto
   and l.atributo_idx = a.idx_casa;

  if v_impetos <> 440 or v_relacoes <> 1542 or v_atributos <> 26 then
    raise exception 'Precondição divergente: impetos %, relações %, atributos %',
      v_impetos, v_relacoes, v_atributos;
  end if;
  if v_orfaos <> 0 or v_legado_casado <> 1542 then
    raise exception 'Integridade divergente: órfãos %, relações conciliadas %',
      v_orfaos, v_legado_casado;
  end if;
end $$;

alter table clube_novo.impeto_jogo
  add column if not exists condicao_estado text not null default 'nao_avaliada';

alter table clube_novo.impeto_atributo_jogo
  add column if not exists delta smallint,
  add column if not exists bit_delta smallint,
  add column if not exists largura_delta smallint,
  add column if not exists registro_origem integer,
  add column if not exists fonte_origem text,
  add column if not exists endereco_origem text,
  add column if not exists presente_dt200 boolean not null default false,
  add column if not exists presente_dt870_original boolean not null default false,
  add column if not exists presente_dt870_atualizacao boolean not null default false,
  add column if not exists confirmado boolean not null default false,
  add column if not exists falta_o_que text;

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conrelid = 'clube_novo.impeto_jogo'::regclass
      and conname = 'impeto_jogo_condicao_estado_ck'
  ) then
    alter table clube_novo.impeto_jogo
      add constraint impeto_jogo_condicao_estado_ck
      check (condicao_estado in ('ausente_comprovada','presente_sem_semantica','nao_avaliada'));
  end if;

  if not exists (
    select 1 from pg_constraint
    where conrelid = 'clube_novo.impeto_atributo_jogo'::regclass
      and conname = 'impeto_atributo_delta_ck'
  ) then
    alter table clube_novo.impeto_atributo_jogo
      add constraint impeto_atributo_delta_ck check (delta is null or delta between 1 and 31),
      add constraint impeto_atributo_bit_delta_ck check (bit_delta is null or bit_delta between 0 and 319),
      add constraint impeto_atributo_largura_delta_ck check (largura_delta is null or largura_delta between 1 and 32),
      add constraint impeto_atributo_confirmado_ck check (
        not confirmado or (
          delta is not null and bit_delta is not null and largura_delta is not null
          and registro_origem is not null and fonte_origem is not null
          and endereco_origem is not null
        )
      );
  end if;
end $$;

-- Os 131 códigos abaixo não possuem condição nos registros físicos atuais.
with incondicionais(codigo_jogo) as (
  select unnest(array[
    8,9,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,
    36,37,38,39,40,41,42,44,45,49,50,56,57,58,64,69,70,71,72,73,74,75,76,77,78,
    79,80,81,82,83,84,85,86,87,104,105,106,107,108,109,110,111,112,113,114,115,
    116,117,118,119,120,134,135,142,143,144,145,146,147,148,149,150,151,152,153,
    154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,173,175,184,
    185,186,187,188,189,190,191,192,193,194,195,199,200,201,202,205,206,207,250,
    263,265,267
  ]::integer[])
), codigos_com_receita as (
  select distinct codigo_impeto as codigo_jogo
  from clube_novo.impeto_atributo_jogo
)
update clube_novo.impeto_jogo i
set condicao_estado = case
  when x.codigo_jogo is not null then 'ausente_comprovada'
  when r.codigo_jogo is not null then 'presente_sem_semantica'
  else 'nao_avaliada'
end
from codigos_com_receita r
full join incondicionais x using (codigo_jogo)
where i.codigo_jogo = coalesce(r.codigo_jogo, x.codigo_jogo);

-- Mapeamento físico direto dos 23 atributos não ambíguos no registro de 40 bytes.
with atributo_bit(codigo_atributo, bit_delta) as (
  values
    ('PB:524:6',122),('PB:498:6',144),('PB:504:6',149),('PB:368:6',154),
    ('PB:408:6',160),('PB:416:6',165),('PB:512:6',170),('PB:518:6',175),
    ('PB:434:6',180),('PB:428:6',185),('PB:480:6',202),('PB:486:6',217),
    ('PB:422:6',224),('PB:448:6',229),('PB:454:6',234),('PB:492:6',239),
    ('PB:530:6',244),('PB:384:6',249),('PB:390:6',261),('PB:544:6',266),
    ('PB:550:6',271),('PB:396:6',276),('PB:402:6',281)
), incondicionais(codigo_jogo) as (
  select unnest(array[
    8,9,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,
    36,37,38,39,40,41,42,44,45,49,50,56,57,58,64,69,70,71,72,73,74,75,76,77,78,
    79,80,81,82,83,84,85,86,87,104,105,106,107,108,109,110,111,112,113,114,115,
    116,117,118,119,120,134,135,142,143,144,145,146,147,148,149,150,151,152,153,
    154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,173,175,184,
    185,186,187,188,189,190,191,192,193,194,195,199,200,201,202,205,206,207,250,
    263,265,267
  ]::integer[])
), fonte as (
  select r.codigo_impeto, r.codigo_atributo, b.bit_delta, l.delta,
         i.registro_dt870_atualizacao,
         coalesce(i.presente_dt200,false) as presente_dt200,
         coalesce(i.presente_dt870_steam,false) as presente_dt870_original,
         coalesce(i.presente_dt870_atualizacao,false) as presente_dt870_atualizacao
  from clube_novo.impeto_atributo_jogo r
  join incondicionais x on x.codigo_jogo = r.codigo_impeto
  join atributo_bit b on b.codigo_atributo = r.codigo_atributo
  join clube_novo.atributo_jogo a on a.codigo = r.codigo_atributo
  join clube.impeto_efeito l
    on l.impeto_id = r.codigo_impeto and l.atributo_idx = a.idx_casa
  join clube_novo.impeto_jogo i on i.codigo_jogo = r.codigo_impeto
  where i.presente_dt870_atualizacao is true
    and i.registro_dt870_atualizacao is not null
)
update clube_novo.impeto_atributo_jogo r
set delta = f.delta,
    bit_delta = f.bit_delta,
    largura_delta = 5,
    registro_origem = f.registro_dt870_atualizacao,
    fonte_origem = 'dt870_console_win-2026-08-27.cpk',
    arquivo_origem = 'PlayerBooster.bin',
    endereco_origem = format('registro %s de 40 bytes; bit %s; largura 5',
                              f.registro_dt870_atualizacao, f.bit_delta),
    presente_dt200 = f.presente_dt200,
    presente_dt870_original = f.presente_dt870_original,
    presente_dt870_atualizacao = f.presente_dt870_atualizacao,
    confirmado = true,
    falta_o_que = null
from fonte f
where r.codigo_impeto = f.codigo_impeto
  and r.codigo_atributo = f.codigo_atributo;

-- As demais relações permanecem deliberadamente sem delta aplicável.
update clube_novo.impeto_atributo_jogo r
set confirmado = false,
    falta_o_que = trim(both '; ' from concat_ws('; ',
      case when i.condicao_estado = 'presente_sem_semantica'
        then 'condição física presente; semântica e parâmetros ainda não comprovados' end,
      case when r.codigo_atributo in ('PB:472:6','PB:466:6','PB:460:6')
        then 'três campos físicos de goleiro são distintos, mas a permutação canônica ainda não foi provada' end
    ))
from clube_novo.impeto_jogo i
where i.codigo_jogo = r.codigo_impeto
  and r.confirmado is not true;

do $$
declare
  v_confirmadas bigint;
  v_bloqueadas bigint;
  v_invalidas bigint;
begin
  select count(*) filter (where confirmado),
         count(*) filter (where not confirmado),
         count(*) filter (where confirmado and (delta is null or falta_o_que is not null))
  into v_confirmadas, v_bloqueadas, v_invalidas
  from clube_novo.impeto_atributo_jogo;
  if v_confirmadas <> 488 or v_bloqueadas <> 1054 or v_invalidas <> 0 then
    raise exception 'Readback divergente: confirmadas %, bloqueadas %, inválidas %',
      v_confirmadas, v_bloqueadas, v_invalidas;
  end if;
end $$;

commit;

select confirmado, count(*) as relacoes, min(delta) as delta_min, max(delta) as delta_max
from clube_novo.impeto_atributo_jogo
group by confirmado
order by confirmado desc;

