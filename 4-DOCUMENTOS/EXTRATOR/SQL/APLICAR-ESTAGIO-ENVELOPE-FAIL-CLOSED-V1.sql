begin;
create table if not exists clube_novo.contrato_leitura_envelope_mapeamento (
  mapeamento_id bigint generated always as identity primary key,
  destino_id bigint not null references clube_novo.contrato_leitura_escritor_destino(destino_id) on delete restrict,
  coluna_destino text not null,
  campo_id bigint references clube_novo.contrato_leitura_campo(campo_id) on delete restrict,
  artefato_fisico text,
  coluna_fisica text,
  regra_decomposicao jsonb not null default '{}'::jsonb,
  normalizador_id text,
  versao_normalizador text,
  proveniencia text not null,
  status text not null default 'bloqueado_sem_prova' check (status in ('comprovado','bloqueado_sem_prova')),
  unique(destino_id,coluna_destino),
  check ((status='comprovado') = (campo_id is not null and artefato_fisico is not null and coluna_fisica is not null))
);
create table if not exists clube_novo.envelope_revisao_extrator_estagio (
  estagio_id bigint generated always as identity primary key,
  contrato_id text not null references clube_novo.contrato_leitura_jogo(contrato_id),
  pacote_sha256 text not null check (pacote_sha256 ~ '^[0-9a-f]{64}$'),
  destino_id bigint not null references clube_novo.contrato_leitura_escritor_destino(destino_id),
  identidade jsonb not null, valores jsonb not null, procedencia jsonb not null,
  selo jsonb not null, estado text not null default 'revisao' check(estado='revisao'),
  unique(pacote_sha256,destino_id,identidade)
);
commit;
