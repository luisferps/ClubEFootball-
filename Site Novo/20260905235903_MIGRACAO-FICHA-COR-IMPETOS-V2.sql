-- Ficha V2: prepara o contrato de cor dos Impetos sem inventar o mapeamento.
-- A tabela nasce vazia. Somente evidencia confirmada do jogo deve popula-la.

do $preflight$
declare
  v_payload jsonb;
  v_stable boolean;
  v_security_definer boolean;
begin
  if to_regclass('clube_novo.tipo_impeto_cor_visual_jogo') is not null then
    raise exception 'tipo_impeto_cor_visual_jogo ja existe; aborte e audite o estado atual';
  end if;

  if to_regprocedure('public.site_novo_ficha_v2(text,bigint)') is not null then
    raise exception 'site_novo_ficha_v2 ja existe; aborte e audite o estado atual';
  end if;

  select p.provolatile = 's', p.prosecdef
    into v_stable, v_security_definer
  from pg_proc p
  where p.oid = 'public.site_novo_ficha_v1(text,bigint)'::regprocedure::oid;

  if not coalesce(v_stable, false) or not coalesce(v_security_definer, false) then
    raise exception 'Ficha V1 perdeu as garantias STABLE/SECURITY DEFINER';
  end if;

  select public.site_novo_ficha_v1('55068997045101',8475)
    into v_payload;

  if v_payload ->> 'contrato' <> 'site-novo-ficha-v1'
     or (v_payload ->> 'versao')::integer <> 1
     or jsonb_typeof(v_payload -> 'dados') <> 'object' then
    raise exception 'Ficha V1 nao preserva o envelope publico esperado pela V2';
  end if;
end
$preflight$;

create table clube_novo.tipo_impeto_cor_visual_jogo (
  tipo_raw smallint primary key
    references clube_novo.tipo_impeto_jogo(codigo_raw)
    on update cascade on delete cascade,
  cor_visual text not null
    check (cor_visual in ('azul','roxo','laranja','dourado')),
  valor_fisico text,
  fonte_origem text not null,
  endereco_origem text,
  evidencia text not null,
  estado_validacao text not null default 'confirmada'
    check (estado_validacao in ('candidata','confirmada')),
  atualizado_em timestamptz not null default now()
);

comment on table clube_novo.tipo_impeto_cor_visual_jogo is
  'Mapeamento tipo fisico de Impeto para cor de apresentacao. Deve permanecer vazio ate a correspondencia ser provada no jogo.';
comment on column clube_novo.tipo_impeto_cor_visual_jogo.cor_visual is
  'Cor do Impeto aplicado: azul, roxo, laranja ou dourado. Branco/verde pertencem aos tokens de fabricacao e cinza representa vaga vazia.';
comment on column clube_novo.tipo_impeto_cor_visual_jogo.valor_fisico is
  'Valor bruto/enum encontrado no jogo, preservado sem reinterpretacao.';
comment on column clube_novo.tipo_impeto_cor_visual_jogo.endereco_origem is
  'Endereco reproduzivel da evidencia, como arquivo/registro/bit/largura ou rotina/offset.';

revoke all on table clube_novo.tipo_impeto_cor_visual_jogo
  from public, anon, authenticated, service_role;

create function public.site_novo_ficha_v2(
  p_card_id text default null::text,
  p_linha_id bigint default null::bigint
)
returns jsonb
language sql
stable
security definer
set search_path=''
as $function$
with original as (
  select public.site_novo_ficha_v1(p_card_id, p_linha_id) as payload
), enriquecida as (
  select
    o.payload,
    case
      when jsonb_typeof(o.payload #> '{dados,build,impetos}') = 'array' then (
        select coalesce(
          jsonb_agg(
            elemento.item || jsonb_build_object(
              'cor_visual', cor.cor_visual,
              'cor_visual_estado', coalesce(cor.estado_validacao, 'aguardando_mapeamento')
            )
            order by elemento.ordem
          ),
          '[]'::jsonb
        )
        from jsonb_array_elements(o.payload #> '{dados,build,impetos}')
          with ordinality as elemento(item, ordem)
        left join clube_novo.impeto_jogo ij
          on ij.codigo_jogo = case
            when coalesce(elemento.item ->> 'codigo', '') ~ '^[0-9]+$'
              then (elemento.item ->> 'codigo')::integer
            else null
          end
        left join clube_novo.tipo_impeto_cor_visual_jogo cor
          on cor.tipo_raw = ij.tipo_condicao_raw
          and cor.estado_validacao = 'confirmada'
      )
      else null
    end as impetos
  from original o
)
select
  case
    when impetos is not null then jsonb_set(
      payload || jsonb_build_object(
        'contrato', 'site-novo-ficha-v2',
        'versao', 2
      ),
      '{dados,build,impetos}',
      impetos,
      true
    )
    else payload || jsonb_build_object(
      'contrato', 'site-novo-ficha-v2',
      'versao', 2
    )
  end
from enriquecida;
$function$;

comment on function public.site_novo_ficha_v2(text,bigint) is
  'Ficha publica V2: preserva a V1 e acrescenta a cor confirmada do tipo fisico de cada Impeto. Sem mapeamento, entrega null e a tela usa estado neutro.';

revoke all on function public.site_novo_ficha_v2(text,bigint)
  from public;
grant execute on function public.site_novo_ficha_v2(text,bigint)
  to anon, authenticated, service_role;
