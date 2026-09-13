-- Rollback cirurgico da habilitacao de Chute subito.
-- Nao restaura resultados/fila do Otimizador; esse estado deve ser tratado pelo
-- rollback proprio do lote corretivo, preservando historico e trabalhadores.

begin;
set local lock_timeout = '5s';
set local statement_timeout = '30s';

delete from clube_novo.carta_habilidade_jogo
where skill_id = 2457
  and card_id in ('88045755960771','88045755960841','88045755964138');

delete from clube_novo.contrato_leitura_envelope_mapeamento m
using clube_novo.contrato_leitura_campo f
where m.campo_id = f.campo_id
  and f.contrato_id = 'clubef-dt870-2026-r1'
  and f.chave_campo = 'carta.habilidade.2457';

delete from clube_novo.contrato_leitura_campo
where contrato_id = 'clubef-dt870-2026-r1'
  and chave_campo = 'carta.habilidade.2457';

with ordem_fisica as (
  select m.mapeamento_id,
         (row_number() over (order by f.bit_inicio, m.mapeamento_id) - 1)::integer as ordem_correta
  from clube_novo.contrato_leitura_envelope_mapeamento m
  join clube_novo.contrato_leitura_campo f on f.campo_id = m.campo_id
  where f.contrato_id = 'clubef-dt870-2026-r1'
    and m.destino_id = 21
    and m.coluna_destino = 'skill_id'
    and m.grupo_repeticao = 'habilidades_player_bin'
)
update clube_novo.contrato_leitura_envelope_mapeamento m
set ordem_regra = o.ordem_correta
from ordem_fisica o
where o.mapeamento_id = m.mapeamento_id
  and m.ordem_regra is distinct from o.ordem_correta;

with ordem_por_skill as (
  select (f.transformacao->>'skill_id')::integer as skill_id,
         m.ordem_regra::smallint as ordem_correta
  from clube_novo.contrato_leitura_envelope_mapeamento m
  join clube_novo.contrato_leitura_campo f on f.campo_id = m.campo_id
  where f.contrato_id = 'clubef-dt870-2026-r1'
    and m.destino_id = 21
    and m.coluna_destino = 'skill_id'
    and m.grupo_repeticao = 'habilidades_player_bin'
)
update clube_novo.carta_habilidade_jogo ch
set ordem = (ch.ordem + 1000)::smallint
from ordem_por_skill o
where o.skill_id = ch.skill_id
  and ch.ordem is distinct from o.ordem_correta;

with ordem_por_skill as (
  select (f.transformacao->>'skill_id')::integer as skill_id,
         m.ordem_regra::smallint as ordem_correta
  from clube_novo.contrato_leitura_envelope_mapeamento m
  join clube_novo.contrato_leitura_campo f on f.campo_id = m.campo_id
  where f.contrato_id = 'clubef-dt870-2026-r1'
    and m.destino_id = 21
    and m.coluna_destino = 'skill_id'
    and m.grupo_repeticao = 'habilidades_player_bin'
)
update clube_novo.carta_habilidade_jogo ch
set ordem = o.ordem_correta
from ordem_por_skill o
where o.skill_id = ch.skill_id
  and ch.ordem >= 1000;

update clube_novo.habilidade_jogo
set nome_en = null,
    nome_pt = nome_jp,
    tipo = 'a_catalogar',
    bit_na_carta = null,
    cartas = 0,
    efeito = null,
    codigo_casa = 'jogo_2457',
    fabricavel = null,
    so_goleiro = null,
    extras = jsonb_build_object('fonte','PlayerSkill.bin'),
    efeito_por_codigo = null,
    efeito_legivel = null,
    so_de_linha = null,
    nome_no_motor = nome_jp,
    efeito_desconhecido = true,
    bit_desconhecido = true,
    pode_rodar = false,
    falta_o_que = 'efeito nao apurado · endereco na carta nao achado'
where skill_id = 2457;

update clube_novo.contrato_leitura_jogo
set versao_contrato = 'r4-rehomologacao-jogo-0309-v1',
    fingerprint_contrato_sha256 =
      clube_novo.fingerprint_material_contrato_leitura(contrato_id),
    validado_em = clock_timestamp()
where contrato_id = 'clubef-dt870-2026-r1';

commit;
