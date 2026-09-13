set local lock_timeout='5s'; set local statement_timeout='180s';

create table clube_novo.otimizador_politica_habilidades (
 versao text primary key, motor_versao text not null, formula_fingerprint text not null,
 regras jsonb not null, criada_em timestamptz not null default now());
alter table clube_novo.otimizador_politica_habilidades enable row level security;
revoke all on clube_novo.otimizador_politica_habilidades from public,anon,authenticated;
grant select on clube_novo.otimizador_politica_habilidades to service_role;
create table clube_novo.otimizador_historico_habilidades (
 versao text not null references clube_novo.otimizador_politica_habilidades(versao),
 tipo text not null, identidade text not null, antes jsonb not null,
 primary key(versao,tipo,identidade));
alter table clube_novo.otimizador_historico_habilidades enable row level security;
revoke all on clube_novo.otimizador_historico_habilidades from public,anon,authenticated;
grant select on clube_novo.otimizador_historico_habilidades to service_role;

insert into clube_novo.otimizador_politica_habilidades values('habilidades-funcao-20260909-v1','otimizador-fila-producao-v3-local-20260909-habilidades-v12','a1cc830af3366e2d0c9ac12138d892058b3e57ed216e43d68242d105b33cb9d2','{"versao":"habilidades-funcao-20260909-v1","motor_versao":"otimizador-fila-producao-v3-local-20260909-habilidades-v12","formula_fingerprint":"a1cc830af3366e2d0c9ac12138d892058b3e57ed216e43d68242d105b33cb9d2","permitidas":{"34":[6,7,12,13,14,15],"46":[6,7,12,13,14,15],"19":[1,2,3],"37":[1,2,3,8,9,10,11,12,13,14,15],"15":[1,2,3,6,16,17,18,19]},"exigidos":{"0":[4,5,6,17,18,19],"1":[4,5,6,17,18,19],"2":[4,5,6,17,18,19],"3":[4,5,6,17,18,19],"4":[4,5,6,12,13,17,18,19],"5":[4,5,6,17,18,19],"6":[4,5,6,17,18,19],"7":[4,5,6,17,18,19],"10":[4,5,6,17,18,19],"15":[4,5,7,8,9,10,11,12,13,14,15],"19":[4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19],"27":[4,5,17],"34":[1,2,3,4,5,8,9,10,11,16,17,18,19],"37":[4,5,6,7,16,17,18,19],"38":[4,5,17,18,19],"46":[1,2,3,4,5,8,9,10,11,16,17,18,19],"55":[1,2,3,4,5,9,14,15],"56":[1,2,4,5,6,7,10,11,16,17,18,19]},"slots_minimos":0,"slots_maximos":5,"preencher_sem_ganho":false,"nativas_preservadas":true,"editor_livre":true,"normalizacao_alterada":false,"fila_reordenada":false,"dribles":[0,1,2,3,4,5,6,7,10],"desbloqueios_aprovados":[[0,16],[2,16],[4,16]],"bloqueios":[{"skill_id":34,"funcao_id":1},{"skill_id":44,"funcao_id":1},{"skill_id":45,"funcao_id":1},{"skill_id":46,"funcao_id":1},{"skill_id":47,"funcao_id":1},{"skill_id":49,"funcao_id":1},{"skill_id":55,"funcao_id":1},{"skill_id":56,"funcao_id":1},{"skill_id":57,"funcao_id":1},{"skill_id":58,"funcao_id":1},{"skill_id":60,"funcao_id":1},{"skill_id":64,"funcao_id":1},{"skill_id":1716,"funcao_id":1},{"skill_id":2101,"funcao_id":1},{"skill_id":34,"funcao_id":2},{"skill_id":44,"funcao_id":2},{"skill_id":45,"funcao_id":2},{"skill_id":46,"funcao_id":2},{"skill_id":47,"funcao_id":2},{"skill_id":49,"funcao_id":2},{"skill_id":55,"funcao_id":2},{"skill_id":56,"funcao_id":2},{"skill_id":57,"funcao_id":2},{"skill_id":58,"funcao_id":2},{"skill_id":60,"funcao_id":2},{"skill_id":64,"funcao_id":2},{"skill_id":1716,"funcao_id":2},{"skill_id":2101,"funcao_id":2},{"skill_id":34,"funcao_id":3},{"skill_id":44,"funcao_id":3},{"skill_id":45,"funcao_id":3},{"skill_id":46,"funcao_id":3},{"skill_id":47,"funcao_id":3},{"skill_id":49,"funcao_id":3},{"skill_id":55,"funcao_id":3},{"skill_id":57,"funcao_id":3},{"skill_id":58,"funcao_id":3},{"skill_id":60,"funcao_id":3},{"skill_id":64,"funcao_id":3},{"skill_id":1716,"funcao_id":3},{"skill_id":2101,"funcao_id":3},{"skill_id":0,"funcao_id":4},{"skill_id":1,"funcao_id":4},{"skill_id":2,"funcao_id":4},{"skill_id":3,"funcao_id":4},{"skill_id":4,"funcao_id":4},{"skill_id":5,"funcao_id":4},{"skill_id":6,"funcao_id":4},{"skill_id":7,"funcao_id":4},{"skill_id":10,"funcao_id":4},{"skill_id":15,"funcao_id":4},{"skill_id":17,"funcao_id":4},{"skill_id":19,"funcao_id":4},{"skill_id":20,"funcao_id":4},{"skill_id":21,"funcao_id":4},{"skill_id":22,"funcao_id":4},{"skill_id":23,"funcao_id":4},{"skill_id":26,"funcao_id":4},{"skill_id":27,"funcao_id":4},{"skill_id":28,"funcao_id":4},{"skill_id":34,"funcao_id":4},{"skill_id":36,"funcao_id":4},{"skill_id":37,"funcao_id":4},{"skill_id":38,"funcao_id":4},{"skill_id":46,"funcao_id":4},{"skill_id":48,"funcao_id":4},{"skill_id":54,"funcao_id":4},{"skill_id":55,"funcao_id":4},{"skill_id":56,"funcao_id":4},{"skill_id":57,"funcao_id":4},{"skill_id":58,"funcao_id":4},{"skill_id":59,"funcao_id":4},{"skill_id":60,"funcao_id":4},{"skill_id":0,"funcao_id":5},{"skill_id":1,"funcao_id":5},{"skill_id":2,"funcao_id":5},{"skill_id":3,"funcao_id":5},{"skill_id":4,"funcao_id":5},{"skill_id":5,"funcao_id":5},{"skill_id":6,"funcao_id":5},{"skill_id":7,"funcao_id":5},{"skill_id":10,"funcao_id":5},{"skill_id":15,"funcao_id":5},{"skill_id":17,"funcao_id":5},{"skill_id":19,"funcao_id":5},{"skill_id":20,"funcao_id":5},{"skill_id":21,"funcao_id":5},{"skill_id":22,"funcao_id":5},{"skill_id":23,"funcao_id":5},{"skill_id":26,"funcao_id":5},{"skill_id":27,"funcao_id":5},{"skill_id":28,"funcao_id":5},{"skill_id":34,"funcao_id":5},{"skill_id":36,"funcao_id":5},{"skill_id":37,"funcao_id":5},{"skill_id":38,"funcao_id":5},{"skill_id":46,"funcao_id":5},{"skill_id":48,"funcao_id":5},{"skill_id":54,"funcao_id":5},{"skill_id":55,"funcao_id":5},{"skill_id":56,"funcao_id":5},{"skill_id":57,"funcao_id":5},{"skill_id":58,"funcao_id":5},{"skill_id":59,"funcao_id":5},{"skill_id":60,"funcao_id":5},{"skill_id":0,"funcao_id":6},{"skill_id":1,"funcao_id":6},{"skill_id":2,"funcao_id":6},{"skill_id":3,"funcao_id":6},{"skill_id":4,"funcao_id":6},{"skill_id":5,"funcao_id":6},{"skill_id":6,"funcao_id":6},{"skill_id":7,"funcao_id":6},{"skill_id":10,"funcao_id":6},{"skill_id":19,"funcao_id":6},{"skill_id":20,"funcao_id":6},{"skill_id":37,"funcao_id":6},{"skill_id":44,"funcao_id":6},{"skill_id":45,"funcao_id":6},{"skill_id":47,"funcao_id":6},{"skill_id":49,"funcao_id":6},{"skill_id":56,"funcao_id":6},{"skill_id":1716,"funcao_id":6},{"skill_id":2101,"funcao_id":6},{"skill_id":15,"funcao_id":7},{"skill_id":19,"funcao_id":7},{"skill_id":20,"funcao_id":7},{"skill_id":37,"funcao_id":7},{"skill_id":44,"funcao_id":7},{"skill_id":45,"funcao_id":7},{"skill_id":47,"funcao_id":7},{"skill_id":49,"funcao_id":7},{"skill_id":56,"funcao_id":7},{"skill_id":1716,"funcao_id":7},{"skill_id":2101,"funcao_id":7},{"skill_id":15,"funcao_id":8},{"skill_id":19,"funcao_id":8},{"skill_id":34,"funcao_id":8},{"skill_id":44,"funcao_id":8},{"skill_id":45,"funcao_id":8},{"skill_id":46,"funcao_id":8},{"skill_id":47,"funcao_id":8},{"skill_id":49,"funcao_id":8},{"skill_id":60,"funcao_id":8},{"skill_id":64,"funcao_id":8},{"skill_id":1716,"funcao_id":8},{"skill_id":2101,"funcao_id":8},{"skill_id":15,"funcao_id":9},{"skill_id":19,"funcao_id":9},{"skill_id":34,"funcao_id":9},{"skill_id":44,"funcao_id":9},{"skill_id":45,"funcao_id":9},{"skill_id":46,"funcao_id":9},{"skill_id":47,"funcao_id":9},{"skill_id":49,"funcao_id":9},{"skill_id":55,"funcao_id":9},{"skill_id":57,"funcao_id":9},{"skill_id":58,"funcao_id":9},{"skill_id":60,"funcao_id":9},{"skill_id":64,"funcao_id":9},{"skill_id":1716,"funcao_id":9},{"skill_id":2101,"funcao_id":9},{"skill_id":15,"funcao_id":10},{"skill_id":19,"funcao_id":10},{"skill_id":34,"funcao_id":10},{"skill_id":44,"funcao_id":10},{"skill_id":45,"funcao_id":10},{"skill_id":46,"funcao_id":10},{"skill_id":47,"funcao_id":10},{"skill_id":49,"funcao_id":10},{"skill_id":56,"funcao_id":10},{"skill_id":1716,"funcao_id":10},{"skill_id":2101,"funcao_id":10},{"skill_id":15,"funcao_id":11},{"skill_id":19,"funcao_id":11},{"skill_id":34,"funcao_id":11},{"skill_id":44,"funcao_id":11},{"skill_id":45,"funcao_id":11},{"skill_id":46,"funcao_id":11},{"skill_id":47,"funcao_id":11},{"skill_id":49,"funcao_id":11},{"skill_id":56,"funcao_id":11},{"skill_id":1716,"funcao_id":11},{"skill_id":2101,"funcao_id":11},{"skill_id":4,"funcao_id":12},{"skill_id":15,"funcao_id":12},{"skill_id":19,"funcao_id":12},{"skill_id":44,"funcao_id":12},{"skill_id":45,"funcao_id":12},{"skill_id":47,"funcao_id":12},{"skill_id":49,"funcao_id":12},{"skill_id":64,"funcao_id":12},{"skill_id":1716,"funcao_id":12},{"skill_id":2101,"funcao_id":12},{"skill_id":4,"funcao_id":13},{"skill_id":15,"funcao_id":13},{"skill_id":19,"funcao_id":13},{"skill_id":44,"funcao_id":13},{"skill_id":45,"funcao_id":13},{"skill_id":47,"funcao_id":13},{"skill_id":49,"funcao_id":13},{"skill_id":64,"funcao_id":13},{"skill_id":1716,"funcao_id":13},{"skill_id":2101,"funcao_id":13},{"skill_id":15,"funcao_id":14},{"skill_id":19,"funcao_id":14},{"skill_id":44,"funcao_id":14},{"skill_id":45,"funcao_id":14},{"skill_id":47,"funcao_id":14},{"skill_id":49,"funcao_id":14},{"skill_id":55,"funcao_id":14},{"skill_id":57,"funcao_id":14},{"skill_id":58,"funcao_id":14},{"skill_id":59,"funcao_id":14},{"skill_id":60,"funcao_id":14},{"skill_id":64,"funcao_id":14},{"skill_id":1716,"funcao_id":14},{"skill_id":2101,"funcao_id":14},{"skill_id":15,"funcao_id":15},{"skill_id":19,"funcao_id":15},{"skill_id":44,"funcao_id":15},{"skill_id":45,"funcao_id":15},{"skill_id":47,"funcao_id":15},{"skill_id":49,"funcao_id":15},{"skill_id":55,"funcao_id":15},{"skill_id":57,"funcao_id":15},{"skill_id":58,"funcao_id":15},{"skill_id":59,"funcao_id":15},{"skill_id":60,"funcao_id":15},{"skill_id":64,"funcao_id":15},{"skill_id":1716,"funcao_id":15},{"skill_id":2101,"funcao_id":15},{"skill_id":19,"funcao_id":16},{"skill_id":26,"funcao_id":16},{"skill_id":34,"funcao_id":16},{"skill_id":37,"funcao_id":16},{"skill_id":44,"funcao_id":16},{"skill_id":45,"funcao_id":16},{"skill_id":46,"funcao_id":16},{"skill_id":47,"funcao_id":16},{"skill_id":49,"funcao_id":16},{"skill_id":56,"funcao_id":16},{"skill_id":1716,"funcao_id":16},{"skill_id":2101,"funcao_id":16},{"skill_id":0,"funcao_id":17},{"skill_id":1,"funcao_id":17},{"skill_id":2,"funcao_id":17},{"skill_id":3,"funcao_id":17},{"skill_id":4,"funcao_id":17},{"skill_id":5,"funcao_id":17},{"skill_id":6,"funcao_id":17},{"skill_id":7,"funcao_id":17},{"skill_id":10,"funcao_id":17},{"skill_id":19,"funcao_id":17},{"skill_id":26,"funcao_id":17},{"skill_id":27,"funcao_id":17},{"skill_id":34,"funcao_id":17},{"skill_id":37,"funcao_id":17},{"skill_id":38,"funcao_id":17},{"skill_id":44,"funcao_id":17},{"skill_id":45,"funcao_id":17},{"skill_id":46,"funcao_id":17},{"skill_id":47,"funcao_id":17},{"skill_id":49,"funcao_id":17},{"skill_id":56,"funcao_id":17},{"skill_id":1716,"funcao_id":17},{"skill_id":2101,"funcao_id":17},{"skill_id":0,"funcao_id":18},{"skill_id":1,"funcao_id":18},{"skill_id":2,"funcao_id":18},{"skill_id":3,"funcao_id":18},{"skill_id":4,"funcao_id":18},{"skill_id":5,"funcao_id":18},{"skill_id":6,"funcao_id":18},{"skill_id":7,"funcao_id":18},{"skill_id":10,"funcao_id":18},{"skill_id":17,"funcao_id":18},{"skill_id":19,"funcao_id":18},{"skill_id":20,"funcao_id":18},{"skill_id":21,"funcao_id":18},{"skill_id":22,"funcao_id":18},{"skill_id":23,"funcao_id":18},{"skill_id":26,"funcao_id":18},{"skill_id":28,"funcao_id":18},{"skill_id":34,"funcao_id":18},{"skill_id":37,"funcao_id":18},{"skill_id":38,"funcao_id":18},{"skill_id":44,"funcao_id":18},{"skill_id":45,"funcao_id":18},{"skill_id":46,"funcao_id":18},{"skill_id":47,"funcao_id":18},{"skill_id":49,"funcao_id":18},{"skill_id":54,"funcao_id":18},{"skill_id":56,"funcao_id":18},{"skill_id":1716,"funcao_id":18},{"skill_id":2101,"funcao_id":18},{"skill_id":0,"funcao_id":19},{"skill_id":1,"funcao_id":19},{"skill_id":2,"funcao_id":19},{"skill_id":3,"funcao_id":19},{"skill_id":4,"funcao_id":19},{"skill_id":5,"funcao_id":19},{"skill_id":6,"funcao_id":19},{"skill_id":7,"funcao_id":19},{"skill_id":10,"funcao_id":19},{"skill_id":17,"funcao_id":19},{"skill_id":19,"funcao_id":19},{"skill_id":20,"funcao_id":19},{"skill_id":21,"funcao_id":19},{"skill_id":22,"funcao_id":19},{"skill_id":23,"funcao_id":19},{"skill_id":26,"funcao_id":19},{"skill_id":28,"funcao_id":19},{"skill_id":34,"funcao_id":19},{"skill_id":37,"funcao_id":19},{"skill_id":38,"funcao_id":19},{"skill_id":44,"funcao_id":19},{"skill_id":45,"funcao_id":19},{"skill_id":46,"funcao_id":19},{"skill_id":47,"funcao_id":19},{"skill_id":49,"funcao_id":19},{"skill_id":54,"funcao_id":19},{"skill_id":56,"funcao_id":19},{"skill_id":1716,"funcao_id":19},{"skill_id":2101,"funcao_id":19}],"sugestoes_respeitam_bloqueios":true}'::jsonb,now());

