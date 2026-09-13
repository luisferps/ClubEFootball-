-- Chute subito (skill_id 2457) - contrato fisico, catalogo do motor e relacoes.
--
-- Prova fisica: Player.bin do dt870_updated, bit 639 (largura 1), presente
-- exatamente nos cards 88045755960771, 88045755960841 e 88045755964138.
-- Regra aprovada em 05/09/2026: Finalizacao +5%; Forca do chute +0%.
-- O script e idempotente e nao pausa/reinicia trabalhadores nem altera lotes.

begin;
set local lock_timeout = '5s';
set local statement_timeout = '120s';

do $guard$
begin
  if not exists (
    select 1
    from clube_novo.contrato_leitura_jogo
    where contrato_id = 'clubef-dt870-2026-r1'
      and estado = 'ativo'
      and cobertura_total
  ) then
    raise exception 'Chute subito recusado: contrato fisico ativo/integral nao encontrado';
  end if;

  if not exists (
    select 1 from clube_novo.habilidade_jogo where skill_id = 2457
  ) then
    raise exception 'Chute subito recusado: skill_id 2457 nao existe no catalogo fisico';
  end if;
end
$guard$;

update clube_novo.habilidade_jogo
set nome_en = 'Rapid Trigger Finish',
    nome_pt = 'Chute súbito',
    tipo = 'especial',
    bit_na_carta = 639,
    cartas = 3,
    efeito = jsonb_build_object('6', jsonb_build_object('pct', 5)),
    codigo_casa = 'rapidTriggerFinish',
    fabricavel = false,
    so_goleiro = false,
    extras = coalesce(extras, '{}'::jsonb) || jsonb_build_object(
      'descricao_pt', 'Permite executar o chute mais rapidamente, reduzindo o tempo ate o contato com a bola.',
      'descricao_fonte', 'semantica confirmada na tela do jogo em 05/09/2026; texto fisico localizado permanece pendente',
      'mapeamento_fisico', jsonb_build_object(
        'arquivo', 'Player.bin',
        'papel_fonte', 'dt870_updated',
        'bit_inicio', 639,
        'largura_bits', 1,
        'cards_com_bit', jsonb_build_array(
          '88045755960771', '88045755960841', '88045755964138'
        )
      )
    ),
    novo_2027 = true,
    efeito_por_codigo = jsonb_build_object(
      'PB:530:6', jsonb_build_object('pct', 5)
    ),
    efeito_legivel = 'Finalização +5%',
    vetada = false,
    vetada_motivo = null,
    so_de_linha = true,
    acessorio = false,
    nome_no_motor = 'Chute súbito',
    efeito_desconhecido = false,
    bit_desconhecido = false,
    pode_rodar = true,
    falta_o_que = null
where skill_id = 2457;

insert into clube_novo.contrato_leitura_campo (
  contrato_id, arquivo_id, chave_campo, entidade_destino, tipo_leitura,
  bit_inicio, largura_bits, endianness, transformacao,
  catalogo_schema, catalogo_tabela, catalogo_chave, requisito,
  proveniencia_mapa_assunto, prova, status_prova, ativo,
  chave_familia, expected_type, normalizador_id, versao_normalizador,
  schema_payload, identidade_estavel, fk_destino, nulidade,
  serializacao_saida
)
values (
  'clubef-dt870-2026-r1', 1, 'carta.habilidade.2457',
  'carta_habilidade_jogo.skill_id', 'bitfield_le',
  639, 1, 'little', jsonb_build_object('skill_id', 2457),
  'clube_novo', 'habilidade_jogo', 'skill_id',
  jsonb_build_object('presente_quando', true),
  'habilidade - na carta',
  'Player.bin bit 639/w1; varredura dt870_updated encontrou somente os cards 88045755960771, 88045755960841 e 88045755964138; skill_id 2457 no PlayerSkill.bin',
  'comprovado', true,
  'relacoes', 'foreign_key', 'catalogo_fk', 'v1',
  jsonb_build_object(
    'raw', 'obrigatorio',
    'versao', 'envelope_campo_v1',
    'normalizado', 'obrigatorio',
    'proveniencia', 'obrigatorio'
  ),
  jsonb_build_object('campo_raiz', 'carta.id', 'catalogo_chave', 'skill_id'),
  null, 'nullable_explicit', 'json'
)
on conflict (contrato_id, chave_campo) do update
set arquivo_id = excluded.arquivo_id,
    entidade_destino = excluded.entidade_destino,
    tipo_leitura = excluded.tipo_leitura,
    byte_offset = null,
    bit_inicio = excluded.bit_inicio,
    largura_bits = excluded.largura_bits,
    largura_bytes = null,
    endianness = excluded.endianness,
    codificacao = null,
    transformacao = excluded.transformacao,
    catalogo_schema = excluded.catalogo_schema,
    catalogo_tabela = excluded.catalogo_tabela,
    catalogo_chave = excluded.catalogo_chave,
    requisito = excluded.requisito,
    proveniencia_mapa_assunto = excluded.proveniencia_mapa_assunto,
    prova = excluded.prova,
    status_prova = excluded.status_prova,
    ativo = excluded.ativo,
    chave_familia = excluded.chave_familia,
    expected_type = excluded.expected_type,
    normalizador_id = excluded.normalizador_id,
    versao_normalizador = excluded.versao_normalizador,
    schema_payload = excluded.schema_payload,
    identidade_estavel = excluded.identidade_estavel,
    fk_destino = excluded.fk_destino,
    nulidade = excluded.nulidade,
    serializacao_saida = excluded.serializacao_saida;

