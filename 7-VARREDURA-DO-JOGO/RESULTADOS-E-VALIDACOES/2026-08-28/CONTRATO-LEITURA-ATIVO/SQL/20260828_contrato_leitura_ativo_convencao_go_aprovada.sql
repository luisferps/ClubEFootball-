-- Direção explícita: as três associações GO são convenção aprovada e rastreável.
-- Elas são válidas operacionalmente, mas nunca devem aparecer como prova física individual.

alter table clube_novo.contrato_leitura_campo
  drop constraint contrato_leitura_campo_status_prova_check;
alter table clube_novo.contrato_leitura_campo
  add constraint contrato_leitura_campo_status_prova_check
  check (status_prova in ('comprovado','convencao_aprovada','provisorio','nao_usado'));

update clube_novo.contrato_leitura_campo f
set status_prova='convencao_aprovada',
    proveniencia_mapa_assunto=v.assunto,
    prova=v.prova
from (values
  ('impeto.efeito.bit.192','impeto - efeito - Talento de GO','PlayerBooster.bin bit192/w5; convenção de mapeamento aprovada pelo usuário; decisão registrada em clube_novo.mapa_do_jogo e MANUAL-DAS-TABELAS.md §8; não é prova física individual'),
  ('impeto.efeito.bit.197','impeto - efeito - Defesa de GO','PlayerBooster.bin bit197/w5; convenção de mapeamento aprovada pelo usuário; decisão registrada em clube_novo.mapa_do_jogo e MANUAL-DAS-TABELAS.md §8; não é prova física individual'),
  ('impeto.efeito.bit.256','impeto - efeito - Reflexos de GO','PlayerBooster.bin bit256/w5; convenção de mapeamento aprovada pelo usuário; decisão registrada em clube_novo.mapa_do_jogo e MANUAL-DAS-TABELAS.md §8; não é prova física individual')
) as v(chave_campo,assunto,prova)
where f.contrato_id='clubef-dt870-2026-r1' and f.chave_campo=v.chave_campo;

create or replace function clube_novo.validar_ativacao_contrato_leitura()
returns trigger
language plpgsql
security invoker
set search_path = clube_novo, pg_temp
as $$
begin
  if new.estado = 'ativo' then
    if not new.cobertura_total then
      raise exception 'contrato não pode ativar: cobertura integral não confirmada';
    end if;
    if exists (
      select 1 from clube_novo.contrato_leitura_campo f
      where f.contrato_id = new.contrato_id and f.ativo
        and f.status_prova not in ('comprovado','convencao_aprovada')
    ) then
      raise exception 'contrato não pode ativar: há campo ativo sem prova física nem convenção aprovada rastreável';
    end if;
    if exists (
      select 1 from clube_novo.contrato_leitura_cadeia c
      where c.contrato_id = new.contrato_id and c.requer_selo_contrato and c.estado <> 'conforme'
    ) then
      raise exception 'contrato não pode ativar: cadeia satélite ainda possui elo pendente';
    end if;
  end if;
  return new;
end;
$$;

create or replace function clube_novo.obter_pedido_leitura_contrato_ativo()
returns jsonb
language plpgsql
security invoker
set search_path = clube_novo, pg_temp
as $$
declare
  contract_row clube_novo.contrato_leitura_jogo%rowtype;
  result jsonb;
begin
  select * into contract_row
  from clube_novo.contrato_leitura_jogo
  where estado='ativo' and cobertura_total
  order by ativado_em desc nulls last, criado_em desc
  limit 1;
  if not found then raise exception 'contrato de leitura ativo e integral não encontrado'; end if;
  if exists (
    select 1 from clube_novo.contrato_leitura_campo f
    where f.contrato_id=contract_row.contrato_id and f.ativo
      and f.status_prova not in ('comprovado','convencao_aprovada')
  ) then raise exception 'contrato ativo inválido: campo sem prova física nem convenção aprovada'; end if;
  if exists (
    select 1 from clube_novo.contrato_leitura_cadeia c
    where c.contrato_id=contract_row.contrato_id and c.requer_selo_contrato and c.estado <> 'conforme'
  ) then raise exception 'contrato ativo inválido: cadeia satélite não conforme'; end if;
  select jsonb_build_object(
    'contrato_id',contract_row.contrato_id,'versao_jogo',contract_row.versao_jogo,
    'versao_contrato',contract_row.versao_contrato,
    'fingerprint_contrato_sha256',contract_row.fingerprint_contrato_sha256,
    'fingerprint_fontes_sha256',contract_row.fingerprint_fontes_sha256,
    'requisitos',coalesce((select jsonb_agg(jsonb_build_object('chave',r.chave_requisito,'expressao',r.expressao,'obrigatorio',r.obrigatorio) order by r.chave_requisito) from clube_novo.contrato_leitura_requisito r where r.contrato_id=contract_row.contrato_id),'[]'::jsonb),
    'arquivos',coalesce((select jsonb_agg(jsonb_build_object('arquivo_id',a.arquivo_id,'papel_fonte',a.papel_fonte,'arquivo',a.arquivo,'cpk',a.cpk,'versao_arquivo',a.versao_arquivo,'sha256_arquivo',a.sha256_arquivo,'tamanho_registro',a.tamanho_registro,'prefixo_bytes',a.prefixo_bytes,'decodificador',a.decodificador,'obrigatorio',a.obrigatorio) order by a.papel_fonte,a.arquivo) from clube_novo.contrato_leitura_arquivo a where a.contrato_id=contract_row.contrato_id),'[]'::jsonb),
    'campos',coalesce((select jsonb_agg(jsonb_build_object('chave_campo',f.chave_campo,'arquivo_id',f.arquivo_id,'entidade_destino',f.entidade_destino,'tipo_leitura',f.tipo_leitura,'byte_offset',f.byte_offset,'bit_inicio',f.bit_inicio,'largura_bits',f.largura_bits,'largura_bytes',f.largura_bytes,'endianness',f.endianness,'codificacao',f.codificacao,'transformacao',f.transformacao,'catalogo_schema',f.catalogo_schema,'catalogo_tabela',f.catalogo_tabela,'catalogo_chave',f.catalogo_chave,'requisito',f.requisito,'proveniencia',f.proveniencia_mapa_assunto,'prova',f.prova,'status_base',f.status_prova) order by f.chave_campo) from clube_novo.contrato_leitura_campo f where f.contrato_id=contract_row.contrato_id and f.ativo and f.status_prova in ('comprovado','convencao_aprovada')),'[]'::jsonb)
  ) into result;
  return result;
end;
$$;