insert into clube_novo.otimizador_historico_habilidades select 'habilidades-funcao-20260909-v1','habilidade_jogo',skill_id::text,to_jsonb(t) from clube_novo.habilidade_jogo t where true;

insert into clube_novo.otimizador_historico_habilidades select 'habilidades-funcao-20260909-v1','otimizador_lote_producao_v3',id::text,to_jsonb(t) from clube_novo.otimizador_lote_producao_v3 t where estado='pausado';

insert into clube_novo.otimizador_historico_habilidades select 'habilidades-funcao-20260909-v1','bloqueios','todos',jsonb_agg(to_jsonb(t)) from clube_novo.habilidade_funcao_bloqueio_otimizador t;

do $guard$ begin
 perform 1 from clube_novo.otimizador_lote_producao_v3 where estado='pausado' order by id for update;
 if (select count(*) from clube_novo.otimizador_lote_producao_v3 where estado='pausado')<>7
 or exists(select 1 from clube_novo.otimizador_lote_producao_linha_v3 where reserva_token is not null)
 or exists(select 1 from clube_novo.build_linha_card where estado_otimizador='processando')
 then raise exception 'Implantacao recusada: fila mudou ou ha processamento'; end if;
end $guard$;

create temporary table _fila_hab_antes on commit drop as select lote_id,md5(string_agg(linha_id::text||':'||ordem_fila::text,',' order by ordem_fila)) fp from clube_novo.otimizador_lote_producao_linha_v3 group by lote_id;

delete from clube_novo.habilidade_funcao_bloqueio_otimizador where funcao_id=16 and skill_id in(0,2,4);

insert into clube_novo.habilidade_funcao_bloqueio_otimizador(skill_id,funcao_id,origem) values (34,1,'habilidades-funcao-20260909-v1'),(44,1,'habilidades-funcao-20260909-v1'),(45,1,'habilidades-funcao-20260909-v1'),(46,1,'habilidades-funcao-20260909-v1'),(47,1,'habilidades-funcao-20260909-v1'),(49,1,'habilidades-funcao-20260909-v1'),(55,1,'habilidades-funcao-20260909-v1'),(56,1,'habilidades-funcao-20260909-v1'),(57,1,'habilidades-funcao-20260909-v1'),(58,1,'habilidades-funcao-20260909-v1'),(60,1,'habilidades-funcao-20260909-v1'),(64,1,'habilidades-funcao-20260909-v1'),(1716,1,'habilidades-funcao-20260909-v1'),(2101,1,'habilidades-funcao-20260909-v1'),(34,2,'habilidades-funcao-20260909-v1'),(44,2,'habilidades-funcao-20260909-v1'),(45,2,'habilidades-funcao-20260909-v1'),(46,2,'habilidades-funcao-20260909-v1'),(47,2,'habilidades-funcao-20260909-v1'),(49,2,'habilidades-funcao-20260909-v1'),(55,2,'habilidades-funcao-20260909-v1'),(56,2,'habilidades-funcao-20260909-v1'),(57,2,'habilidades-funcao-20260909-v1'),(58,2,'habilidades-funcao-20260909-v1'),(60,2,'habilidades-funcao-20260909-v1'),(64,2,'habilidades-funcao-20260909-v1'),(1716,2,'habilidades-funcao-20260909-v1'),(2101,2,'habilidades-funcao-20260909-v1'),(34,3,'habilidades-funcao-20260909-v1'),(44,3,'habilidades-funcao-20260909-v1'),(45,3,'habilidades-funcao-20260909-v1'),(46,3,'habilidades-funcao-20260909-v1'),(47,3,'habilidades-funcao-20260909-v1'),(49,3,'habilidades-funcao-20260909-v1'),(55,3,'habilidades-funcao-20260909-v1'),(57,3,'habilidades-funcao-20260909-v1'),(58,3,'habilidades-funcao-20260909-v1'),(60,3,'habilidades-funcao-20260909-v1'),(64,3,'habilidades-funcao-20260909-v1'),(1716,3,'habilidades-funcao-20260909-v1'),(2101,3,'habilidades-funcao-20260909-v1'),(0,4,'habilidades-funcao-20260909-v1'),(1,4,'habilidades-funcao-20260909-v1'),(2,4,'habilidades-funcao-20260909-v1'),(3,4,'habilidades-funcao-20260909-v1'),(4,4,'habilidades-funcao-20260909-v1'),(5,4,'habilidades-funcao-20260909-v1'),(6,4,'habilidades-funcao-20260909-v1'),(7,4,'habilidades-funcao-20260909-v1'),(10,4,'habilidades-funcao-20260909-v1'),(15,4,'habilidades-funcao-20260909-v1'),(17,4,'habilidades-funcao-20260909-v1'),(19,4,'habilidades-funcao-20260909-v1'),(20,4,'habilidades-funcao-20260909-v1'),(21,4,'habilidades-funcao-20260909-v1'),(22,4,'habilidades-funcao-20260909-v1'),(23,4,'habilidades-funcao-20260909-v1'),(26,4,'habilidades-funcao-20260909-v1'),(27,4,'habilidades-funcao-20260909-v1'),(28,4,'habilidades-funcao-20260909-v1'),(34,4,'habilidades-funcao-20260909-v1'),(36,4,'habilidades-funcao-20260909-v1'),(37,4,'habilidades-funcao-20260909-v1'),(38,4,'habilidades-funcao-20260909-v1'),(46,4,'habilidades-funcao-20260909-v1'),(48,4,'habilidades-funcao-20260909-v1'),(54,4,'habilidades-funcao-20260909-v1'),(55,4,'habilidades-funcao-20260909-v1'),(56,4,'habilidades-funcao-20260909-v1'),(57,4,'habilidades-funcao-20260909-v1'),(58,4,'habilidades-funcao-20260909-v1'),(59,4,'habilidades-funcao-20260909-v1'),(60,4,'habilidades-funcao-20260909-v1'),(0,5,'habilidades-funcao-20260909-v1'),(1,5,'habilidades-funcao-20260909-v1'),(2,5,'habilidades-funcao-20260909-v1'),(3,5,'habilidades-funcao-20260909-v1'),(4,5,'habilidades-funcao-20260909-v1'),(5,5,'habilidades-funcao-20260909-v1'),(6,5,'habilidades-funcao-20260909-v1'),(7,5,'habilidades-funcao-20260909-v1'),(10,5,'habilidades-funcao-20260909-v1'),(15,5,'habilidades-funcao-20260909-v1'),(17,5,'habilidades-funcao-20260909-v1'),(19,5,'habilidades-funcao-20260909-v1'),(20,5,'habilidades-funcao-20260909-v1'),(21,5,'habilidades-funcao-20260909-v1'),(22,5,'habilidades-funcao-20260909-v1'),(23,5,'habilidades-funcao-20260909-v1'),(26,5,'habilidades-funcao-20260909-v1'),(27,5,'habilidades-funcao-20260909-v1'),(28,5,'habilidades-funcao-20260909-v1'),(34,5,'habilidades-funcao-20260909-v1'),(36,5,'habilidades-funcao-20260909-v1'),(37,5,'habilidades-funcao-20260909-v1'),(38,5,'habilidades-funcao-20260909-v1'),(46,5,'habilidades-funcao-20260909-v1'),(48,5,'habilidades-funcao-20260909-v1'),(54,5,'habilidades-funcao-20260909-v1'),(55,5,'habilidades-funcao-20260909-v1'),(56,5,'habilidades-funcao-20260909-v1'),(57,5,'habilidades-funcao-20260909-v1'),(58,5,'habilidades-funcao-20260909-v1'),(59,5,'habilidades-funcao-20260909-v1'),(60,5,'habilidades-funcao-20260909-v1'),(0,6,'habilidades-funcao-20260909-v1'),(1,6,'habilidades-funcao-20260909-v1'),(2,6,'habilidades-funcao-20260909-v1'),(3,6,'habilidades-funcao-20260909-v1'),(4,6,'habilidades-funcao-20260909-v1'),(5,6,'habilidades-funcao-20260909-v1'),(6,6,'habilidades-funcao-20260909-v1'),(7,6,'habilidades-funcao-20260909-v1'),(10,6,'habilidades-funcao-20260909-v1'),(19,6,'habilidades-funcao-20260909-v1'),(20,6,'habilidades-funcao-20260909-v1'),(37,6,'habilidades-funcao-20260909-v1'),(44,6,'habilidades-funcao-20260909-v1'),(45,6,'habilidades-funcao-20260909-v1'),(47,6,'habilidades-funcao-20260909-v1'),(49,6,'habilidades-funcao-20260909-v1'),(56,6,'habilidades-funcao-20260909-v1'),(1716,6,'habilidades-funcao-20260909-v1'),(2101,6,'habilidades-funcao-20260909-v1'),(15,7,'habilidades-funcao-20260909-v1'),(19,7,'habilidades-funcao-20260909-v1'),(20,7,'habilidades-funcao-20260909-v1'),(37,7,'habilidades-funcao-20260909-v1'),(44,7,'habilidades-funcao-20260909-v1'),(45,7,'habilidades-funcao-20260909-v1'),(47,7,'habilidades-funcao-20260909-v1'),(49,7,'habilidades-funcao-20260909-v1'),(56,7,'habilidades-funcao-20260909-v1'),(1716,7,'habilidades-funcao-20260909-v1'),(2101,7,'habilidades-funcao-20260909-v1'),(15,8,'habilidades-funcao-20260909-v1'),(19,8,'habilidades-funcao-20260909-v1'),(34,8,'habilidades-funcao-20260909-v1'),(44,8,'habilidades-funcao-20260909-v1'),(45,8,'habilidades-funcao-20260909-v1'),(46,8,'habilidades-funcao-20260909-v1'),(47,8,'habilidades-funcao-20260909-v1'),(49,8,'habilidades-funcao-20260909-v1'),(60,8,'habilidades-funcao-20260909-v1'),(64,8,'habilidades-funcao-20260909-v1'),(1716,8,'habilidades-funcao-20260909-v1'),(2101,8,'habilidades-funcao-20260909-v1'),(15,9,'habilidades-funcao-20260909-v1'),(19,9,'habilidades-funcao-20260909-v1'),(34,9,'habilidades-funcao-20260909-v1'),(44,9,'habilidades-funcao-20260909-v1'),(45,9,'habilidades-funcao-20260909-v1'),(46,9,'habilidades-funcao-20260909-v1'),(47,9,'habilidades-funcao-20260909-v1'),(49,9,'habilidades-funcao-20260909-v1'),(55,9,'habilidades-funcao-20260909-v1'),(57,9,'habilidades-funcao-20260909-v1'),(58,9,'habilidades-funcao-20260909-v1'),(60,9,'habilidades-funcao-20260909-v1'),(64,9,'habilidades-funcao-20260909-v1'),(1716,9,'habilidades-funcao-20260909-v1'),(2101,9,'habilidades-funcao-20260909-v1'),(15,10,'habilidades-funcao-20260909-v1'),(19,10,'habilidades-funcao-20260909-v1'),(34,10,'habilidades-funcao-20260909-v1'),(44,10,'habilidades-funcao-20260909-v1'),(45,10,'habilidades-funcao-20260909-v1'),(46,10,'habilidades-funcao-20260909-v1'),(47,10,'habilidades-funcao-20260909-v1'),(49,10,'habilidades-funcao-20260909-v1'),(56,10,'habilidades-funcao-20260909-v1'),(1716,10,'habilidades-funcao-20260909-v1'),(2101,10,'habilidades-funcao-20260909-v1'),(15,11,'habilidades-funcao-20260909-v1'),(19,11,'habilidades-funcao-20260909-v1'),(34,11,'habilidades-funcao-20260909-v1'),(44,11,'habilidades-funcao-20260909-v1'),(45,11,'habilidades-funcao-20260909-v1'),(46,11,'habilidades-funcao-20260909-v1'),(47,11,'habilidades-funcao-20260909-v1'),(49,11,'habilidades-funcao-20260909-v1'),(56,11,'habilidades-funcao-20260909-v1'),(1716,11,'habilidades-funcao-20260909-v1'),(2101,11,'habilidades-funcao-20260909-v1'),(4,12,'habilidades-funcao-20260909-v1'),(15,12,'habilidades-funcao-20260909-v1'),(19,12,'habilidades-funcao-20260909-v1'),(44,12,'habilidades-funcao-20260909-v1'),(45,12,'habilidades-funcao-20260909-v1'),(47,12,'habilidades-funcao-20260909-v1'),(49,12,'habilidades-funcao-20260909-v1'),(64,12,'habilidades-funcao-20260909-v1'),(1716,12,'habilidades-funcao-20260909-v1'),(2101,12,'habilidades-funcao-20260909-v1'),(4,13,'habilidades-funcao-20260909-v1'),(15,13,'habilidades-funcao-20260909-v1'),(19,13,'habilidades-funcao-20260909-v1'),(44,13,'habilidades-funcao-20260909-v1'),(45,13,'habilidades-funcao-20260909-v1'),(47,13,'habilidades-funcao-20260909-v1'),(49,13,'habilidades-funcao-20260909-v1'),(64,13,'habilidades-funcao-20260909-v1'),(1716,13,'habilidades-funcao-20260909-v1'),(2101,13,'habilidades-funcao-20260909-v1'),(15,14,'habilidades-funcao-20260909-v1'),(19,14,'habilidades-funcao-20260909-v1'),(44,14,'habilidades-funcao-20260909-v1'),(45,14,'habilidades-funcao-20260909-v1'),(47,14,'habilidades-funcao-20260909-v1'),(49,14,'habilidades-funcao-20260909-v1'),(55,14,'habilidades-funcao-20260909-v1'),(57,14,'habilidades-funcao-20260909-v1'),(58,14,'habilidades-funcao-20260909-v1'),(59,14,'habilidades-funcao-20260909-v1'),(60,14,'habilidades-funcao-20260909-v1'),(64,14,'habilidades-funcao-20260909-v1'),(1716,14,'habilidades-funcao-20260909-v1'),(2101,14,'habilidades-funcao-20260909-v1'),(15,15,'habilidades-funcao-20260909-v1'),(19,15,'habilidades-funcao-20260909-v1'),(44,15,'habilidades-funcao-20260909-v1'),(45,15,'habilidades-funcao-20260909-v1'),(47,15,'habilidades-funcao-20260909-v1'),(49,15,'habilidades-funcao-20260909-v1'),(55,15,'habilidades-funcao-20260909-v1'),(57,15,'habilidades-funcao-20260909-v1'),(58,15,'habilidades-funcao-20260909-v1'),(59,15,'habilidades-funcao-20260909-v1'),(60,15,'habilidades-funcao-20260909-v1'),(64,15,'habilidades-funcao-20260909-v1'),(1716,15,'habilidades-funcao-20260909-v1'),(2101,15,'habilidades-funcao-20260909-v1'),(19,16,'habilidades-funcao-20260909-v1'),(26,16,'habilidades-funcao-20260909-v1'),(34,16,'habilidades-funcao-20260909-v1'),(37,16,'habilidades-funcao-20260909-v1'),(44,16,'habilidades-funcao-20260909-v1'),(45,16,'habilidades-funcao-20260909-v1'),(46,16,'habilidades-funcao-20260909-v1'),(47,16,'habilidades-funcao-20260909-v1'),(49,16,'habilidades-funcao-20260909-v1'),(56,16,'habilidades-funcao-20260909-v1'),(1716,16,'habilidades-funcao-20260909-v1'),(2101,16,'habilidades-funcao-20260909-v1'),(0,17,'habilidades-funcao-20260909-v1'),(1,17,'habilidades-funcao-20260909-v1'),(2,17,'habilidades-funcao-20260909-v1'),(3,17,'habilidades-funcao-20260909-v1'),(4,17,'habilidades-funcao-20260909-v1'),(5,17,'habilidades-funcao-20260909-v1'),(6,17,'habilidades-funcao-20260909-v1'),(7,17,'habilidades-funcao-20260909-v1'),(10,17,'habilidades-funcao-20260909-v1'),(19,17,'habilidades-funcao-20260909-v1'),(26,17,'habilidades-funcao-20260909-v1'),(27,17,'habilidades-funcao-20260909-v1'),(34,17,'habilidades-funcao-20260909-v1'),(37,17,'habilidades-funcao-20260909-v1'),(38,17,'habilidades-funcao-20260909-v1'),(44,17,'habilidades-funcao-20260909-v1'),(45,17,'habilidades-funcao-20260909-v1'),(46,17,'habilidades-funcao-20260909-v1'),(47,17,'habilidades-funcao-20260909-v1'),(49,17,'habilidades-funcao-20260909-v1'),(56,17,'habilidades-funcao-20260909-v1'),(1716,17,'habilidades-funcao-20260909-v1'),(2101,17,'habilidades-funcao-20260909-v1'),(0,18,'habilidades-funcao-20260909-v1'),(1,18,'habilidades-funcao-20260909-v1'),(2,18,'habilidades-funcao-20260909-v1'),(3,18,'habilidades-funcao-20260909-v1'),(4,18,'habilidades-funcao-20260909-v1'),(5,18,'habilidades-funcao-20260909-v1'),(6,18,'habilidades-funcao-20260909-v1'),(7,18,'habilidades-funcao-20260909-v1'),(10,18,'habilidades-funcao-20260909-v1'),(17,18,'habilidades-funcao-20260909-v1'),(19,18,'habilidades-funcao-20260909-v1'),(20,18,'habilidades-funcao-20260909-v1'),(21,18,'habilidades-funcao-20260909-v1'),(22,18,'habilidades-funcao-20260909-v1'),(23,18,'habilidades-funcao-20260909-v1'),(26,18,'habilidades-funcao-20260909-v1'),(28,18,'habilidades-funcao-20260909-v1'),(34,18,'habilidades-funcao-20260909-v1'),(37,18,'habilidades-funcao-20260909-v1'),(38,18,'habilidades-funcao-20260909-v1'),(44,18,'habilidades-funcao-20260909-v1'),(45,18,'habilidades-funcao-20260909-v1'),(46,18,'habilidades-funcao-20260909-v1'),(47,18,'habilidades-funcao-20260909-v1'),(49,18,'habilidades-funcao-20260909-v1'),(54,18,'habilidades-funcao-20260909-v1'),(56,18,'habilidades-funcao-20260909-v1'),(1716,18,'habilidades-funcao-20260909-v1'),(2101,18,'habilidades-funcao-20260909-v1'),(0,19,'habilidades-funcao-20260909-v1'),(1,19,'habilidades-funcao-20260909-v1'),(2,19,'habilidades-funcao-20260909-v1'),(3,19,'habilidades-funcao-20260909-v1'),(4,19,'habilidades-funcao-20260909-v1'),(5,19,'habilidades-funcao-20260909-v1'),(6,19,'habilidades-funcao-20260909-v1'),(7,19,'habilidades-funcao-20260909-v1'),(10,19,'habilidades-funcao-20260909-v1'),(17,19,'habilidades-funcao-20260909-v1'),(19,19,'habilidades-funcao-20260909-v1'),(20,19,'habilidades-funcao-20260909-v1'),(21,19,'habilidades-funcao-20260909-v1'),(22,19,'habilidades-funcao-20260909-v1'),(23,19,'habilidades-funcao-20260909-v1'),(26,19,'habilidades-funcao-20260909-v1'),(28,19,'habilidades-funcao-20260909-v1'),(34,19,'habilidades-funcao-20260909-v1'),(37,19,'habilidades-funcao-20260909-v1'),(38,19,'habilidades-funcao-20260909-v1'),(44,19,'habilidades-funcao-20260909-v1'),(45,19,'habilidades-funcao-20260909-v1'),(46,19,'habilidades-funcao-20260909-v1'),(47,19,'habilidades-funcao-20260909-v1'),(49,19,'habilidades-funcao-20260909-v1'),(54,19,'habilidades-funcao-20260909-v1'),(56,19,'habilidades-funcao-20260909-v1'),(1716,19,'habilidades-funcao-20260909-v1'),(2101,19,'habilidades-funcao-20260909-v1') on conflict(skill_id,funcao_id) do nothing;

