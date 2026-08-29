-- Fase 1: contrato de leitura ativo e versionado. Sem carga de dados do jogo.
-- Escopo: somente schema clube_novo; não toca legado, motor, fórmulas ou tabelas de domínio.

create table if not exists clube_novo.contrato_leitura_jogo (
  contrato_id text primary key check (contrato_id ~ '^[a-z0-9][a-z0-9._-]{2,127}$'),
  versao_jogo text not null check (btrim(versao_jogo) <> ''),
  versao_contrato text not null check (btrim(versao_contrato) <> ''),
  fingerprint_contrato_sha256 text not null check (fingerprint_contrato_sha256 ~ '^[0-9a-f]{64}$'),
  fingerprint_fontes_sha256 text not null check (fingerprint_fontes_sha256 ~ '^[0-9a-f]{64}$'),
  estado text not null check (estado in ('rascunho', 'validado', 'ativo', 'revogado')),
  politica_fonte jsonb not null default '{}'::jsonb,
  cobertura_total boolean not null default false,
  criado_em timestamptz not null default now(),
  validado_em timestamptz,
  ativado_em timestamptz,
  observacao text,
  check ((estado <> 'ativo') or (cobertura_total and validado_em is not null and ativado_em is not null))
);

create table if not exists clube_novo.contrato_leitura_arquivo (
  arquivo_id bigint generated always as identity primary key,
  contrato_id text not null references clube_novo.contrato_leitura_jogo(contrato_id) on delete restrict,
  papel_fonte text not null check (btrim(papel_fonte) <> ''),
  arquivo text not null check (btrim(arquivo) <> ''),
  cpk text,
  versao_arquivo text not null check (btrim(versao_arquivo) <> ''),
  sha256_arquivo text not null check (sha256_arquivo ~ '^[0-9a-f]{64}$'),
  tamanho_registro integer check (tamanho_registro is null or tamanho_registro > 0),
  prefixo_bytes integer not null default 0 check (prefixo_bytes >= 0),
  decodificador text not null check (btrim(decodificador) <> ''),
  obrigatorio boolean not null default true,
  proveniencia text not null check (btrim(proveniencia) <> ''),
  unique (contrato_id, papel_fonte, arquivo),
  unique (arquivo_id, contrato_id)
);

create table if not exists clube_novo.contrato_leitura_campo (
  campo_id bigint generated always as identity primary key,
  contrato_id text not null references clube_novo.contrato_leitura_jogo(contrato_id) on delete restrict,
  arquivo_id bigint not null,
  chave_campo text not null check (chave_campo ~ '^[a-z0-9][a-z0-9._-]{2,191}$'),
  entidade_destino text not null check (btrim(entidade_destino) <> ''),
  tipo_leitura text not null check (tipo_leitura in ('bitfield_le','byte_le','byte_be','fixed_utf8_nul','id_mask','membership','all_str_parser','computed')),
  byte_offset integer check (byte_offset is null or byte_offset >= 0),
  bit_inicio integer check (bit_inicio is null or bit_inicio >= 0),
  largura_bits smallint check (largura_bits is null or largura_bits > 0),
  largura_bytes integer check (largura_bytes is null or largura_bytes > 0),
  endianness text check (endianness is null or endianness in ('little', 'big', 'not_applicable')),
  codificacao text,
  transformacao jsonb not null default '{}'::jsonb,
  catalogo_schema text,
  catalogo_tabela text,
  catalogo_chave text,
  requisito jsonb not null default '{}'::jsonb,
  proveniencia_mapa_assunto text not null check (btrim(proveniencia_mapa_assunto) <> ''),
  prova text not null check (btrim(prova) <> ''),
  status_prova text not null check (status_prova in ('comprovado', 'provisorio', 'nao_usado')),
  ativo boolean not null default true,
  foreign key (arquivo_id, contrato_id) references clube_novo.contrato_leitura_arquivo(arquivo_id, contrato_id) on delete restrict,
  unique (contrato_id, chave_campo),
  check (
    (tipo_leitura = 'bitfield_le' and bit_inicio is not null and largura_bits is not null and byte_offset is null)
    or (tipo_leitura in ('byte_le', 'byte_be', 'fixed_utf8_nul') and byte_offset is not null and largura_bytes is not null)
    or (tipo_leitura in ('id_mask', 'membership', 'all_str_parser', 'computed'))
  )
);

