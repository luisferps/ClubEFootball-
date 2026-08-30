-- Aplicador interno do Extrator. Não altera tabelas de domínio nem legado.
-- A aplicação só pode ser chamada pelo processo desktop depois da aprovação
-- vinculada ao hash do pacote, contrato e fontes atualmente ativos.

create table if not exists clube_novo.aplicacao_pacote_revisao_extrator (
  aplicacao_id bigint generated always as identity primary key,
  idempotency_key text not null unique check (btrim(idempotency_key) <> ''),
  execucao_id bigint not null references clube_novo.execucao_leitura_contrato(execucao_id) on delete restrict,
  contrato_id text not null references clube_novo.contrato_leitura_jogo(contrato_id) on delete restrict,
  pacote_sha256 text not null check (pacote_sha256 ~ '^[0-9a-f]{64}$'),
  selo_contrato jsonb not null,
  manifesto_fontes jsonb not null,
  cobertura_familias jsonb not null,
  auditoria_familias jsonb not null,
  estado text not null check (estado in ('aplicado')),
  criado_em timestamptz not null default now(),
  aplicado_em timestamptz not null default now(),
  unique (contrato_id, pacote_sha256)
);

comment on table clube_novo.aplicacao_pacote_revisao_extrator is
  'Auditoria da aplicação transacional interna. A linha só persiste depois de leitura, aprovação vinculada, aplicação e readback na mesma transação.';