update clube_novo.habilidade_jogo h set gemeas=x.ids,gemeas_nomes=x.nomes
from (select a.skill_id,array_agg(g.skill_id order by g.skill_id) filter(where g.skill_id is not null) ids,
 array_agg(g.nome_pt order by g.skill_id) filter(where g.skill_id is not null) nomes
 from clube_novo.habilidade_jogo a left join clube_novo.habilidade_jogo g
 on g.skill_id<>a.skill_id and g.efeito_por_codigo=a.efeito_por_codigo and a.efeito_por_codigo<>'{}'::jsonb
 group by a.skill_id) x where x.skill_id=h.skill_id and (h.gemeas is distinct from x.ids or h.gemeas_nomes is distinct from x.nomes);
update clube_novo.habilidade_jogo h set bloqueia_funcoes=x.funcoes
from (select h2.skill_id,array_agg(f.codigo_legado order by f.id) filter(where f.id is not null) funcoes
 from clube_novo.habilidade_jogo h2 left join clube_novo.habilidade_funcao_bloqueio_otimizador b using(skill_id)
 left join clube_novo.funcao_sistema f on f.id=b.funcao_id group by h2.skill_id) x
where x.skill_id=h.skill_id and h.bloqueia_funcoes is distinct from x.funcoes;

do $guard$ begin if (select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='otimizador_producao_concluir_linha_v3' and md5(pg_get_functiondef(p.oid))='71702843d038c21792a175852e13aaf4')<>1 then raise exception 'Contrato mudou: otimizador_producao_concluir_linha_v3'; end if; end $guard$;

do $guard$ begin if (select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='otimizador_producao_concluir_linha_v6' and md5(pg_get_functiondef(p.oid))='45fde109a0d0230d80d0844e5538e396')<>1 then raise exception 'Contrato mudou: otimizador_producao_concluir_linha_v6'; end if; end $guard$;

do $guard$ begin if (select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='otimizador_producao_importar_json_local_v1' and md5(pg_get_functiondef(p.oid))='7bdec4b15397e394624201ab7c3dbf4f')<>1 then raise exception 'Contrato mudou: otimizador_producao_importar_json_local_v1'; end if; end $guard$;

do $guard$ begin if (select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='otimizador_regua_v2' and md5(pg_get_functiondef(p.oid))='9e269e624dd6f16c0b81834acdaeaad6')<>1 then raise exception 'Contrato mudou: otimizador_regua_v2'; end if; end $guard$;

do $guard$ begin if (select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='otimizador_producao_criar_lote_integral_v5' and md5(pg_get_functiondef(p.oid))='aad54a3f58b96e7ebae0a5da9d562fa7')<>1 then raise exception 'Contrato mudou: otimizador_producao_criar_lote_integral_v5'; end if; end $guard$;

do $guard$ begin if (select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='otimizador_producao_pacote_local_linhas_v2' and md5(pg_get_functiondef(p.oid))='718d24075de79892d87bb52ecc82974e')<>1 then raise exception 'Contrato mudou: otimizador_producao_pacote_local_linhas_v2'; end if; end $guard$;

do $guard$ begin if (select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='otimizador_producao_pacote_local_manifesto_v2' and md5(pg_get_functiondef(p.oid))='7a007156635d9c55c9650427a0c044fb')<>1 then raise exception 'Contrato mudou: otimizador_producao_pacote_local_manifesto_v2'; end if; end $guard$;

do $guard$ begin if (select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='otimizador_producao_preparar_fatia_v5' and md5(pg_get_functiondef(p.oid))='217545ab673c6d006fc41170eb55694c')<>1 then raise exception 'Contrato mudou: otimizador_producao_preparar_fatia_v5'; end if; end $guard$;

do $guard$ begin if (select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='frontend_build_publicada_v2' and md5(pg_get_functiondef(p.oid))='18bf59306a1ed28befc1504159b32831')<>1 then raise exception 'Contrato mudou: frontend_build_publicada_v2'; end if; end $guard$;

do $guard$ begin if (select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='clube_novo' and p.proname='site_novo_ficha_sugestoes_v1' and md5(pg_get_functiondef(p.oid))='e477fe116850bd612896e72fc185d03f')<>1 then raise exception 'Contrato mudou: site_novo_ficha_sugestoes_v1'; end if; end $guard$;

do $guard$ begin if (select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='build_editor' and p.proname='catalogo_v1' and md5(pg_get_functiondef(p.oid))='4a092f8bb26bc41dc9e0b77d42c15613')<>1 then raise exception 'Contrato mudou: catalogo_v1'; end if; end $guard$;

CREATE OR REPLACE FUNCTION public.otimizador_regua_v2()
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_versao integer;
  v_atributos integer;
  v_funcoes integer;
  v_adicionais_validos integer;
  v_adicionais_proibidos integer;
  v_motivos text[] := '{}';
begin
  select max(versao) into v_versao from clube_novo.otimizador_molde;
  select count(*) into v_atributos from clube_novo.atributo_ordem_otimizador;
  select count(*) into v_funcoes from clube_novo.funcao_sistema where ativa and pode_rodar;
  if v_atributos<>26 then v_motivos:=array_append(v_motivos,'atributos_da_regua_incompletos'); end if;
  if v_funcoes<1 then v_motivos:=array_append(v_motivos,'funcoes_ativas_ausentes'); end if;
  if exists(
    select 1 from clube_novo.funcao_sistema f
    where f.ativa and f.pode_rodar and
      (select count(*) from clube_novo.otimizador_molde m
       where m.versao=v_versao and m.funcao_id=f.id)<>v_atributos
  ) then v_motivos:=array_append(v_motivos,'molde_incompleto_por_funcao'); end if;
  if (select count(*) from clube_novo.otimizador_regua_parametro)<>8 then
    v_motivos:=array_append(v_motivos,'parametros_da_regua_incompletos');
  end if;
  if (select count(*) from clube_novo.otimizador_custo_nivel)<>25 then
    v_motivos:=array_append(v_motivos,'custos_de_nivel_incompletos');
  end if;
  if (select count(*) from clube_novo.otimizador_multiplicador)<>100
     or (select min(ponto) from clube_novo.otimizador_multiplicador)<>0
     or (select max(ponto) from clube_novo.otimizador_multiplicador)<>99 then
    v_motivos:=array_append(v_motivos,'multiplicadores_incompletos');
  end if;
  if exists(select 1 from clube_novo.carta_habilidade_jogo ch
            join clube_novo.habilidade_jogo h using(skill_id) where not h.pode_rodar) then
    v_motivos:=array_append(v_motivos,'habilidade_de_carta_bloqueada');
  end if;

  -- REGRA UNICA (02/09/2026, ordem do Luis): vaga de Impeto adicionada so aceita
  -- Impeto NAO CONDICIONAL com TODOS os efeitos +1. Nao existe excecao.
  -- O "Pacote total" (condicional, +3 nos 26 atributos) NAO e adicionavel:
  -- a excecao 'pacote_total_excecao' foi REVOGADA nesta migracao.
  select count(*) into v_adicionais_validos
  from clube_novo.impeto_jogo i
  where i.condicional is false
    and exists (
      select 1 from clube_novo.impeto_atributo_jogo a
      where a.codigo_impeto=i.codigo_jogo
    )
    and not exists (
      select 1 from clube_novo.impeto_atributo_jogo a
      where a.codigo_impeto=i.codigo_jogo and a.delta<>1
    );

  -- TRAVA: nenhum candidato adicional pode ser condicional, ter delta<>1,
  -- ou mexer em mais de 4 atributos. Se algum passar, o lote NAO roda.
  select count(*) into v_adicionais_proibidos
  from clube_novo.impeto_jogo i
  where i.condicional is false
    and exists (
      select 1 from clube_novo.impeto_atributo_jogo a
      where a.codigo_impeto=i.codigo_jogo
    )
    and not exists (
      select 1 from clube_novo.impeto_atributo_jogo a
      where a.codigo_impeto=i.codigo_jogo and a.delta<>1
    )
    and (
      i.nome_pt='Pacote total'
      or (select count(*) from clube_novo.impeto_atributo_jogo a
          where a.codigo_impeto=i.codigo_jogo) > 4
    );

  if v_adicionais_validos<1 then
    v_motivos:=array_append(v_motivos,'catalogo_impetos_adicionais_ausente');
  end if;
  if v_adicionais_proibidos>0 then
    v_motivos:=array_append(v_motivos,'impeto_adicional_proibido_no_catalogo');
  end if;

  return jsonb_build_object(
    'contrato','otimizador_regua_v2',
    'politica_habilidades',(select regras from clube_novo.otimizador_politica_habilidades where versao='habilidades-funcao-20260909-v1'),
    'gate',jsonb_build_object('pode_rodar',cardinality(v_motivos)=0,'motivos',to_jsonb(v_motivos)),
    'versao_molde',v_versao,
    'parametros',(select coalesce(jsonb_object_agg(chave,valor),'{}'::jsonb)
                  from clube_novo.otimizador_regua_parametro),
    'barras',(select coalesce(jsonb_object_agg(barra,indices),'{}'::jsonb) from (
      select b.barra,jsonb_agg(o.indice_otimizador order by b.ordem) indices
      from clube_novo.otimizador_barra_atributo b
      join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=b.codigo_atributo
      group by b.barra) x),
    'custo_nivel',(select coalesce(jsonb_object_agg(nivel,acumulado),'{}'::jsonb)
                   from clube_novo.otimizador_custo_nivel),
    'multiplicadores',(select coalesce(jsonb_object_agg(ponto,multiplicador),'{}'::jsonb)
                       from clube_novo.otimizador_multiplicador),
    'atributos',(select jsonb_agg(jsonb_build_object(
      'indice_otimizador',o.indice_otimizador,'codigo',a.codigo,'bit',a.bit)
      order by o.indice_otimizador)
      from clube_novo.atributo_ordem_otimizador o
      join clube_novo.atributo_jogo a on a.codigo=o.codigo_atributo),
    'funcoes',(select jsonb_agg(jsonb_build_object('funcao_id',f.id,'ordem',f.ordem) order by f.id)
      from clube_novo.funcao_sistema f where f.ativa and f.pode_rodar),
    'molde',(select jsonb_agg(jsonb_build_object(
      'funcao_id',m.funcao_id,'indice_otimizador',o.indice_otimizador,
      'alvo',m.alvo,'peso',m.peso) order by m.funcao_id,o.indice_otimizador)
      from clube_novo.otimizador_molde m
      join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=m.codigo_atributo
      where m.versao=v_versao),
    'habilidades',(select jsonb_agg(jsonb_build_object(
      'skill_id',h.skill_id,'bit_na_carta',h.bit_na_carta,'tipo',h.tipo,
      'fabricavel',h.fabricavel,'vetada',h.vetada,'pode_rodar',h.pode_rodar,
      'efeitos',coalesce((select jsonb_agg(jsonb_build_object(
        'indice_otimizador',o.indice_otimizador,'codigo_atributo',e.key,
        'pct',coalesce((e.value->>'pct')::numeric,0),
        'flat',coalesce((e.value->>'flat')::numeric,0)) order by o.indice_otimizador)
        from jsonb_each(coalesce(h.efeito_por_codigo,'{}'::jsonb)) e
        join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=e.key),'[]'::jsonb)
      ) order by h.skill_id) from clube_novo.habilidade_jogo h where h.pode_rodar),
    'bloqueios',(select coalesce(jsonb_agg(jsonb_build_object(
      'skill_id',skill_id,'funcao_id',funcao_id) order by funcao_id,skill_id),'[]'::jsonb)
      from clube_novo.habilidade_funcao_bloqueio_otimizador),
    'incidencias',(select coalesce(jsonb_agg(jsonb_build_object(
      'skill_id',skill_id,'funcao_id',funcao_id,'incidencia_pct',incidencia_pct)
      order by funcao_id,skill_id),'[]'::jsonb)
      from clube_novo.habilidade_funcao_incidencia_otimizador),
    'tecnicos',(select jsonb_agg(jsonb_build_object(
      'tecnico_id',t.id,
      'proficiencias',coalesce((select jsonb_agg(jsonb_build_object(
        'codigo_estilo',e.codigo_estilo,'valor',e.proficiencia) order by e.codigo_estilo)
        from clube_novo.tecnico_estilo_jogo e where e.tecnico_id=t.id),'[]'::jsonb),
      'proficiencia_maxima',(select max(e.proficiencia) from clube_novo.tecnico_estilo_jogo e where e.tecnico_id=t.id),
      'estilos_principais',coalesce((select jsonb_agg(jsonb_build_object(
        'codigo_estilo',p.codigo_estilo,'valor',p.proficiencia,'gemea',p.gemea)
        order by p.codigo_estilo) from clube_novo.tecnico_estilo_principal_jogo p
        where p.tecnico_id=t.id and (p.principal or p.gemea)),'[]'::jsonb),
      'boosts',coalesce((select jsonb_agg(jsonb_build_object(
        'indice_otimizador',o.indice_otimizador,'codigo_atributo',b.codigo_atributo,'delta',b.delta)
        order by b.ordem) from clube_novo.tecnico_atributo_jogo b
        join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=b.codigo_atributo
        where b.tecnico_id=t.id),'[]'::jsonb)) order by t.id)
      from clube_novo.tecnico_jogo t where t.pode_rodar),
    'impetos',(select coalesce(jsonb_agg(jsonb_build_object(
      'codigo_impeto',i.codigo_jogo,'condicional',i.condicional,
      'nivel_maximo',clube_novo.impeto_nivel_maximo_v1(i.codigo_jogo),
      'efeitos',coalesce((select jsonb_agg(jsonb_build_object(
        'indice_otimizador',o.indice_otimizador,'codigo_atributo',a.codigo_atributo,'delta',a.delta)
        order by o.indice_otimizador) from clube_novo.impeto_atributo_jogo a
        join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=a.codigo_atributo
        where a.codigo_impeto=i.codigo_jogo),'[]'::jsonb)) order by i.codigo_jogo),'[]'::jsonb)
      from clube_novo.impeto_jogo i),
    'impetos_adicionais',(select coalesce(jsonb_agg(jsonb_build_object(
      'codigo_impeto',i.codigo_jogo,
      'nome_pt',i.nome_pt,
      'regra','delta_mais_um',
      'slots',jsonb_build_array(1,2),
      'efeitos',coalesce((select jsonb_agg(jsonb_build_object(
        'indice_otimizador',o.indice_otimizador,'codigo_atributo',a.codigo_atributo,'delta',a.delta)
        order by o.indice_otimizador) from clube_novo.impeto_atributo_jogo a
        join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=a.codigo_atributo
        where a.codigo_impeto=i.codigo_jogo),'[]'::jsonb)
    ) order by i.codigo_jogo),'[]'::jsonb)
    from clube_novo.impeto_jogo i
    where i.condicional is false
      and exists (select 1 from clube_novo.impeto_atributo_jogo a where a.codigo_impeto=i.codigo_jogo)
      and not exists (select 1 from clube_novo.impeto_atributo_jogo a where a.codigo_impeto=i.codigo_jogo and a.delta<>1))
  );
