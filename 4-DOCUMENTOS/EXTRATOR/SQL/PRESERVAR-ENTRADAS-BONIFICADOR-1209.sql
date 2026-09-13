create table clube_novo.recalculo_1209_entrada_antes_v1 (
 card_id text primary key,
 carta jsonb not null,
 entrada_bonificador jsonb not null,
 carta_fingerprint text not null,
 preservado_em timestamptz not null default clock_timestamp()
);
alter table clube_novo.recalculo_1209_entrada_antes_v1 enable row level security;
revoke all on clube_novo.recalculo_1209_entrada_antes_v1 from public,anon,authenticated;
comment on table clube_novo.recalculo_1209_entrada_antes_v1 is 'Snapshot anterior a importacao fisica de 12/09/2026. Evidencia para comparar entradas e reaproveitar bonus conformes. Nao e fonte operacional.';