create table if not exists clube_novo.contrato_leitura_requisito (
  requisito_id bigint generated always as identity primary key,
  contrato_id text not null references clube_novo.contrato_leitura_jogo(contrato_id) on delete restrict,
  chave_requisito text not null check (chave_requisito ~ '^[a-z0-9][a-z0-9._-]{2,191}$'),
  expressao jsonb not null,
  obrigatorio boolean not null default true,
  proveniencia text not null check (btrim(proveniencia) <> ''),
  unique (contrato_id, chave_requisito)
);

create table if not exists clube_novo.execucao_leitura_contrato (
  execucao_id bigint generated always as identity primary key,
  idempotency_key text not null unique check (btrim(idempotency_key) <> ''),
  contrato_id text not null references clube_novo.contrato_leitura_jogo(contrato_id) on delete restrict,
  versao_jogo text not null,
  fingerprint_contrato_sha256 text not null check (fingerprint_contrato_sha256 ~ '^[0-9a-f]{64}$'),
  fingerprint_fontes_sha256 text not null check (fingerprint_fontes_sha256 ~ '^[0-9a-f]{64}$'),
  fingerprint_saida_sha256 text not null check (fingerprint_saida_sha256 ~ '^[0-9a-f]{64}$'),
  manifesto_fontes jsonb not null,
  estado text not null check (estado in ('estagiado', 'aceito', 'recusado')),
  motivo_recusa text,
  criado_em timestamptz not null default now(),
  aceito_em timestamptz,
  check ((estado = 'aceito') = (aceito_em is not null))
);

create or replace function clube_novo.estagiar_execucao_leitura_contrato(
  p_idempotency_key text,
  p_contrato_id text,
  p_versao_jogo text,
  p_fingerprint_contrato_sha256 text,
  p_fingerprint_fontes_sha256 text,
  p_fingerprint_saida_sha256 text,
  p_manifesto_fontes jsonb
) returns clube_novo.execucao_leitura_contrato
language plpgsql
security invoker
set search_path = clube_novo, pg_temp
as $$
declare
  v_contrato clube_novo.contrato_leitura_jogo;
  v_existente clube_novo.execucao_leitura_contrato;
  v_resultado clube_novo.execucao_leitura_contrato;
begin
  select * into v_existente from clube_novo.execucao_leitura_contrato where idempotency_key = p_idempotency_key;
  if found then
    if v_existente.contrato_id = p_contrato_id
       and v_existente.versao_jogo = p_versao_jogo
       and v_existente.fingerprint_contrato_sha256 = p_fingerprint_contrato_sha256
       and v_existente.fingerprint_fontes_sha256 = p_fingerprint_fontes_sha256
       and v_existente.fingerprint_saida_sha256 = p_fingerprint_saida_sha256
       and v_existente.manifesto_fontes = p_manifesto_fontes then
      return v_existente;
    end if;
    raise exception 'idempotency_key já usado com conteúdo divergente';
  end if;

  select * into v_contrato from clube_novo.contrato_leitura_jogo where contrato_id = p_contrato_id;
  if not found then raise exception 'contrato inexistente'; end if;
  if v_contrato.estado <> 'ativo' or not v_contrato.cobertura_total then
    raise exception 'contrato não está ativo ou não tem cobertura integral';
  end if;
  if v_contrato.versao_jogo <> p_versao_jogo
     or v_contrato.fingerprint_contrato_sha256 <> p_fingerprint_contrato_sha256
     or v_contrato.fingerprint_fontes_sha256 <> p_fingerprint_fontes_sha256 then
    raise exception 'versão ou fingerprint divergente: carga recusada';
  end if;

  insert into clube_novo.execucao_leitura_contrato
    (idempotency_key, contrato_id, versao_jogo, fingerprint_contrato_sha256, fingerprint_fontes_sha256, fingerprint_saida_sha256, manifesto_fontes, estado, aceito_em)
  values
    (p_idempotency_key, p_contrato_id, p_versao_jogo, p_fingerprint_contrato_sha256, p_fingerprint_fontes_sha256, p_fingerprint_saida_sha256, p_manifesto_fontes, 'aceito', now())
  returning * into v_resultado;
  return v_resultado;
end;
$$;

comment on table clube_novo.contrato_leitura_jogo is 'Contrato ativo, versionado e fingerprintado. Só ativo com cobertura total.';
comment on table clube_novo.contrato_leitura_campo is 'Campo físico tipado; nenhuma constante operacional é aceita fora desta relação quando o contrato estiver ativo.';
comment on function clube_novo.estagiar_execucao_leitura_contrato is 'Gate transacional idempotente. Recusa versão/fingerprint/contrato não ativo antes de qualquer carga de domínio.';