end $function$
;

CREATE OR REPLACE FUNCTION public.otimizador_producao_criar_lote_integral_v5(p_lote_id uuid, p_formula_fingerprint text, p_motor_versao text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_formula constant text:='a1cc830af3366e2d0c9ac12138d892058b3e57ed216e43d68242d105b33cb9d2';
  v_regua jsonb; v_contrato_fp text; v_fingerprint text;
  v_total integer:=0; v_condicionais integer:=0; v_inseridas integer:=0;
begin
  if p_lote_id is null or p_formula_fingerprint<>v_formula
     or p_motor_versao is distinct from 'otimizador-fila-producao-v3-local-20260909-habilidades-v12' then
    raise exception 'criação integral recusada: selo de fórmula ou versão local inválidos';
  end if;
  if exists(
    select 1 from clube_novo.otimizador_lote_producao_v3 where tipo_lote='integral'
  ) then
    raise exception 'criação integral recusada: já existe lote integral V5; a recuperação exige decisão explícita';
  end if;

  select public.otimizador_regua_v2() into v_regua;
  if not coalesce((v_regua->'gate'->>'pode_rodar')::boolean,false) then
    raise exception 'criação integral recusada: gate da régua do Otimizador está fechado';
  end if;
  v_contrato_fp:=clube_novo.otimizador_producao_contrato_fingerprint_v3(v_regua);

  select count(*) into v_total
  from clube_novo.carta_jogo c
  join clube_novo.otimizador_prioridade_orcamento_v1 pr on pr.card_id=c.card_id and pr.prioridade_grupo is not null
  where coalesce(c.roda_motor,false)
    and coalesce(c.pode_rodar_vinculos,false)
    and not exists(
      select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=c.card_id and coalesce(ci.condicional,false)
    );
  if v_total=0 then
    raise exception 'criação integral recusada: não há candidata básica elegível';
  end if;

  select count(*) into v_condicionais
  from clube_novo.carta_jogo c
  join clube_novo.otimizador_prioridade_orcamento_v1 pr on pr.card_id=c.card_id and pr.prioridade_grupo is not null
  where coalesce(c.roda_motor,false)
    and coalesce(c.pode_rodar_vinculos,false)
    and exists(
      select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=c.card_id and coalesce(ci.condicional,false)
    );

  v_fingerprint:=encode(extensions.digest(convert_to(
    'preparando:'||p_lote_id::text||':'||v_formula||':'||v_contrato_fp||':'||p_motor_versao,
    'UTF8'),'sha256'),'hex');

  insert into clube_novo.otimizador_lote_producao_v3(
    id,tipo_lote,estado,formula_fingerprint,contrato_fingerprint,motor_versao,
    regua_snapshot,fingerprint,cards,linhas,preparo_total,preparo_concluido,
    excluidas_incompletas,excluidas_impeto_condicional,excluidas_sem_linha,pode_publicar
  ) values (
    p_lote_id,'integral','preparando',v_formula,v_contrato_fp,p_motor_versao,
    v_regua,v_fingerprint,0,0,v_total,0,0,v_condicionais,0,false
  );

  insert into clube_novo.otimizador_lote_producao_candidata_v5(
    lote_id,card_id,ordem_candidata,overall_snapshot,carta_versao_snapshot
  )
  select p_lote_id,c.card_id,
         row_number() over(order by pr.prioridade_grupo,c.overall DESC NULLS FIRST,c.card_id collate "C")::bigint,
         c.overall::integer,coalesce(c.extraido_em::text,'')
  from clube_novo.carta_jogo c
  join clube_novo.otimizador_prioridade_orcamento_v1 pr on pr.card_id=c.card_id and pr.prioridade_grupo is not null
  where coalesce(c.roda_motor,false)
    and coalesce(c.pode_rodar_vinculos,false)
    and not exists(
      select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=c.card_id and coalesce(ci.condicional,false)
    );
  get diagnostics v_inseridas=row_count;
  if v_inseridas<>v_total then
    raise exception 'criação integral recusada: fotografia de candidatas não foi preservada (% de %)',v_inseridas,v_total;
  end if;

  insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
  values(p_lote_id,'preparo_integral_criado',jsonb_build_object(
    'candidatas_basicas',v_total,
    'excluidas_impeto_condicional',v_condicionais,
    'ordem','prioridade_orcamento_v1',
    'preparo','somente snapshots e linhas; nenhum cálculo foi iniciado',
    'pode_publicar',false
  ));
  return public.otimizador_producao_status_v5(p_lote_id);
end
$function$
;

CREATE OR REPLACE FUNCTION public.otimizador_producao_pacote_local_linhas_v2(p_lote_id uuid, p_depois_de_ordem bigint DEFAULT NULL::bigint, p_limite integer DEFAULT 1000)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
 SET statement_timeout TO '30s'
AS $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_itens jsonb := '[]'::jsonb;
  v_proxima_ordem bigint;
begin
  if p_lote_id is null or coalesce(p_limite, 0) not between 1 and 1000
     or coalesce(p_depois_de_ordem, 0) < 0 then
    raise exception 'página de linhas local v2 recusada: argumentos inválidos';
  end if;
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id;
  if not found or v_lote.tipo_lote <> 'integral'
     or v_lote.estado <> 'pausado'
     or v_lote.preparo_concluido <> v_lote.preparo_total
     or v_lote.pode_publicar is distinct from false
     or v_lote.formula_fingerprint not in (
       '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad',
       'bf6040b6fdbbb4a6b8cf97fe66cb441507ee637ec7edb300cf2ebabb5814f070',
       '5a7446b3dfa7b6b45ece1f611b1751fc1221f06e76c53cbd0827a83962c76e89','a1cc830af3366e2d0c9ac12138d892058b3e57ed216e43d68242d105b33cb9d2'
     ) then
    raise exception 'página de linhas local v2 recusada: fotografia não está estável';
  end if;
  if exists (
    select 1 from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id and l.estado_otimizador = 'processando'
  ) then
    raise exception 'página de linhas local v2 recusada: há reserva ativa';
  end if;

  with pagina as materialized (
    select q.linha_id, q.ordem_fila, q.entrada_fingerprint,
           q.prioridade_grupo,q.overall_prioridade,q.nivel_maximo,q.orcamento_real,q.captura_id,
           l.card_id, l.funcao_id, l.posicao_id,
           l.impeto_condicional_codigo, l.impeto_condicional_nivel,
           c.nome as carta_nome, f.rotulo as funcao_rotulo, p.nome_pt as posicao_rotulo
    from clube_novo.otimizador_fila_prioridade_v1 q
    join clube_novo.build_linha_card l on l.id = q.linha_id
    left join clube_novo.carta_jogo c on c.card_id = l.card_id
    left join clube_novo.funcao_sistema f on f.id = l.funcao_id
    left join clube_novo.posicao_jogo p on p.id = l.posicao_id
    where q.lote_id = p_lote_id
      and (p_depois_de_ordem is null or q.ordem_fila > p_depois_de_ordem)
      and l.estado_otimizador = 'pendente'
      -- 03/09: a linha condicional entra. Só fica de fora a que veio pela
      -- metade, sem o par completo que identifica o degrau.
      and ((l.impeto_condicional_codigo is null) = (l.impeto_condicional_nivel is null))
    order by q.ordem_fila
    limit p_limite
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'linha_id', linha_id,
    'ordem_fila', ordem_fila,
    'prioridade_grupo',prioridade_grupo,'overall_prioridade',overall_prioridade,
    'nivel_maximo',nivel_maximo,'orcamento_real',orcamento_real,'captura_id',captura_id,
    'card_id', card_id,
    'funcao_id', funcao_id,
    'posicao_id', posicao_id,
    'carta_entrada_fingerprint', entrada_fingerprint,
    'carta_nome', carta_nome,
    'funcao_rotulo', funcao_rotulo,
    'posicao_rotulo', posicao_rotulo,
    'impeto_condicional_codigo', impeto_condicional_codigo,
    'impeto_condicional_nivel', impeto_condicional_nivel
  ) order by ordem_fila), '[]'::jsonb), max(ordem_fila)
  into v_itens, v_proxima_ordem
  from pagina;

  return jsonb_build_object(
    'contrato', 'otimizador_pacote_local_v2',
    'lote_id', p_lote_id,
    'depois_de_ordem', p_depois_de_ordem,
    'proxima_ordem_fila', v_proxima_ordem,
    'limite', p_limite,
    'contagem_no_manifesto', true,
    'itens', v_itens,
    'pode_publicar', false,
    'impetos_condicionais', 'por_degrau'
  );
end
$function$
;