insert into clube_novo.contrato_leitura_envelope_mapeamento (
  destino_id, coluna_destino, campo_id, artefato_fisico, coluna_fisica,
  regra_decomposicao, normalizador_id, versao_normalizador,
  proveniencia, status, ordem_regra, grupo_repeticao
)
select 21, 'skill_id', f.campo_id, 'cartas_fisicas', 'habilidades',
       jsonb_build_object(
         'bit', 639,
         'tipo', 'lista_filtrada_bit',
         'chave', 'skill_id=2457',
         'ordem', 'ordem_fisica',
         'largura', 1
       ),
       'identidade.skill_id', 'v1',
       'Player.bin bit 639/w1; skill_id 2457 no catalogo normalizado',
       'comprovado', 35, 'habilidades_player_bin'
from clube_novo.contrato_leitura_campo f
where f.contrato_id = 'clubef-dt870-2026-r1'
  and f.chave_campo = 'carta.habilidade.2457'
on conflict (destino_id, coluna_destino, campo_id, ordem_regra, grupo_repeticao)
do update
set artefato_fisico = excluded.artefato_fisico,
    coluna_fisica = excluded.coluna_fisica,
    regra_decomposicao = excluded.regra_decomposicao,
    normalizador_id = excluded.normalizador_id,
    versao_normalizador = excluded.versao_normalizador,
    proveniencia = excluded.proveniencia,
    status = excluded.status;

-- Reconstroi a ordem fisica de todas as habilidades a partir do bit. Assim a
-- nova habilidade ocupa a posicao 35 e as posteriores avancam uma casa sem
-- criar uma segunda fonte de ordenacao.
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

-- Mantem as ordens normalizadas existentes coerentes com o contrato fisico.
-- A passagem temporaria por +1000 evita colisao no indice unico (card_id,
-- ordem) enquanto uma sequencia densa avanca uma casa dentro da transacao.
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

insert into clube_novo.carta_habilidade_jogo (card_id, skill_id, ordem)
values
  ('88045755960771', 2457, 35),
  ('88045755960841', 2457, 35),
  ('88045755964138', 2457, 35)
on conflict (card_id, skill_id) do update set ordem = excluded.ordem;

update clube_novo.contrato_leitura_jogo
set versao_contrato = 'r5-habilidade-chute-subito-bit639-v1',
    fingerprint_contrato_sha256 =
      clube_novo.fingerprint_material_contrato_leitura(contrato_id),
    validado_em = clock_timestamp()
where contrato_id = 'clubef-dt870-2026-r1';

do $readback$
declare
  v_regua jsonb;
begin
  if (select count(*) from clube_novo.carta_habilidade_jogo where skill_id = 2457) <> 3 then
    raise exception 'Readback Chute subito falhou: quantidade de cartas diferente de 3';
  end if;

  if exists (
    select 1
    from clube_novo.carta_habilidade_jogo
    where skill_id = 2457
      and card_id not in ('88045755960771','88045755960841','88045755964138')
  ) then
    raise exception 'Readback Chute subito falhou: relacao criada para card nao comprovado';
  end if;

  if not exists (
    select 1
    from clube_novo.contrato_leitura_campo f
    join clube_novo.contrato_leitura_envelope_mapeamento m on m.campo_id = f.campo_id
    where f.contrato_id = 'clubef-dt870-2026-r1'
      and f.chave_campo = 'carta.habilidade.2457'
      and f.bit_inicio = 639
      and f.largura_bits = 1
      and f.status_prova = 'comprovado'
      and f.ativo
      and m.destino_id = 21
      and m.ordem_regra = 35
      and m.status = 'comprovado'
  ) then
    raise exception 'Readback Chute subito falhou: contrato/envelope fisico divergente';
  end if;

  if not exists (
    select 1 from clube_novo.habilidade_jogo
    where skill_id = 2457
      and nome_pt = 'Chute súbito'
      and tipo = 'especial'
      and bit_na_carta = 639
      and fabricavel is false
      and efeito = '{"6":{"pct":5}}'::jsonb
      and efeito_por_codigo = '{"PB:530:6":{"pct":5}}'::jsonb
      and efeito_legivel = 'Finalização +5%'
      and efeito_desconhecido is false
      and bit_desconhecido is false
      and pode_rodar
  ) then
    raise exception 'Readback Chute subito falhou: catalogo/efeito do motor divergente';
  end if;

  select public.otimizador_regua_v2() into v_regua;
  if not coalesce((v_regua#>>'{gate,pode_rodar}')::boolean, false) then
    raise exception 'Readback Chute subito falhou: gate do Otimizador fechou: %', v_regua#>'{gate,motivos}';
  end if;
  if not exists (
    select 1
    from jsonb_array_elements(coalesce(v_regua->'habilidades','[]'::jsonb)) h,
         jsonb_array_elements(coalesce(h->'efeitos','[]'::jsonb)) e
    where (h->>'skill_id')::integer = 2457
      and e->>'codigo_atributo' = 'PB:530:6'
      and (e->>'pct')::numeric = 5
      and (e->>'flat')::numeric = 0
  ) then
    raise exception 'Readback Chute subito falhou: regua nao publicou Finalizacao +5%%';
  end if;
end
$readback$;

commit;