CREATE OR REPLACE FUNCTION public.otimizador_producao_pacote_local_manifesto_v2(p_lote_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
 SET statement_timeout TO '90s'
AS $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_cartas integer;
  v_linhas integer;
  v_condicionais integer;
  v_prioridade_fingerprint text;
begin
  if p_lote_id is null then
    raise exception 'pacote local v2 recusado: lote obrigatório';
  end if;

  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id;

  if not found or v_lote.tipo_lote <> 'integral' then
    raise exception 'pacote local v2 recusado: lote integral inexistente';
  end if;
  if v_lote.estado <> 'pausado'
     or v_lote.preparo_concluido <> v_lote.preparo_total
     or v_lote.pode_publicar is distinct from false
     or v_lote.formula_fingerprint not in (
       '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad',
       'bf6040b6fdbbb4a6b8cf97fe66cb441507ee637ec7edb300cf2ebabb5814f070',
       '5a7446b3dfa7b6b45ece1f611b1751fc1221f06e76c53cbd0827a83962c76e89','a1cc830af3366e2d0c9ac12138d892058b3e57ed216e43d68242d105b33cb9d2'
     )
     or not coalesce((v_lote.regua_snapshot -> 'gate' ->> 'pode_rodar')::boolean, false) then
    raise exception 'pacote local v2 recusado: lote não está pausado e apto para fotografia selada';
  end if;
  if exists (
    select 1 from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id and l.estado_otimizador = 'processando'
  ) then
    raise exception 'pacote local v2 recusado: há reserva ativa no lote';
  end if;
  if exists (
    select 1 from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id
      and l.estado_otimizador = 'pendente'
      and ((l.impeto_condicional_codigo is null) <> (l.impeto_condicional_nivel is null))
  ) then
    raise exception 'pacote local v2 recusado: há linha com Ímpeto condicional pela metade (código sem nível, ou o contrário)';
  end if;

  -- A fotografia de prioridade é cara nos lotes grandes. Materializar uma vez
  -- evita as quatro leituras integrais que faziam o RPC estourar 30 segundos.
  with pendentes as materialized (
    select p.*
    from clube_novo.otimizador_fila_prioridade_v1 p
    where p.lote_id = p_lote_id
  )
  select count(distinct card_id)::integer,
         count(*)::integer,
         count(*) filter(where impeto_condicional_codigo is not null)::integer,
         encode(extensions.digest(convert_to(coalesce(
           string_agg(linha_id::text||':'||ordem_fila::text||':'||prioridade_grupo::text||':'||
             coalesce(overall_prioridade::text,'null')||':'||nivel_maximo::text||':'||captura_id::text||':'||entrada_fingerprint,
             ',' order by ordem_fila),''),'UTF8'),'sha256'),'hex')
  into v_cartas,v_linhas,v_condicionais,v_prioridade_fingerprint
  from pendentes;

  return jsonb_build_object(
    'contrato','otimizador_pacote_local_v2',
    'lote_id',v_lote.id,
    'formula_fingerprint',v_lote.formula_fingerprint,
    'contrato_fingerprint',v_lote.contrato_fingerprint,
    'motor_versao',v_lote.motor_versao,
    'lote_fingerprint',v_lote.fingerprint,
    'regua',v_lote.regua_snapshot,
    'pode_publicar',false,
    'impetos_condicionais',case when v_condicionais>0 then 'por_degrau' else 'nenhum_no_lote' end,
    'linhas_condicionais',coalesce(v_condicionais,0),
    'cartas_total',coalesce(v_cartas,0),
    'linhas_total',coalesce(v_linhas,0),
    'paginacao','cursor_canonico',
    'prioridade_contrato','prioridade_orcamento_v1',
    'prioridade_fingerprint',v_prioridade_fingerprint,
    'fonte','clube_novo.otimizador_entrada_linha_v1'
  );
end
$function$
;

CREATE OR REPLACE FUNCTION public.otimizador_producao_preparar_fatia_v5(p_lote_id uuid, p_limite integer DEFAULT 10)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_formula constant text:='a1cc830af3366e2d0c9ac12138d892058b3e57ed216e43d68242d105b33cb9d2';
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_c clube_novo.otimizador_lote_producao_candidata_v5%rowtype;
  v_entrada jsonb; v_bonificador jsonb; v_versao_atual text;
  v_motivo text; v_processadas integer:=0; v_linhas integer:=0;
  v_linhas_inseridas integer:=0; v_ordem_base bigint:=0;
  v_pendentes_preparo integer:=0; v_concluidas_preparo integer:=0;
  v_cards_final integer:=0; v_linhas_final integer:=0; v_fingerprint text;
begin
  if p_lote_id is null or coalesce(p_limite,0) not between 1 and 20 then
    raise exception 'preparo V5 recusado: lote e limite 1..20 são obrigatórios';
  end if;
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id=p_lote_id
  for update;
  if not found then raise exception 'lote integral V5 inexistente'; end if;
  if v_lote.tipo_lote<>'integral' then raise exception 'preparo V5 recusado: lote não é integral'; end if;
  if v_lote.formula_fingerprint<>v_formula or v_lote.pode_publicar is not false then
    raise exception 'preparo V5 recusado: selo do lote não é a fórmula aprovada';
  end if;
  if v_lote.estado<>'preparando' then
    return public.otimizador_producao_status_v5(p_lote_id);
  end if;

  loop
    exit when v_processadas>=p_limite;
    select * into v_c
    from clube_novo.otimizador_lote_producao_candidata_v5 c
    where c.lote_id=p_lote_id and c.estado='pendente'
    order by (select p.prioridade_grupo from clube_novo.otimizador_prioridade_orcamento_v1 p where p.card_id=c.card_id) nulls last,
             c.overall_snapshot DESC NULLS FIRST,c.card_id collate "C"
    for update skip locked
    limit 1;
    exit when not found;
    v_processadas:=v_processadas+1;

    begin
      v_versao_atual:=null;
      select coalesce(c.extraido_em::text,'') into v_versao_atual
      from clube_novo.carta_jogo c
      where c.card_id=v_c.card_id;
      if not found or v_versao_atual is distinct from v_c.carta_versao_snapshot then
        update clube_novo.otimizador_lote_producao_candidata_v5
        set estado='divergente',motivo='a versão física da carta mudou durante o preparo',
            atualizado_em=clock_timestamp()
        where lote_id=p_lote_id and card_id=v_c.card_id;
        update clube_novo.otimizador_lote_producao_v3
        set estado='falhou',falha='preparo recusado: a fonte de uma carta mudou; recrie a fotografia do lote',
            atualizado_em=clock_timestamp()
        where id=p_lote_id;
        insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
        values(p_lote_id,'preparo_falhou',jsonb_build_object(
          'card_id',v_c.card_id,'motivo','versão física divergente'
        ));
        return public.otimizador_producao_status_v5(p_lote_id);
      end if;

      select public.otimizador_carta_v3(v_c.card_id),
             public.bonificador_carta_v2(v_c.card_id)
      into v_entrada,v_bonificador;

      if v_entrada is null or v_bonificador is null
         or not coalesce((v_entrada->'gate'->>'pode_rodar')::boolean,false)
         or not coalesce((v_bonificador->>'pode_rodar')::boolean,false)
         or not (v_bonificador ? 'carta_versao')
         or not (v_bonificador ? 'carta_fingerprint') then
        v_motivo:=coalesce(v_entrada#>>'{gate,motivos}',v_bonificador#>>'{gate,motivos}',
          'contrato de entrada incompleto ou gate fechado');
        update clube_novo.otimizador_lote_producao_candidata_v5
        set estado='incompleta',motivo=left(v_motivo,1000),preparado_em=clock_timestamp(),
            atualizado_em=clock_timestamp()
        where lote_id=p_lote_id and card_id=v_c.card_id;
        update clube_novo.otimizador_lote_producao_v3
        set excluidas_incompletas=excluidas_incompletas+1,
            preparo_concluido=preparo_concluido+1,atualizado_em=clock_timestamp()
        where id=p_lote_id;
      else
        select count(*) into v_linhas
        from (
          select distinct fp.funcao_id,fp.posicao_id
          from (
            select cpp.posicao_id
            from clube_novo.carta_posicao_principal_jogo cpp
            where cpp.card_id=v_c.card_id
            union
            select cp.posicao_id
            from clube_novo.carta_posicao_jogo cp
            where cp.card_id=v_c.card_id and cp.nivel_aptidao>0
          ) px
          join clube_novo.otimizador_funcao_posicao fp on fp.posicao_id=px.posicao_id
          join clube_novo.funcao_sistema fs on fs.id=fp.funcao_id and fs.ativa and fs.pode_rodar
          join clube_novo.posicao_jogo p on p.id=fp.posicao_id and p.pode_rodar
        ) linhas;
        if exists (select 1 from clube_novo.carta_impeto_jogo ci
                    where ci.card_id=v_c.card_id and coalesce(ci.condicional,false)) then
          v_linhas := v_linhas * 3;
        end if;

        if v_linhas=0 then
          update clube_novo.otimizador_lote_producao_candidata_v5
          set estado='sem_linha',motivo='não há posição e função canônicas aptas para a carta',
              preparado_em=clock_timestamp(),atualizado_em=clock_timestamp()
          where lote_id=p_lote_id and card_id=v_c.card_id;
          update clube_novo.otimizador_lote_producao_v3
          set excluidas_sem_linha=excluidas_sem_linha+1,
              preparo_concluido=preparo_concluido+1,atualizado_em=clock_timestamp()
          where id=p_lote_id;
        else
          insert into clube_novo.otimizador_lote_producao_carta_v3(
            lote_id,card_id,overall_snapshot,entrada_otimizador,entrada_fingerprint,
            carta_versao_bonificador,carta_fingerprint_bonificador
          ) values (
            p_lote_id,v_c.card_id,v_c.overall_snapshot,v_entrada,
            encode(extensions.digest(convert_to(v_entrada::text,'UTF8'),'sha256'),'hex'),
            v_bonificador->>'carta_versao',v_bonificador->>'carta_fingerprint'
          );

          select coalesce(max(ordem_fila),0) into v_ordem_base
          from clube_novo.otimizador_lote_producao_linha_v3
          where lote_id=p_lote_id;

          with linhas_base as (
            select distinct fp.funcao_id,fp.posicao_id
            from (
              select cpp.posicao_id
              from clube_novo.carta_posicao_principal_jogo cpp
              where cpp.card_id=v_c.card_id
              union
              select cp.posicao_id
              from clube_novo.carta_posicao_jogo cp
              where cp.card_id=v_c.card_id and cp.nivel_aptidao>0
            ) px
            join clube_novo.otimizador_funcao_posicao fp on fp.posicao_id=px.posicao_id
            join clube_novo.funcao_sistema fs on fs.id=fp.funcao_id and fs.ativa and fs.pode_rodar
            join clube_novo.posicao_jogo p on p.id=fp.posicao_id and p.pode_rodar
          ), inseridas as (
            insert into clube_novo.build_linha_card(
              card_id,funcao_id,posicao_id,lote_producao_id,carta_versao,carta_fingerprint,
              estado,pendencias,execucao_tipo,estado_otimizador,
              otimizador_formula_fingerprint_esperado,otimizador_contrato_fingerprint_esperado,
              otimizador_motor_versao_esperada,impeto_condicional_codigo,impeto_condicional_nivel
            )
            select v_c.card_id,b.funcao_id,b.posicao_id,p_lote_id,
                   v_bonificador->>'carta_versao',v_bonificador->>'carta_fingerprint',
                   'pendente','{}'::text[],'producao','pendente',
                   v_lote.formula_fingerprint,v_lote.contrato_fingerprint,v_lote.motor_versao,
                   cond.codigo,cond.nivel
            from linhas_base b
            cross join lateral (
              select ci.codigo_impeto::integer as codigo, d.nivel::smallint as nivel
                from (select ci2.codigo_impeto
                        from clube_novo.carta_impeto_jogo ci2
                       where ci2.card_id=v_c.card_id and coalesce(ci2.condicional,false)
                       order by ci2.slot limit 1) ci
                cross join (values (1),(2),(3)) d(nivel)
              union all
              select null::integer, null::smallint
               where not exists (select 1 from clube_novo.carta_impeto_jogo ci3
                                  where ci3.card_id=v_c.card_id and coalesce(ci3.condicional,false))
            ) cond
            order by b.funcao_id,b.posicao_id,cond.nivel
            returning id,card_id,funcao_id,posicao_id,impeto_condicional_codigo,impeto_condicional_nivel
          )
          insert into clube_novo.otimizador_lote_producao_linha_v3(
            lote_id,linha_id,card_id,ordem_fila,overall_snapshot,entrada_fingerprint
          )
          select p_lote_id,i.id,i.card_id,
                 v_ordem_base+row_number() over(order by b.funcao_id,b.posicao_id,i.impeto_condicional_codigo nulls first,i.impeto_condicional_nivel nulls first,i.id),
                 v_c.overall_snapshot,
                 encode(extensions.digest(convert_to(v_entrada::text,'UTF8'),'sha256'),'hex')
          from inseridas i
          join linhas_base b
            on b.funcao_id=i.funcao_id and b.posicao_id=i.posicao_id;
          get diagnostics v_linhas_inseridas=row_count;
          if v_linhas_inseridas<>v_linhas then
            raise exception 'preparo recusado: cardinalidade de linhas divergente para card_id %',v_c.card_id;
          end if;

          update clube_novo.otimizador_lote_producao_candidata_v5
          set estado='preparada',motivo=null,preparado_em=clock_timestamp(),atualizado_em=clock_timestamp()
          where lote_id=p_lote_id and card_id=v_c.card_id;
          update clube_novo.otimizador_lote_producao_v3
          set cards=cards+1,linhas=linhas+v_linhas,
              preparo_concluido=preparo_concluido+1,atualizado_em=clock_timestamp()
          where id=p_lote_id;
        end if;
      end if;
    exception when others then
      v_motivo:=left(sqlerrm,1000);
      update clube_novo.otimizador_lote_producao_candidata_v5
      set estado='divergente',motivo=v_motivo,atualizado_em=clock_timestamp()
      where lote_id=p_lote_id and card_id=v_c.card_id;
      update clube_novo.otimizador_lote_producao_v3
      set estado='falhou',falha='preparo V5 falhou fechado: '||v_motivo,
          atualizado_em=clock_timestamp()
      where id=p_lote_id;
      insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
      values(p_lote_id,'preparo_falhou',jsonb_build_object('card_id',v_c.card_id,'motivo',v_motivo));
      return public.otimizador_producao_status_v5(p_lote_id);
    end;
  end loop;

  select count(*) filter(where estado='pendente'),count(*) filter(where estado<>'pendente')
  into v_pendentes_preparo,v_concluidas_preparo
  from clube_novo.otimizador_lote_producao_candidata_v5
  where lote_id=p_lote_id;

  if v_pendentes_preparo=0 then
    select count(distinct card_id),count(*) into v_cards_final,v_linhas_final
    from clube_novo.otimizador_lote_producao_linha_v3
    where lote_id=p_lote_id;
    if v_linhas_final=0 then
      update clube_novo.otimizador_lote_producao_v3
      set estado='falhou',falha='preparo V5 terminou sem linha canônica apta',
          preparo_concluido=v_concluidas_preparo,atualizado_em=clock_timestamp()
      where id=p_lote_id;
      insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
      values(p_lote_id,'preparo_falhou',jsonb_build_object('motivo','nenhuma linha apta'));
    else
      select encode(extensions.digest(convert_to(
        p_lote_id::text||':'||v_lote.formula_fingerprint||':'||v_lote.contrato_fingerprint||':'||
        v_lote.motor_versao||':'||
        string_agg(q.card_id||':'||l.funcao_id::text||':'||l.posicao_id::text||':'||q.ordem_fila::text,
                   ',' order by q.ordem_fila),
        'UTF8'),'sha256'),'hex')
      into v_fingerprint
      from clube_novo.otimizador_lote_producao_linha_v3 q
      join clube_novo.build_linha_card l on l.id = q.linha_id
      where q.lote_id=p_lote_id;
      update clube_novo.otimizador_lote_producao_v3
      set estado='parado',cards=v_cards_final,linhas=v_linhas_final,
          preparo_concluido=v_concluidas_preparo,fingerprint=v_fingerprint,
          atualizado_em=clock_timestamp()
      where id=p_lote_id;
      insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
      values(p_lote_id,'preparo_integral_concluido',jsonb_build_object(
        'cards',v_cards_final,'linhas',v_linhas_final,'fingerprint',v_fingerprint,
        'impetos_condicionais','desligados','pode_publicar',false
      ));
    end if;
  elsif v_processadas>0 then
    insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
    values(p_lote_id,'preparo_fatia_concluida',jsonb_build_object(
      'candidatas_processadas',v_processadas,'pendentes_preparo',v_pendentes_preparo
    ));
  end if;
  return public.otimizador_producao_status_v5(p_lote_id);
end
$function$
;

create or replace function clube_novo.otimizador_validar_habilidades_v12(p_lote uuid,p_linha bigint,p_resultado jsonb)
returns void language plpgsql stable set search_path='' as $fn$
declare r jsonb; c jsonb; f bigint; hs integer[];
begin
 select o.regua_snapshot,lc.entrada_otimizador,l.funcao_id into r,c,f
 from clube_novo.build_linha_card l join clube_novo.otimizador_lote_producao_v3 o on o.id=p_lote
 join clube_novo.otimizador_lote_producao_carta_v3 lc on lc.lote_id=o.id and lc.card_id=l.card_id
 where l.id=p_linha;
 if r is null or p_resultado->>'politica_habilidades' is distinct from 'habilidades-funcao-20260909-v1'
 or r#>>'{politica_habilidades,versao}' is distinct from 'habilidades-funcao-20260909-v1'
 or p_resultado->>'motor_versao' is distinct from 'otimizador-fila-producao-v3-local-20260909-habilidades-v12' then
 raise exception 'Resultado sem a politica vigente de habilidades; atualize motor e pacote'; end if;
 select coalesce(array_agg(value::integer),'{}') into hs from jsonb_array_elements_text(p_resultado->'habilidades');
 if cardinality(hs)>5 or cardinality(hs)<>(select count(distinct x) from unnest(hs) x)
 then raise exception 'Lista de adicionais invalida'; end if;
 if exists(select 1 from jsonb_array_elements(c->'habilidades') x where (x->>'skill_id')::int=any(hs))
 then raise exception 'Adicional repete habilidade nativa'; end if;
 if exists(select 1 from unnest(hs) id left join clube_novo.habilidade_jogo h on h.skill_id=id
 where h.skill_id is null or not coalesce(h.fabricavel,false) or coalesce(h.vetada,true) or not coalesce(h.pode_rodar,false))
 then raise exception 'Adicional fora do catalogo elegivel'; end if;
 if exists(select 1 from clube_novo.habilidade_funcao_bloqueio_otimizador b where b.funcao_id=f and b.skill_id=any(hs))
 then raise exception 'Habilidade bloqueada para a funcao'; end if;
 if exists(select 1 from unnest(hs) id where not exists(
 select 1 from jsonb_array_elements(r->'habilidades') h cross join lateral jsonb_array_elements(h->'efeitos') e
 join jsonb_array_elements(r->'molde') m on m->>'indice_otimizador'=e->>'indice_otimizador'
 where (h->>'skill_id')::int=id and (m->>'funcao_id')::bigint=f and (m->>'peso')::numeric>0
 and (coalesce((e->>'pct')::numeric,0)>0 or coalesce((e->>'flat')::numeric,0)>0)))
 then raise exception 'Habilidade sem efeito em atributo pontuado pela funcao'; end if;
end $fn$;
revoke all on function clube_novo.otimizador_validar_habilidades_v12(uuid,bigint,jsonb) from public,anon,authenticated;

CREATE OR REPLACE FUNCTION public.otimizador_producao_importar_json_local_v1(p_lote_id uuid, p_linha_id bigint, p_resultado jsonb, p_calculado_em_utc timestamp with time zone)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_q clube_novo.otimizador_lote_producao_linha_v3%rowtype;
  v_l clube_novo.build_linha_card%rowtype;
  v_habilidades integer[];
  v_resultado_fp text;
  v_build_id bigint;
  v_enviado_em timestamptz;
  v_vals jsonb;
  v_vals_int jsonb;
  v_arows jsonb;
  v_impeto integer;
  v_cond_codigo integer;
  v_cond_nivel integer;
  v_completou boolean := false;
  v_lote_fingerprint_recebido text;
begin
  if p_lote_id is null or p_linha_id is null then
    raise exception 'importação JSON recusada: lote e linha são obrigatórios';
  end if;
  if p_calculado_em_utc is null then
    raise exception 'importação JSON recusada: data/hora de cálculo ausente';
  end if;
  if jsonb_typeof(p_resultado) <> 'object' then
    raise exception 'importação JSON recusada: resultado deve ser objeto';
  end if;

  select * into v_lote
    from clube_novo.otimizador_lote_producao_v3
   where id = p_lote_id
   for update;
  select * into v_q
    from clube_novo.otimizador_lote_producao_linha_v3
   where lote_id = p_lote_id
     and linha_id = p_linha_id
   for update;
  select * into v_l
    from clube_novo.build_linha_card
   where id = p_linha_id
   for update;

  if v_lote.id is null
     or v_lote.tipo_lote <> 'integral'
     or v_lote.pode_publicar is not false
     or v_q.linha_id is null
     or v_l.id is null
     or v_l.lote_producao_id is distinct from p_lote_id then
    raise exception 'importação JSON recusada: lote ou linha não pertence à fila integral';
  end if;
  if p_resultado->>'card_id' is distinct from v_l.card_id
     or (p_resultado->>'funcao_id')::bigint is distinct from v_l.funcao_id
     or (p_resultado->>'posicao_id')::integer is distinct from v_l.posicao_id then
    raise exception 'importação JSON recusada: identidade da linha diverge';
  end if;

  if v_l.otimizador_formula_fingerprint_esperado is null
     or v_l.otimizador_contrato_fingerprint_esperado is null
     or v_l.otimizador_motor_versao_esperada is null
     or v_q.entrada_fingerprint is null then
    raise exception 'importação JSON recusada: linha sem selos esperados completos';
  end if;

  if p_resultado->>'formula_fingerprint' is distinct from v_l.otimizador_formula_fingerprint_esperado
     or p_resultado->>'contrato_fingerprint' is distinct from v_l.otimizador_contrato_fingerprint_esperado
     or p_resultado->>'motor_versao' is distinct from v_l.otimizador_motor_versao_esperada
     or p_resultado->>'carta_entrada_fingerprint' is distinct from v_q.entrada_fingerprint then
    raise exception 'importação JSON recusada: selo da linha divergente';
  end if;

  v_lote_fingerprint_recebido := p_resultado->>'lote_fingerprint';
  if v_lote_fingerprint_recebido is null
     or v_lote_fingerprint_recebido !~ '^[0-9a-f]{64}$' then
    raise exception 'importação JSON recusada: fingerprint do lote ausente ou inválido';
  end if;

  -- O fingerprint acima registra a procedência declarada pelo pacote e fica no
  -- fingerprint integral do resultado. A integridade canônica é conferida pelos
  -- selos imutáveis da linha. O agregado do lote muda quando a fila recebe cartas
  -- novas e seus valores antigos não foram todos preservados no banco.

  v_cond_codigo := nullif(p_resultado->>'impeto_condicional_codigo', '')::integer;
  v_cond_nivel := nullif(p_resultado->>'impeto_condicional_nivel', '')::integer;

  if v_cond_codigo is distinct from v_l.impeto_condicional_codigo
     or v_cond_nivel is distinct from v_l.impeto_condicional_nivel then
    raise exception
      'importação JSON recusada: o degrau do Ímpeto condicional não é o desta linha (linha: % / %, resultado: % / %)',
      v_l.impeto_condicional_codigo, v_l.impeto_condicional_nivel,
      v_cond_codigo, v_cond_nivel;
  end if;
  if (v_cond_codigo is null) <> (v_cond_nivel is null) then
    raise exception 'importação JSON recusada: Ímpeto condicional pela metade (código sem nível, ou o contrário)';
  end if;
  if v_cond_nivel is not null and v_cond_nivel not between 1 and 3 then
    raise exception 'importação JSON recusada: degrau % fora de 1..3', v_cond_nivel;
  end if;

  if not (p_resultado ?& array[
    'b1', 'barras', 'tecnico_id', 'habilidades', 'builds_comparadas', 'builds_possiveis'
  ]) then
    raise exception 'importação JSON recusada: resultado incompleto';
  end if;
  if jsonb_typeof(p_resultado->'barras') <> 'object'
     or jsonb_typeof(p_resultado->'habilidades') <> 'array' then
    raise exception 'importação JSON recusada: build inválida';
  end if;

  v_impeto := nullif(p_resultado->>'impeto_adicional_codigo', '')::integer;
  perform clube_novo.conferir_impeto_x_posicao_v1(v_impeto, v_l.posicao_id);

  begin
    v_vals := case
      when jsonb_typeof(p_resultado->'vals_tela') = 'array'
       and jsonb_array_length(p_resultado->'vals_tela') = 26
      then p_resultado->'vals_tela'
    end;
  exception when others then
    v_vals := null;
  end;
  begin
    v_vals_int := case
      when jsonb_typeof(p_resultado->'vals') = 'array'
       and jsonb_array_length(p_resultado->'vals') = 26
      then p_resultado->'vals'
    end;
  exception when others then
    v_vals_int := null;
  end;
  begin
    v_arows := clube_novo.arows_da_cadeia_v1(p_resultado->'cadeia');
  exception when others then
    v_arows := null;
  end;

  select coalesce(array_agg(x.valor::integer order by x.ordem), '{}'::integer[])
    into v_habilidades
    from jsonb_array_elements_text(p_resultado->'habilidades')
      with ordinality x(valor, ordem);

  v_resultado_fp := encode(
    extensions.digest(convert_to(p_resultado::text, 'UTF8'), 'sha256'),
    'hex'
  );

  -- Uma resposta perdida depois do commit continua idempotente mesmo se o
  -- lote agregado tiver recebido outras cartas desde o primeiro envio.
  if v_l.estado_otimizador = 'concluido' then
    if v_l.build_otimizador_id is not null
       and v_q.resultado_fingerprint = v_resultado_fp then
      v_enviado_em := coalesce(v_q.finalizada_em, v_l.otimizador_finalizado_em);
      if v_enviado_em is null then
        raise exception 'importação JSON recusada: linha concluída sem carimbo de envio';
      end if;
      if v_vals is not null or v_vals_int is not null or v_arows is not null then
        update clube_novo.build_otimizador b
           set atributos_finais = coalesce(b.atributos_finais, v_vals),
               atributos_internos = coalesce(b.atributos_internos, v_vals_int),
               arows_snapshot = coalesce(b.arows_snapshot, v_arows)
         where b.id = v_l.build_otimizador_id
           and (
             b.atributos_finais is null
             or b.atributos_internos is null
             or b.arows_snapshot is null
           );
        v_completou := found;
      end if;
      return jsonb_build_object(
        'contrato', 'otimizador_importacao_json_local_v1',
        'linha_id', p_linha_id,
        'build_otimizador_id', v_l.build_otimizador_id,
        'resultado_fingerprint', v_resultado_fp,
        'lote_fingerprint_recebido', v_lote_fingerprint_recebido,
        'calculado_em_utc', p_calculado_em_utc,
        'enviado_em_utc', v_enviado_em,
        'idempotente', true,
        'numeros_completados', v_completou,
        'bonificador', 'pendente',
        'pode_publicar', false
      );
    end if;
    raise exception 'importação JSON recusada: linha concluída com resultado diferente';
  end if;

  if v_lote.estado <> 'pausado' then
    raise exception 'importação JSON recusada: o lote precisa estar pausado';
  end if;
  if v_l.estado_otimizador <> 'pendente'
     or v_q.reserva_token is not null
     or v_q.worker_id is not null then
    raise exception 'importação JSON recusada: a linha não está livre para envio local';
  end if;

  -- Regra vigente para novas gravacoes; recibos historicos seguem idempotentes.
  if exists (
    select 1 from clube_novo.habilidade_funcao_bloqueio_otimizador bq
    where bq.funcao_id = v_l.funcao_id and bq.skill_id = any(v_habilidades)
  ) then
    raise exception 'importação JSON recusada: habilidade adicional proibida nesta especialidade; atualize o pacote e recalcule a linha';
  end if;

  v_enviado_em := clock_timestamp();

  perform clube_novo.otimizador_validar_habilidades_v12(p_lote_id,p_linha_id,p_resultado);

  insert into clube_novo.build_otimizador(
    tecnico_id,
    barras,
    impeto_adicional_codigo,
    habilidades_adicionais,
    pontuacao,
    contrato_versao,
    contrato_fingerprint,
    carta_versao,
    carta_fingerprint,
    formula_fingerprint,
    resultado_fingerprint,
    motor_versao,
    builds_comparadas,
    builds_possiveis,
    atributos_finais,
    atributos_internos,
    arows_snapshot
  ) values (
    (p_resultado->>'tecnico_id')::bigint,
    p_resultado->'barras',
    v_impeto,
    v_habilidades,
    (p_resultado->>'b1')::numeric,
    'otimizador_regua_v2',
    v_l.otimizador_contrato_fingerprint_esperado,
    v_l.carta_versao,
    v_l.carta_fingerprint,
    v_l.otimizador_formula_fingerprint_esperado,
    v_resultado_fp,
    v_l.otimizador_motor_versao_esperada,
    (p_resultado->>'builds_comparadas')::integer,
    (p_resultado->>'builds_possiveis')::numeric,
    v_vals,
    v_vals_int,
    v_arows
  ) returning id into v_build_id;

  update clube_novo.build_linha_card
     set build_otimizador_id = v_build_id,
         estado_otimizador = 'concluido',
         erro_otimizador = null,
         otimizador_finalizado_em = v_enviado_em,
         pendencias = '{}'::text[],
         atualizado_em = v_enviado_em
   where id = p_linha_id
     and estado_otimizador = 'pendente';
  if not found then
    raise exception 'importação JSON recusada: a linha mudou durante o envio';
  end if;

  update clube_novo.otimizador_lote_producao_linha_v3
     set reserva_token = null,
         worker_id = null,
         reservada_em = null,
         finalizada_em = v_enviado_em,
         resultado_fingerprint = v_resultado_fp
   where lote_id = p_lote_id
     and linha_id = p_linha_id;

  insert into clube_novo.otimizador_evento_producao_v3(
    lote_id,
    linha_id,
    evento,
    detalhe
  ) values (
    p_lote_id,
    p_linha_id,
    'linha_importada_json_local',
    jsonb_build_object(
      'contrato', 'otimizador_importacao_json_local_v1',
      'build_otimizador_id', v_build_id,
      'resultado_fingerprint', v_resultado_fp,
      'lote_fingerprint_recebido', v_lote_fingerprint_recebido,
      'calculado_em_utc', p_calculado_em_utc,
      'enviado_em_utc', v_enviado_em,
      'atributos_finais', v_vals is not null,
      'atributos_internos', v_vals_int is not null,
      'arows_snapshot', v_arows is not null,
      'impeto_x_posicao_conferido', true,
      'impeto_condicional_codigo', v_cond_codigo,
      'impeto_condicional_nivel', v_cond_nivel,
      'bonificador', 'pendente',
      'pode_publicar', false
    )
  );

  if v_lote.preparo_concluido >= v_lote.preparo_total
     and not exists (
       select 1
       from clube_novo.otimizador_lote_producao_linha_v3 q2
       join clube_novo.build_linha_card l2 on l2.id = q2.linha_id
       where q2.lote_id = p_lote_id
         and l2.estado_otimizador in ('pendente', 'processando')
     ) then
    update clube_novo.otimizador_lote_producao_v3
       set estado = 'concluido',
           finalizado_em = v_enviado_em,
           atualizado_em = v_enviado_em
     where id = p_lote_id
       and estado = 'pausado';
    if found then
      insert into clube_novo.otimizador_evento_producao_v3(lote_id, evento, detalhe)
      values (
        p_lote_id,
        'lote_concluido',
        jsonb_build_object(
          'origem', 'operacao_local_json_v1',
          'enviado_em_utc', v_enviado_em
        )
      );
    end if;
  end if;

  return jsonb_build_object(
    'contrato', 'otimizador_importacao_json_local_v1',
    'linha_id', p_linha_id,
    'build_otimizador_id', v_build_id,
    'resultado_fingerprint', v_resultado_fp,
    'lote_fingerprint_recebido', v_lote_fingerprint_recebido,
    'calculado_em_utc', p_calculado_em_utc,
    'enviado_em_utc', v_enviado_em,
    'idempotente', false,
    'numeros_completados', false,
    'impeto_condicional_nivel', v_cond_nivel,
    'bonificador', 'pendente',
    'pode_publicar', false
  );
end
$function$
;

CREATE OR REPLACE FUNCTION public.otimizador_producao_concluir_linha_v3(p_lote_id uuid, p_linha_id bigint, p_reserva_token uuid, p_resultado jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_q clube_novo.otimizador_lote_producao_linha_v3%rowtype;
  v_l clube_novo.build_linha_card%rowtype; v_habilidades integer[];
  v_resultado_fp text; v_build_id bigint;
begin
  if jsonb_typeof(p_resultado)<>'object' then raise exception 'resultado do Otimizador deve ser objeto'; end if;
  select * into v_lote from clube_novo.otimizador_lote_producao_v3 where id=p_lote_id for update;
  select * into v_q from clube_novo.otimizador_lote_producao_linha_v3 where lote_id=p_lote_id and linha_id=p_linha_id for update;
  select * into v_l from clube_novo.build_linha_card where id=p_linha_id for update;
  if v_lote.id is null or v_q.linha_id is null or v_l.id is null then raise exception 'conclusão recusada: lote ou linha inexistente'; end if;
  if v_l.estado_otimizador<>'processando' or v_q.reserva_token is distinct from p_reserva_token then raise exception 'conclusão recusada: reserva não pertence ao worker'; end if;
  if p_resultado->>'card_id'<>v_l.card_id or (p_resultado->>'funcao_id')::bigint<>v_l.funcao_id or (p_resultado->>'posicao_id')::integer<>v_l.posicao_id then raise exception 'conclusão recusada: identidade da linha diverge'; end if;
  if p_resultado->>'formula_fingerprint'<>v_lote.formula_fingerprint or p_resultado->>'contrato_fingerprint'<>v_lote.contrato_fingerprint or p_resultado->>'motor_versao'<>v_lote.motor_versao or p_resultado->>'lote_fingerprint'<>v_lote.fingerprint or p_resultado->>'carta_entrada_fingerprint'<>v_q.entrada_fingerprint then raise exception 'conclusão recusada: selo divergente'; end if;
  if coalesce(p_resultado->>'impeto_condicional_codigo','')<>'' or coalesce(p_resultado->>'impeto_condicional_nivel','')<>'' then raise exception 'conclusão recusada: Ímpeto condicional continua desligado'; end if;
  if not (p_resultado ?& array['b1','barras','tecnico_id','habilidades','builds_comparadas','builds_possiveis']) then raise exception 'conclusão recusada: resultado incompleto'; end if;
  if jsonb_typeof(p_resultado->'barras')<>'object' or jsonb_typeof(p_resultado->'habilidades')<>'array' then raise exception 'conclusão recusada: build inválida'; end if;
  select coalesce(array_agg(x.valor::integer order by x.ordem),'{}'::integer[]) into v_habilidades from jsonb_array_elements_text(p_resultado->'habilidades') with ordinality x(valor,ordem);
  v_resultado_fp:=encode(extensions.digest(convert_to(p_resultado::text,'UTF8'),'sha256'),'hex');
  if exists(select 1 from clube_novo.habilidade_funcao_bloqueio_otimizador b
            where b.funcao_id=v_l.funcao_id and b.skill_id=any(v_habilidades)) then
    raise exception 'conclusão recusada: habilidade adicional proibida nesta especialidade';
  end if;
  perform clube_novo.otimizador_validar_habilidades_v12(p_lote_id,p_linha_id,p_resultado);

  insert into clube_novo.build_otimizador(
    tecnico_id,barras,impeto_adicional_codigo,habilidades_adicionais,pontuacao,
    contrato_versao,contrato_fingerprint,carta_versao,carta_fingerprint,
    formula_fingerprint,resultado_fingerprint,motor_versao,builds_comparadas,builds_possiveis
  ) values (
    (p_resultado->>'tecnico_id')::bigint,p_resultado->'barras',
    nullif(p_resultado->>'impeto_adicional_codigo','')::integer,v_habilidades,(p_resultado->>'b1')::numeric,
    'otimizador_regua_v2',v_lote.contrato_fingerprint,v_l.carta_versao,v_l.carta_fingerprint,
    v_lote.formula_fingerprint,v_resultado_fp,v_lote.motor_versao,
    (p_resultado->>'builds_comparadas')::integer,(p_resultado->>'builds_possiveis')::numeric
  ) returning id into v_build_id;
  update clube_novo.build_linha_card set build_otimizador_id=v_build_id,estado_otimizador='concluido',erro_otimizador=null,otimizador_finalizado_em=clock_timestamp(),pendencias='{}'::text[],atualizado_em=clock_timestamp() where id=p_linha_id;
  update clube_novo.otimizador_lote_producao_linha_v3 set reserva_token=null,worker_id=null,finalizada_em=clock_timestamp(),resultado_fingerprint=v_resultado_fp where lote_id=p_lote_id and linha_id=p_linha_id;
  insert into clube_novo.otimizador_evento_producao_v3(lote_id,linha_id,evento,detalhe) values(p_lote_id,p_linha_id,'linha_concluida',jsonb_build_object('build_otimizador_id',v_build_id,'resultado_fingerprint',v_resultado_fp,'bonificador','pendente'));
  if v_lote.estado='rodando' and not exists(select 1 from clube_novo.otimizador_lote_producao_linha_v3 q join clube_novo.build_linha_card l on l.id=q.linha_id where q.lote_id=p_lote_id and l.estado_otimizador in ('pendente','processando')) then
    update clube_novo.otimizador_lote_producao_v3 set estado='concluido',finalizado_em=clock_timestamp(),atualizado_em=clock_timestamp() where id=p_lote_id;
    insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento) values(p_lote_id,'lote_concluido');
  end if;
  return jsonb_build_object('contrato','otimizador_fila_producao_v3','linha_id',p_linha_id,'build_otimizador_id',v_build_id,'bonificador','pendente','pode_publicar',false);
end
$function$
;

CREATE OR REPLACE FUNCTION public.otimizador_producao_concluir_linha_v6(p_lote_id uuid, p_linha_id bigint, p_reserva_token uuid, p_resultado jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_q clube_novo.otimizador_lote_producao_linha_v3%rowtype;
  v_l clube_novo.build_linha_card%rowtype;
  v_habilidades integer[];
  v_resultado_fp text;
  v_build_id bigint;
begin
  if jsonb_typeof(p_resultado) <> 'object' then
    raise exception 'resultado do Otimizador deve ser objeto';
  end if;

  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id
  for update;
  select * into v_q
  from clube_novo.otimizador_lote_producao_linha_v3
  where lote_id = p_lote_id and linha_id = p_linha_id
  for update;
  select * into v_l
  from clube_novo.build_linha_card
  where id = p_linha_id
  for update;

  if v_lote.id is null or v_lote.tipo_lote <> 'integral'
     or v_q.linha_id is null or v_l.id is null then
    raise exception 'conclusão da esteira V6 recusada: lote ou linha inexistente';
  end if;
  if v_l.estado_otimizador <> 'processando'
     or v_q.reserva_token is distinct from p_reserva_token then
    raise exception 'conclusão da esteira V6 recusada: reserva não pertence ao worker';
  end if;
  if p_resultado->>'card_id' <> v_l.card_id
     or (p_resultado->>'funcao_id')::bigint <> v_l.funcao_id
     or (p_resultado->>'posicao_id')::integer <> v_l.posicao_id then
    raise exception 'conclusão da esteira V6 recusada: identidade da linha diverge';
  end if;
  if p_resultado->>'formula_fingerprint' <> v_lote.formula_fingerprint
     or p_resultado->>'contrato_fingerprint' <> v_lote.contrato_fingerprint
     or p_resultado->>'motor_versao' <> v_lote.motor_versao
     or p_resultado->>'lote_fingerprint' <> v_lote.fingerprint
     or p_resultado->>'carta_entrada_fingerprint' <> v_q.entrada_fingerprint then
    raise exception 'conclusão da esteira V6 recusada: selo divergente';
  end if;
  if coalesce(p_resultado->>'impeto_condicional_codigo', '') <> ''
     or coalesce(p_resultado->>'impeto_condicional_nivel', '') <> '' then
    raise exception 'conclusão da esteira V6 recusada: Ímpeto condicional continua desligado';
  end if;
  if not (p_resultado ?& array['b1', 'barras', 'tecnico_id', 'habilidades', 'builds_comparadas', 'builds_possiveis']) then
    raise exception 'conclusão da esteira V6 recusada: resultado incompleto';
  end if;
  if jsonb_typeof(p_resultado->'barras') <> 'object'
     or jsonb_typeof(p_resultado->'habilidades') <> 'array' then
    raise exception 'conclusão da esteira V6 recusada: build inválida';
  end if;

  select coalesce(array_agg(x.valor::integer order by x.ordem), '{}'::integer[])
  into v_habilidades
  from jsonb_array_elements_text(p_resultado->'habilidades') with ordinality x(valor, ordem);

  v_resultado_fp := encode(extensions.digest(convert_to(p_resultado::text, 'UTF8'), 'sha256'), 'hex');

  -- O ID é ALWAYS IDENTITY; a coluna não pode receber nextval/manualmente.
  if exists(select 1 from clube_novo.habilidade_funcao_bloqueio_otimizador b
            where b.funcao_id=v_l.funcao_id and b.skill_id=any(v_habilidades)) then
    raise exception 'conclusão recusada: habilidade adicional proibida nesta especialidade';
  end if;
  perform clube_novo.otimizador_validar_habilidades_v12(p_lote_id,p_linha_id,p_resultado);

  insert into clube_novo.build_otimizador(
    tecnico_id, barras, impeto_adicional_codigo, habilidades_adicionais, pontuacao,
    contrato_versao, contrato_fingerprint, carta_versao, carta_fingerprint,
    formula_fingerprint, resultado_fingerprint, motor_versao, builds_comparadas, builds_possiveis
  ) values (
    (p_resultado->>'tecnico_id')::bigint,
    p_resultado->'barras',
    nullif(p_resultado->>'impeto_adicional_codigo', '')::integer,
    v_habilidades,
    (p_resultado->>'b1')::numeric,
    'otimizador_regua_v2',
    v_lote.contrato_fingerprint,
    v_l.carta_versao,
    v_l.carta_fingerprint,
    v_lote.formula_fingerprint,
    v_resultado_fp,
    v_lote.motor_versao,
    (p_resultado->>'builds_comparadas')::integer,
    (p_resultado->>'builds_possiveis')::numeric
  ) returning id into v_build_id;

  update clube_novo.build_linha_card
  set build_otimizador_id = v_build_id,
      estado_otimizador = 'concluido',
      erro_otimizador = null,
      otimizador_finalizado_em = clock_timestamp(),
      pendencias = '{}'::text[],
      atualizado_em = clock_timestamp()
  where id = p_linha_id;

  update clube_novo.otimizador_lote_producao_linha_v3
  set reserva_token = null,
      worker_id = null,
      finalizada_em = clock_timestamp(),
      resultado_fingerprint = v_resultado_fp
  where lote_id = p_lote_id and linha_id = p_linha_id;

  insert into clube_novo.otimizador_evento_producao_v3(lote_id, linha_id, evento, detalhe)
  values(
    p_lote_id,
    p_linha_id,
    'linha_concluida',
    jsonb_build_object(
      'build_otimizador_id', v_build_id,
      'resultado_fingerprint', v_resultado_fp,
      'bonificador', 'pendente',
      'esteira_v6', true
    )
  );

  if v_lote.estado = 'rodando'
     and v_lote.preparo_concluido >= v_lote.preparo_total
     and not exists (
       select 1
       from clube_novo.otimizador_lote_producao_linha_v3 q2
       join clube_novo.build_linha_card l2 on l2.id = q2.linha_id
       where q2.lote_id = p_lote_id
         and l2.estado_otimizador in ('pendente', 'processando')
     ) then
    update clube_novo.otimizador_lote_producao_v3
    set estado = 'concluido', finalizado_em = clock_timestamp(), atualizado_em = clock_timestamp()
    where id = p_lote_id;
    insert into clube_novo.otimizador_evento_producao_v3(lote_id, evento)
    values(p_lote_id, 'lote_concluido');
  end if;

  return jsonb_build_object(
    'contrato', 'otimizador_fila_producao_v3',
    'linha_id', p_linha_id,
    'build_otimizador_id', v_build_id,
    'bonificador', 'pendente',
    'pode_publicar', false
  );
end
$function$
;

CREATE OR REPLACE FUNCTION clube_novo.site_novo_ficha_sugestoes_v1(p_card_id text, p_linha_id bigint)
 RETURNS jsonb
 LANGUAGE sql
 STABLE
 SET search_path TO ''
AS $function$
with contexto as materialized (
  select a.linha_id, a.card_id, a.funcao_id, b.tecnico_id,
         b.habilidades_adicionais, b.arows_snapshot, l.regua_snapshot as regua
  from clube_novo.build_publicacao_linha_ativa_v1 a
  join clube_novo.build_otimizador b on b.id = a.build_otimizador_id
  join clube_novo.otimizador_lote_producao_linha_v3 pl
    on pl.linha_id = a.linha_id and pl.resultado_fingerprint = b.resultado_fingerprint
  join clube_novo.otimizador_lote_producao_v3 l on l.id = pl.lote_id
  where a.card_id = p_card_id and a.linha_id = p_linha_id
), multiplicadores as materialized (
  select regua->'multiplicadores' as valores from contexto
), habilidades as materialized (
  select (h.item->>'skill_id')::integer as id, h.item,
    (select jsonb_agg(e.item order by e.item->>'codigo_atributo')
     from jsonb_array_elements(h.item->'efeitos') e(item)) as efeitos
  from contexto c cross join lateral jsonb_array_elements(c.regua->'habilidades') h(item)
), bloqueios as materialized (
  select b.skill_id as id from contexto c
  join clube_novo.habilidade_funcao_bloqueio_otimizador b on b.funcao_id=c.funcao_id
), incidencias as materialized (
  select (i.item->>'skill_id')::integer as id, (i.item->>'incidencia_pct')::numeric as pct
  from contexto c cross join lateral jsonb_array_elements(c.regua->'incidencias') i(item)
  where (i.item->>'funcao_id')::bigint = c.funcao_id
), pares as (
  select distinta.id, hg.nome_pt as nome, hg.ordem,
         coalesce(i.pct, 0) as incidencia,
         escolhida.skill_id as substitui_id, origem.nome_pt as substitui_nome,
         escolhida.ordem as ordem_escolhida
  from contexto c
  cross join lateral unnest(c.habilidades_adicionais) with ordinality escolhida(skill_id, ordem)
  join clube_novo.habilidade_jogo origem on origem.skill_id = escolhida.skill_id
  join habilidades atual on atual.id = escolhida.skill_id
  join habilidades distinta on distinta.id = any(origem.gemeas)
    and distinta.efeitos = atual.efeitos
    and distinta.item->>'tipo' = atual.item->>'tipo'
  join clube_novo.habilidade_jogo hg on hg.skill_id = distinta.id
  left join incidencias i on i.id = distinta.id
  where atual.item->>'fabricavel' = 'true'
    and distinta.item->>'fabricavel' = 'true'
    and distinta.item->>'pode_rodar' = 'true'
    and distinta.item->>'vetada' = 'false'
    and not (distinta.id = any(c.habilidades_adicionais))
    and not exists (select 1 from clube_novo.carta_habilidade_jogo n where n.card_id=c.card_id and n.skill_id=distinta.id)
    and not exists (select 1 from bloqueios v where v.id=distinta.id)
), gemeas as (
  select id,nome,ordem,incidencia,
    jsonb_agg(jsonb_build_object('id',substitui_id,'nome',substitui_nome) order by ordem_escolhida) as substitui
  from pares group by id,nome,ordem,incidencia
), pesos as materialized (
  select (p.item->>0)::integer as indice
  from contexto c cross join lateral jsonb_array_elements(c.arows_snapshot) p(item)
  where jsonb_array_length(c.arows_snapshot)=26 and (p.item->>1)::numeric <> 0
), catalogo_tecnicos as materialized (
  select (t.item->>'tecnico_id')::bigint as id, t.item,
         m.valores->(t.item->>'proficiencia_maxima') as multiplicador
  from contexto c cross join multiplicadores m
  cross join lateral jsonb_array_elements(c.regua->'tecnicos') t(item)
), tecnicos as materialized (
  select t.id, t.item, t.multiplicador,
         (select coalesce(jsonb_agg(jsonb_build_object('indice', (b.item->>'indice_otimizador')::integer,
                    'delta', (b.item->>'delta')::numeric) order by (b.item->>'indice_otimizador')::integer), '[]'::jsonb)
          from jsonb_array_elements(t.item->'boosts') b(item)
          join pesos p on p.indice=(b.item->>'indice_otimizador')::integer) as efeitos
  from contexto c
  join catalogo_tecnicos escolhido on escolhido.id=c.tecnico_id
  join catalogo_tecnicos t on t.multiplicador=escolhido.multiplicador
  where exists (select 1 from pesos)
), equivalentes as (
  select t.id,j.nome_en as nome,
    (select jsonb_agg(jsonb_build_object('codigo',e.item->>'codigo_estilo','nome',ej.nome_pt,
                          'proficiencia',(e.item->>'valor')::integer) order by ej.ordem)
     from jsonb_array_elements(t.item->'estilos_principais') e(item)
     join clube_novo.estilo_jogo_tecnico ej on ej.codigo=e.item->>'codigo_estilo') as estilos,
    (select coalesce(jsonb_agg(jsonb_build_object(
       'codigo_atributo',ta.codigo_atributo,'nome',aj.nome_pt,'delta',ta.delta
     ) order by ta.ordem),'[]'::jsonb)
     from clube_novo.tecnico_atributo_jogo ta
     join clube_novo.atributo_jogo aj on aj.codigo=ta.codigo_atributo
     where ta.tecnico_id=t.id) as atributos
  from contexto c join tecnicos escolhido on escolhido.id=c.tecnico_id
  join tecnicos t on t.id <> escolhido.id and t.multiplicador=escolhido.multiplicador and t.efeitos=escolhido.efeitos
  join clube_novo.tecnico_jogo j on j.id=t.id
  where jsonb_typeof(t.multiplicador)='number'
)
select jsonb_build_object(
  'estado', case when exists (select 1 from contexto) then 'pronto' else 'nao_publicado' end,
  'habilidades', coalesce((select jsonb_agg(jsonb_build_object('id',id,'nome',nome,'substitui',substitui)
                         order by incidencia desc,ordem,id) from gemeas), '[]'::jsonb),
  'tecnicos', coalesce((select jsonb_agg(jsonb_build_object('id',id,'nome',nome,'estilos',estilos,'atributos',atributos) order by nome,id)
                      from equivalentes), '[]'::jsonb)
);
$function$
;

create or replace function clube_novo.filtrar_gemeas_funcao_v12(p_habilidades jsonb,p_funcao bigint)
returns jsonb language sql stable set search_path='' as $fn$
select coalesce(jsonb_agg(jsonb_set(x.h,'{gemeas}',coalesce((
 select jsonb_agg(jsonb_build_object('skill_id',g.skill_id,'nome',g.nome_pt) order by g.nome_pt)
 from clube_novo.habilidade_jogo origem join clube_novo.habilidade_jogo g on g.skill_id=any(origem.gemeas)
 where origem.skill_id=(x.h->>'skill_id')::int and g.fabricavel and not g.vetada and g.pode_rodar
 and g.tipo=origem.tipo and g.efeito_por_codigo=origem.efeito_por_codigo
 and not exists(select 1 from clube_novo.habilidade_funcao_bloqueio_otimizador b where b.skill_id=g.skill_id and b.funcao_id=p_funcao)
),'[]'::jsonb)) order by x.n),'[]'::jsonb)
from jsonb_array_elements(coalesce(p_habilidades,'[]'::jsonb)) with ordinality x(h,n)
$fn$;
revoke all on function clube_novo.filtrar_gemeas_funcao_v12(jsonb,bigint) from public,anon,authenticated;

CREATE OR REPLACE FUNCTION public.frontend_build_publicada_v2(p_card_id text DEFAULT NULL::text, p_funcao_id bigint DEFAULT NULL::bigint, p_limit integer DEFAULT 100, p_offset integer DEFAULT 0)
 RETURNS TABLE(schema_versao text, publicacao_v2_fingerprint text, linha_id bigint, card_id text, carta_nome text, carta_tipo text, carta_box text, carta_overall integer, foto_url_cloudinary text, funcao_id bigint, funcao_codigo text, funcao_nome text, posicao_id integer, posicao_codigo text, posicao_nome text, build_otimizador_id bigint, build_bonificador_id bigint, tecnico_id bigint, tecnico_nome text, tecnico_bonus jsonb, tecnicos_sugeridos jsonb, barras jsonb, impeto_adicional_codigo integer, impeto_adicional jsonb, impeto_condicional jsonb, impetos jsonb, impetos_adicionaveis jsonb, degraus_publicados jsonb, habilidades_do_card jsonb, habilidades_adicionais jsonb, habilidades_sugeridas jsonb, atributos_finais jsonb, arows_snapshot jsonb, pontuacao_otimizador_bruta_evidencia numeric, pontuacao_otimizador_normalizada numeric, bonus_pe numeric, bonus_fisico_total numeric, bonus_posicao numeric, bonus_playstyle_1 numeric, bonus_playstyle_2 numeric, bonus_ia numeric, bonus_outros jsonb, bonus_total_bonificador numeric, overall_final numeric, pontuacao_final numeric, topo_funcao numeric, percentual_topo numeric, estado_final text, motivo_final text, normalizacao_fingerprint text, publicacao_linha_fingerprint_v2 text, publicada_em timestamp with time zone, proveniencia jsonb, contratacoes_por_box jsonb)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
  /* PORTA UNICA DA TELA. A fila publicada e lida da lista pronta
     clube_novo.build_pontuacao_final_v2_publica_v1, que ja vem com nome, foto, funcao,
     posicao, tecnico e impetos gravados e numerada em ordem. Ler direto da conta
     custava 53 segundos com 55 mil linhas e a tela so tem 3. */
  with pagina as materialized (
    /* TRES CAMINHOS SEPARADOS DE PROPOSITO. Num unico SELECT com "ou" o banco
       nao consegue escolher o atalho certo e varre a lista inteira (6 segundos
       para abrir uma ficha). Separados, cada chamada usa o seu atalho. */

    /* 1) FICHA: um card. */
    (select * from clube_novo.build_pontuacao_final_v2_publica_v1 base
      where p_card_id is not null and base.card_id = p_card_id
        and (p_funcao_id is null or base.funcao_id = p_funcao_id)
      order by base.overall_final desc, base.card_id, base.funcao_id,
        base.posicao_id, base.linha_id
      limit least(greatest(coalesce(p_limit, 100), 1), 500)
      offset greatest(coalesce(p_offset, 0), 0))
    union all
    /* 2) LISTA GERAL: faixa de numeros na fila. Mandar o banco pular N linhas
          o obriga a ler as N primeiras; a fila ja vem numerada. */
    (select * from clube_novo.build_pontuacao_final_v2_publica_v1 base
      where p_card_id is null and p_funcao_id is null
        and base.ordem_geral > greatest(coalesce(p_offset, 0), 0)
        and base.ordem_geral <= greatest(coalesce(p_offset, 0), 0)
            + least(greatest(coalesce(p_limit, 100), 1), 500)
      order by base.overall_final desc, base.card_id, base.funcao_id,
        base.posicao_id, base.linha_id
      limit least(greatest(coalesce(p_limit, 100), 1), 500))
    union all
    /* 3) LISTA DE UMA FUNCAO: mesma faixa, contada dentro da funcao. */
    (select * from clube_novo.build_pontuacao_final_v2_publica_v1 base
      where p_card_id is null and p_funcao_id is not null
        and base.funcao_id = p_funcao_id
        and base.ordem_na_funcao > greatest(coalesce(p_offset, 0), 0)
        and base.ordem_na_funcao <= greatest(coalesce(p_offset, 0), 0)
            + least(greatest(coalesce(p_limit, 100), 1), 500)
      order by base.overall_final desc, base.card_id, base.funcao_id,
        base.posicao_id, base.linha_id
      limit least(greatest(coalesce(p_limit, 100), 1), 500))
  ),
  /* CONSTANTES DA FICHA: valem para o card inteiro, nao mudam de linha para
     linha. Calculadas UMA vez -- por linha derrubavam a leitura por tempo. */
  fixos as materialized (
    select
      case when p_card_id is null then '[]'::jsonb
           else coalesce(public.frontend_impetos_adicionaveis_v1(), '[]'::jsonb) end as adicionaveis,
      case when p_card_id is null then '[]'::jsonb
           else coalesce(public.frontend_habilidades_do_card_v1(p_card_id), '[]'::jsonb) end as habs_card
  )
  select
    'clube-frontend-build-publicada-v2'::text,
    v.publicacao_v2_fingerprint, v.linha_id, v.card_id,
    v.carta_nome, v.carta_tipo, v.carta_box, v.carta_overall, v.foto_url_cloudinary,
    v.funcao_id, v.funcao_codigo, v.funcao_nome,
    v.posicao_id, v.posicao_codigo, v.posicao_nome,
    v.build_otimizador_id, v.build_bonificador_id,
    v.tecnico_id, v.tecnico_nome,
    /* DETALHE DA FICHA: so quando a leitura e de UM card. As telas de lista leem
       500 linhas por vez e nao usam nada disto -- calcular por linha ali derruba
       a leitura inteira por tempo (aconteceu em 04/09). */
    case when p_card_id is null then '[]'::jsonb else coalesce(tbon.itens, '[]'::jsonb) end,
    case when p_card_id is null then '[]'::jsonb else coalesce(tsug.itens, '[]'::jsonb) end,
    v.barras,
    v.impeto_adicional_codigo,
    v.impeto_adicional,
    v.impeto_condicional,
    case when p_card_id is null then '[]'::jsonb
         else coalesce(public.frontend_impetos_do_card_v1(v.card_id, v.linha_id), '[]'::jsonb) end,
    fx.adicionaveis,
    case when p_card_id is null then '[]'::jsonb
         else coalesce(public.frontend_degraus_da_linha_v1(v.card_id, v.funcao_id, v.posicao_id), '[]'::jsonb) end,
    clube_novo.filtrar_gemeas_funcao_v12(fx.habs_card,v.funcao_id),
    case when p_card_id is null then '[]'::jsonb
         else clube_novo.filtrar_gemeas_funcao_v12(public.frontend_habilidades_adicionais_v1(v.habilidades_adicionais),v.funcao_id) end,
    case when p_card_id is null then '[]'::jsonb else coalesce(hsug.itens, '[]'::jsonb) end,
    v.atributos_finais, v.arows_snapshot,
    v.pontuacao_otimizador_bruta_evidencia, v.pontuacao_otimizador_normalizada,
    v.bonus_pe, v.bonus_fisico_total, v.bonus_posicao,
    v.bonus_playstyle_1, v.bonus_playstyle_2, v.bonus_ia, v.bonus_outros,
    v.bonus_total_bonificador, v.overall_final, v.overall_final,
    v.topo_funcao, v.percentual_topo, v.estado_final, v.motivo_final,
    v.normalizacao_fingerprint, v.publicacao_linha_fingerprint_v2,
    v.publicada_em, v.proveniencia,
    case when p_card_id is null then '[]'::jsonb else coalesce(cx.itens, '[]'::jsonb) end
  from pagina v
  cross join fixos fx
  left join lateral (
    select jsonb_agg(jsonb_build_object('codigo', ta.codigo_atributo,
      'nome', a.nome_pt, 'delta', ta.delta) order by ta.ordem) as itens
    from clube_novo.tecnico_atributo_jogo ta
    left join clube_novo.atributo_jogo a on a.codigo = ta.codigo_atributo
    where p_card_id is not null and ta.tecnico_id = v.tecnico_id) tbon on true
  left join lateral (
    select jsonb_agg(distinct jsonb_build_object('skill_id', g.skill_id,
      'nome', coalesce(g.nome_pt, g.nome_en, g.nome_no_motor, g.skill_id::text))) as itens
    from unnest(case when p_card_id is null then '{}'::integer[]
                     else coalesce(v.habilidades_adicionais, '{}'::integer[]) end) as a(skill_id)
    join clube_novo.habilidade_jogo hb on hb.skill_id = a.skill_id
    join clube_novo.habilidade_jogo g on g.skill_id = any(hb.gemeas)
      and g.fabricavel and g.pode_rodar and g.tipo=hb.tipo and g.efeito_por_codigo=hb.efeito_por_codigo
    where not (g.skill_id = any(coalesce(v.habilidades_adicionais, '{}'::integer[])))
      and not exists (select 1 from clube_novo.carta_habilidade_jogo ch
                       where ch.card_id = v.card_id and ch.skill_id = g.skill_id)
      and coalesce(g.vetada, false) = false
      and (v.posicao_id = 0 or coalesce(g.so_goleiro, false) = false)
      and (v.posicao_id <> 0 or coalesce(g.so_de_linha, false) = false)
      and not exists (select 1 from clube_novo.habilidade_funcao_bloqueio_otimizador bq
                       where bq.skill_id = g.skill_id and bq.funcao_id = v.funcao_id)) hsug on true
  left join lateral (
    select jsonb_agg(jsonb_build_object('tecnico_id', o.tecnico_id, 'nome', o.nome)
                     order by o.nome) as itens
    from (select ta2.tecnico_id, t2.nome_en as nome
          from clube_novo.tecnico_atributo_jogo ta2
          join clube_novo.tecnico_jogo t2 on t2.id = ta2.tecnico_id
          where p_card_id is not null and ta2.tecnico_id <> v.tecnico_id
            and t2.nome_en is distinct from (select t0.nome_en
                                             from clube_novo.tecnico_jogo t0
                                             where t0.id = v.tecnico_id)
          group by ta2.tecnico_id, t2.nome_en
          having string_agg(ta2.codigo_atributo || ':' || ta2.delta, '|'
                            order by ta2.codigo_atributo) = (
            select string_agg(ta1.codigo_atributo || ':' || ta1.delta, '|'
                              order by ta1.codigo_atributo)
            from clube_novo.tecnico_atributo_jogo ta1
            where ta1.tecnico_id = v.tecnico_id)) o) tsug on true
  left join lateral (
    select case when p_card_id is null then null
                else clube_novo.contratacoes_por_box_build_v1(
                       v.card_id, v.funcao_nome, v.percentual_topo) end as itens) cx on true
  order by v.overall_final desc, v.card_id, v.funcao_id, v.posicao_id, v.linha_id
$function$
;

CREATE OR REPLACE FUNCTION build_editor.catalogo_v1(p_card_id text, p_posicao_id integer)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare result jsonb;
begin
 -- Consulta de cálculo disponível sem conta.
 if not exists(select 1 from clube_novo.carta_jogo where card_id=p_card_id) then raise exception 'Carta não encontrada.'; end if;
 select jsonb_build_object(
  'funcoes',(select coalesce(jsonb_agg(jsonb_build_object('id',f.id,'nome',f.rotulo,'posicao',fp.posicao_id) order by f.ordem),'[]')
     from clube_novo.funcao_sistema f join clube_novo.otimizador_funcao_posicao fp on fp.funcao_id=f.id
     where f.ativa and f.pode_rodar and (exists(select 1 from clube_novo.carta_posicao_jogo cp where cp.card_id=p_card_id and cp.posicao_id=fp.posicao_id and cp.nivel_aptidao>0)
      or exists(select 1 from clube_novo.carta_posicao_principal_jogo pp where pp.card_id=p_card_id and pp.posicao_id=fp.posicao_id))),
  'habilidades',(select coalesce(jsonb_agg(jsonb_build_object('id',h.skill_id,'nome',h.nome_pt,'gemeas','[]'::jsonb,'gemeas_cadastradas',h.gemeas,'fabricavel',h.fabricavel,'vetada',h.vetada,'avaliavel',h.efeito_por_codigo is not null and not h.efeito_desconhecido) order by h.nome_pt),'[]')
     from clube_novo.habilidade_jogo h where h.tipo='comum' and (p_posicao_id=0 or h.skill_id not in (44,45,47,49))
     and not exists(select 1 from clube_novo.carta_habilidade_jogo ch where ch.card_id=p_card_id and ch.skill_id=h.skill_id)),
  'tecnicos',(select coalesce(jsonb_agg(jsonb_build_object('id',t.id::text,'nome',t.nome_en,'atributos',(select coalesce(jsonb_agg(jsonb_build_object('codigo',ta.codigo_atributo,'nome',a.nome_pt,'delta',ta.delta) order by ta.codigo_atributo),'[]') from clube_novo.tecnico_atributo_jogo ta join clube_novo.atributo_jogo a on a.codigo=ta.codigo_atributo where ta.tecnico_id=t.id and ta.confirmado),'proficiencia',(select max(proficiencia) from clube_novo.tecnico_estilo_jogo where tecnico_id=t.id and confirmado)) order by t.nome_en),'[]')
     from clube_novo.tecnico_jogo t where t.pode_rodar and exists(select 1 from clube_novo.tecnico_estilo_jogo te where te.tecnico_id=t.id and confirmado)),
  'adicionais',(select coalesce(jsonb_agg(jsonb_build_object('codigo',i.codigo_jogo,'nome',i.nome_pt,'cor',i.tipo_condicao_raw,'efeitos',(select jsonb_agg(jsonb_build_object('nome',a.nome_pt,'delta',ia.delta)) from clube_novo.impeto_atributo_jogo ia join clube_novo.atributo_jogo a on a.codigo=ia.codigo_atributo where ia.codigo_impeto=i.codigo_jogo)) order by i.nome_pt),'[]')
    from clube_novo.impeto_jogo i join build_editor.adicionais_v1(p_posicao_id) c on c.codigo=i.codigo_jogo),
  'slots',(select coalesce(jsonb_agg(jsonb_build_object('slot',c.slot,'codigo',c.codigo_impeto,'nome',i.nome_pt,'vaga',c.vaga,'condicional',c.condicional,'cor',i.tipo_condicao_raw,
      'maximo',case when c.condicional then coalesce((select efeito_maximo from clube_novo.impeto_condicao_parametro_faixa_jogo where codigo_impeto=c.codigo_impeto),(select max(delta) from clube_novo.impeto_atributo_jogo where codigo_impeto=c.codigo_impeto)) end,
      'efeitos',(select jsonb_agg(jsonb_build_object('nome',a.nome_pt,'delta',ia.delta)) from clube_novo.impeto_atributo_jogo ia join clube_novo.atributo_jogo a on a.codigo=ia.codigo_atributo where ia.codigo_impeto=c.codigo_impeto)) order by c.slot),'[]')
    from clube_novo.carta_impeto_jogo c left join clube_novo.impeto_jogo i on i.codigo_jogo=c.codigo_impeto where c.card_id=p_card_id),
  'bloqueios_sugestao',(select coalesce(jsonb_agg(jsonb_build_object('skill_id',b.skill_id,'funcao_id',b.funcao_id)),'[]'::jsonb) from clube_novo.habilidade_funcao_bloqueio_otimizador b),
  'custos',(select jsonb_object_agg(nivel,acumulado) from clube_novo.otimizador_custo_nivel)
 ) into result;
 return result;
end $function$
;

create temporary table _hab_lotes on commit drop as
select id,jsonb_set(jsonb_set(regua_snapshot,'{bloqueios}',(select jsonb_agg(jsonb_build_object('skill_id',skill_id,'funcao_id',funcao_id) order by funcao_id,skill_id) from clube_novo.habilidade_funcao_bloqueio_otimizador)),
 '{politica_habilidades}',(select regras from clube_novo.otimizador_politica_habilidades where versao='habilidades-funcao-20260909-v1')) regua
from clube_novo.otimizador_lote_producao_v3 where estado='pausado';
update clube_novo.otimizador_lote_producao_v3 o set regua_snapshot=x.regua,
 contrato_fingerprint=clube_novo.otimizador_producao_contrato_fingerprint_v3(x.regua),
 formula_fingerprint='a1cc830af3366e2d0c9ac12138d892058b3e57ed216e43d68242d105b33cb9d2',motor_versao='otimizador-fila-producao-v3-local-20260909-habilidades-v12' from _hab_lotes x where x.id=o.id;
update clube_novo.build_linha_card l set
 otimizador_contrato_fingerprint_esperado=o.contrato_fingerprint,
 otimizador_formula_fingerprint_esperado=o.formula_fingerprint,
 otimizador_motor_versao_esperada=o.motor_versao
from clube_novo.otimizador_lote_producao_v3 o join _hab_lotes x on x.id=o.id
where l.lote_producao_id=o.id and l.estado_otimizador='pendente' and l.estado<>'invalida';
do $guard$ begin
 if (select count(*) from clube_novo.habilidade_funcao_bloqueio_otimizador)<>325 then raise exception 'Matriz de bloqueios incompleta'; end if;
 if exists(select 1 from _fila_hab_antes a join (select lote_id,md5(string_agg(linha_id::text||':'||ordem_fila::text,',' order by ordem_fila)) fp from clube_novo.otimizador_lote_producao_linha_v3 group by lote_id) b using(lote_id) where a.fp<>b.fp)
 then raise exception 'A ordem da fila mudou'; end if;
end $guard$;
comment on table clube_novo.otimizador_politica_habilidades is 'Decisao de 09/09/2026: motor por funcao, 0..5 adicionais com ganho, sugestoes filtradas; editor manual livre. Fonte em 4-DOCUMENTOS/OTIMIZADOR/HABILIDADES-0909.';
