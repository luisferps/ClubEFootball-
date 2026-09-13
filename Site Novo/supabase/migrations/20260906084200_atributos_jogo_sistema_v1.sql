-- Leitura do snapshot publicado: não calcula nem substitui atributos ausentes.
begin;
CREATE OR REPLACE FUNCTION public.site_novo_ficha_base_publicada_v1(p_card_id text DEFAULT NULL::text, p_linha_id bigint DEFAULT NULL::bigint)
 RETURNS jsonb
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
with
entrada as (
  select nullif(btrim(p_card_id), '') as card_id
),
carta as (
  select
    c.card_id,
    c.nome,
    c.foto_url_cloudinary,
    c.box,
    c.level_cap,
    c.orcamento,
    c.altura,
    c.peso,
    c.idade,
    c.resistencia_lesao,
    (c.level_cap = 1 and c.orcamento = 0) as sem_evolucao,
    tc.nome_exibicao as tipo_carta
  from entrada e
  join clube_novo.carta_jogo c
    on c.card_id = e.card_id
  left join clube_novo.tipo_carta_jogo tc
    on tc.tipo_carta_id = c.tipo_carta_id
),
publicadas as (
  select
    l.id,
    l.card_id,
    l.funcao_id,
    l.posicao_id,
    a.build_otimizador_id,
    a.build_bonificador_id,
    a.nota_final,
    a.publicada_em as nota_publicada_em_v1,
    l.impeto_condicional_codigo,
    l.impeto_condicional_nivel,
    bo.tecnico_id,
    bo.barras,
    bo.impeto_adicional_codigo,
    bo.habilidades_adicionais,
    bo.atributos_finais,
    bo.atributos_internos,
    bb.bonus_pe,
    bb.bonus_fisico_total,
    bb.bonus_posicao,
    bb.bonus_playstyle_1,
    bb.bonus_playstyle_2,
    bb.bonus_ia,
    bb.bonus_outros,
    bb.bonus_total,
    bb.bonus_fisico_detalhe
  from entrada e
  join clube_novo.build_linha_card l
    on l.card_id = e.card_id
  join clube_novo.build_publicacao_linha_ativa_v1 a
    on a.linha_id = l.id
  join clube_novo.build_otimizador bo
    on bo.id = a.build_otimizador_id
  join clube_novo.build_bonificador bb
    on bb.id = a.build_bonificador_id
  where l.execucao_tipo = 'producao'
    and l.lote_teste_id is null
    and not (l.pendencias @> array['teste_nao_publicado'::text])
),
selecionada as (
  select p.*
  from publicadas p
  where p_linha_id is null or p.id = p_linha_id
  order by
    p.nota_final desc nulls last,
    case
      when jsonb_typeof(p.atributos_finais) = 'array'
        then jsonb_array_length(p.atributos_finais) = 26
      else false
    end desc,
    p.nota_publicada_em_v1 desc,
    p.id asc
  limit 1
),
contexto as (
  select
    e.card_id as card_id_pedido,
    c.*,
    s.id as linha_id,
    s.funcao_id,
    s.posicao_id,
    s.build_otimizador_id,
    s.build_bonificador_id,
    s.nota_final,
    s.nota_publicada_em_v1,
    s.impeto_condicional_codigo,
    s.impeto_condicional_nivel,
    s.tecnico_id,
    s.barras,
    s.impeto_adicional_codigo,
    s.habilidades_adicionais,
    s.atributos_finais,
    s.atributos_internos,
    s.bonus_pe,
    s.bonus_fisico_total,
    s.bonus_posicao,
    s.bonus_playstyle_1,
    s.bonus_playstyle_2,
    s.bonus_ia,
    s.bonus_outros,
    s.bonus_total,
    s.bonus_fisico_detalhe,
    clube_novo.site_novo_fila_atributos_confirmada_v1(e.card_id)
      as fila_atributos_confirmada,
    case
      when jsonb_typeof(s.atributos_finais) = 'array'
        then jsonb_array_length(s.atributos_finais) = 26
      else false
    end as atributos_completos
  from entrada e
  left join carta c on true
  left join selecionada s on true
)
select jsonb_build_object(
  'contrato', 'site-novo-ficha-v1',
  'versao', 1,
  'status',
    case
      when x.card_id_pedido is null then 'parametro_ausente'
      when x.card_id is null then 'card_nao_encontrado'
      when x.linha_id is null and p_linha_id is not null then 'linha_nao_encontrada_ou_nao_publicada'
      when x.linha_id is null then 'card_sem_build_publicada'
      when not x.atributos_completos and x.fila_atributos_confirmada
        then 'atributos_em_atualizacao'
      when not x.atributos_completos then 'atributos_aguardando_publicacao'
      else 'pronto'
    end,
  'mensagem',
    case
      when x.card_id_pedido is null then 'Informe o card_id na URL para abrir a Ficha.'
      when x.card_id is null then 'Card não encontrado.'
      when x.linha_id is null and p_linha_id is not null then 'A linha pedida não pertence ao card ou não está publicada.'
      when x.linha_id is null then 'Este card ainda não tem build publicada.'
      when not x.atributos_completos and x.fila_atributos_confirmada
        then 'A nota está publicada e há registro vivo de atualização dos 26 atributos.'
      when not x.atributos_completos
        then 'A nota está publicada; os 26 atributos ainda aguardam publicação.'
      else 'Ficha pronta.'
    end,
  'card_id', x.card_id_pedido,
  'dados',
    case
      when x.card_id is null then null
      else jsonb_build_object(
        'card', jsonb_build_object(
          'card_id', x.card_id,
          'nome', x.nome,
          'foto_url', x.foto_url_cloudinary,
          'box', x.box,
          'tipo_carta', x.tipo_carta,
          'no_elenco', null,
          'estilo_jogo', (
            select ps.nome_tela
            from clube_novo.carta_playstyle_jogo cp
            join clube_novo.playstyle ps
              on ps.id_jogo = cp.playstyle_id
            where cp.card_id = x.card_id
              and cp.slot_fisico = 1
            order by cp.slot_fisico, ps.id_jogo
            limit 1
          ),
          'posicao_nativa', (
            select jsonb_build_object(
              'id', pj.id,
              'codigo', pj.codigo_pt,
              'nome', pj.nome_pt
            )
            from clube_novo.carta_posicao_principal_jogo cpp
            join clube_novo.posicao_jogo pj
              on pj.id = cpp.posicao_id
            where cpp.card_id = x.card_id
            order by cpp.posicao_id
            limit 1
          ),
          'posicoes', (
            select coalesce(
              jsonb_agg(
                jsonb_build_object(
                  'id', pj.id,
                  'codigo', pj.codigo_pt,
                  'nome', pj.nome_pt,
                  'nivel', cp.nivel_aptidao,
                  'principal', cpp.posicao_id is not null,
                  'selecionada', pj.id = x.posicao_id
                )
                order by case pj.codigo_pt
                  when 'PTE' then 1
                  when 'CA' then 2
                  when 'PTD' then 3
                  when 'SA' then 4
                  when 'MLE' then 5
                  when 'MAT' then 6
                  when 'MLD' then 7
                  when 'MLG' then 8
                  when 'VOL' then 9
                  when 'LE' then 10
                  when 'ZC' then 11
                  when 'LD' then 12
                  when 'GO' then 13
                  else 99
                end
              ),
              '[]'::jsonb
            )
            from clube_novo.posicao_jogo pj
            left join clube_novo.carta_posicao_jogo cp
              on cp.card_id = x.card_id
             and cp.posicao_id = pj.id
            left join clube_novo.carta_posicao_principal_jogo cpp
              on cpp.card_id = x.card_id
             and cpp.posicao_id = pj.id
            where pj.codigo_pt in (
              'PTE','CA','PTD','SA','MLE','MAT','MLD','MLG','VOL','LE','ZC','LD','GO'
            )
          ),
          'habilidades_especiais', (
            select coalesce(
              jsonb_agg(
                jsonb_build_object(
                  'id', h.skill_id,
                  'nome', h.nome_pt
                )
                order by ch.ordem nulls last, h.ordem, h.skill_id
              ),
              '[]'::jsonb
            )
            from clube_novo.carta_habilidade_jogo ch
            join clube_novo.habilidade_jogo h
              on h.skill_id = ch.skill_id
            where ch.card_id = x.card_id
              and h.tipo = 'especial'
          ),
          'habilidades_nativas', (
            select coalesce(
              jsonb_agg(
                jsonb_build_object(
                  'id', h.skill_id,
                  'nome', h.nome_pt
                )
                order by ch.ordem nulls last, h.ordem, h.skill_id
              ),
              '[]'::jsonb
            )
            from clube_novo.carta_habilidade_jogo ch
            join clube_novo.habilidade_jogo h
              on h.skill_id = ch.skill_id
            where ch.card_id = x.card_id
              and h.tipo is distinct from 'especial'
          ),
          'estilos_ia', (
            select coalesce(
              jsonb_agg(
                jsonb_build_object(
                  'codigo', ei.codigo,
                  'nome', ei.nome_tela
                )
                order by ei.bit
              ),
              '[]'::jsonb
            )
            from clube_novo.carta_estilo_ia_jogo cei
            join clube_novo.estilo_ia ei
              on ei.bit = cei.bit_estilo_ia
            where cei.card_id = x.card_id
          ),
          'altura_cm', x.altura,
          'peso_kg', x.peso,
          'idade_anos', x.idade,
          'resistencia_lesao', x.resistencia_lesao,
          'pe', (
            select coalesce(
              jsonb_agg(
                jsonb_build_object(
                  'campo', cp.campo,
                  'valor', cp.valor,
                  'codigo', p.codigo,
                  'nome', p.nome_pt
                )
                order by case cp.campo
                  when 'pe_dominante' then 1
                  when 'pe_ruim_uso' then 2
                  when 'pe_ruim_precisao' then 3
                  else 99
                end
              ),
              '[]'::jsonb
            )
            from clube_novo.carta_pe_jogo cp
            join clube_novo.pe p
              on p.campo = cp.campo
             and p.valor = cp.valor
            where cp.card_id = x.card_id
          ),
          'corpo', (
            select coalesce(
              jsonb_agg(
                jsonb_build_object(
                  'codigo', co.codigo,
                  'chave_bonus', co.nosso,
                  'nome', co.nome_pt,
                  'ordem', co.pos,
                  'valor', cc.valor,
                  'bonus', case
                    when x.bonus_fisico_detalhe ? co.nosso
                      then x.bonus_fisico_detalhe -> co.nosso
                    else null
                  end
                )
                order by co.pos
              ),
              '[]'::jsonb
            )
            from clube_novo.carta_corpo_jogo cc
            join clube_novo.corpo_ordem co
              on co.codigo = cc.codigo_corpo
            where cc.card_id = x.card_id
              and co.usado_pelo_motor is true
          )
        ),
        'build', case
          when x.linha_id is null then null
          else jsonb_build_object(
            'linha_id', x.linha_id,
            'nota_final', x.nota_final,
            'nota_publicada_em', x.nota_publicada_em_v1,
            'funcao', (
              select jsonb_build_object(
                'id', fs.id,
                'rotulo', fs.rotulo,
                'sigla', fs.sigla,
                'grupo', fs.grupo,
                'familia', fs.familia
              )
              from clube_novo.funcao_sistema fs
              where fs.id = x.funcao_id
            ),
            'posicao', (
              select jsonb_build_object(
                'id', pj.id,
                'codigo', pj.codigo_pt,
                'nome', pj.nome_pt
              )
              from clube_novo.posicao_jogo pj
              where pj.id = x.posicao_id
            ),
            'nivel_maximo', x.level_cap,
            'orcamento_total', x.orcamento,
            'orcamento_gasto', null,
            'evolucao', jsonb_build_object(
              'estado', case
                when x.sem_evolucao then 'nivel_1_sem_evolucao'
                else 'com_evolucao'
              end,
              'sem_evolucao', x.sem_evolucao
            ),
            'barras', (
              select jsonb_agg(
                jsonb_build_object(
                  'chave', b.chave,
                  'rotulo', b.rotulo,
                  'valor', case
                    when x.barras ? b.chave then x.barras -> b.chave
                    else null
                  end
                )
                order by b.ordem
              )
              from (
                values
                  (1, 'shooting', 'Chute'),
                  (2, 'passing', 'Passe'),
                  (3, 'dribbling', 'Drible'),
                  (4, 'dexterity', 'Destreza'),
                  (5, 'lowerBodyStrength', 'Força pernas'),
                  (6, 'aerialStrength', 'Força aérea'),
                  (7, 'defending', 'Defesa'),
                  (8, 'gk1', 'GO reflexo/salto'),
                  (9, 'gk2', 'GO defesa/alcance'),
                  (10, 'gk3', 'GO encaixe/reflexos')
              ) as b(ordem, chave, rotulo)
            ),
            'tecnico', (
              select jsonb_build_object(
                'id', tj.id,
                'nome', tj.nome_en,
                'atributos', (
                  select coalesce(
                    jsonb_agg(
                      jsonb_build_object(
                        'codigo_atributo', ta.codigo_atributo,
                        'nome', aj.nome_pt,
                        'delta', ta.delta
                      )
                      order by ta.ordem
                    ),
                    '[]'::jsonb
                  )
                  from clube_novo.tecnico_atributo_jogo ta
                  join clube_novo.atributo_jogo aj
                    on aj.codigo = ta.codigo_atributo
                  where ta.tecnico_id = tj.id
                ),
                'estilos', (
                  select coalesce(
                    jsonb_agg(
                      jsonb_build_object(
                        'codigo', te.codigo_estilo,
                        'proficiencia', te.proficiencia
                      )
                      order by te.proficiencia desc, te.codigo_estilo
                    ),
                    '[]'::jsonb
                  )
                  from clube_novo.tecnico_estilo_jogo te
                  where te.tecnico_id = tj.id
                ),
                'alternativo', null,
                'sugeridos', '[]'::jsonb
              )
              from clube_novo.tecnico_jogo tj
              where tj.id = x.tecnico_id
            ),
            'habilidades_adicionadas', (
              select coalesce(
                jsonb_agg(
                  jsonb_build_object(
                    'id', hids.skill_id,
                    'nome', hj.nome_pt
                  )
                  order by hids.ordem
                ),
                '[]'::jsonb
              )
              from unnest(x.habilidades_adicionais) with ordinality
                as hids(skill_id, ordem)
              left join clube_novo.habilidade_jogo hj
                on hj.skill_id = hids.skill_id
            ),
            'habilidades_sugeridas', '[]'::jsonb,
            'impetos', (
              select coalesce(
                jsonb_agg(
                  jsonb_build_object(
                    'slot', ci.slot,
                    'tipo', case when ci.vaga then 'adicional' else 'nativo' end,
                    'vaga_original', ci.vaga,
                    'codigo', fin.codigo,
                    'nome', ij.nome_pt,
                    'condicional', ij.condicional,
                    'condicao_estado', ij.condicao_estado,
                    'condicao_nivel', case
                      when x.impeto_condicional_codigo = fin.codigo
                        then x.impeto_condicional_nivel
                      else null
                    end,
                    'delta_uniforme', (
                      select case
                        when count(*) > 0 and min(ia.delta) = max(ia.delta)
                          then min(ia.delta)
                        else null
                      end
                      from clube_novo.impeto_atributo_jogo ia
                      where ia.codigo_impeto = fin.codigo
                    ),
                    'efeitos', (
                      select coalesce(
                        jsonb_agg(
                          jsonb_build_object(
                            'codigo_atributo', ia.codigo_atributo,
                            'nome', aj.nome_pt,
                            'delta', ia.delta
                          )
                          order by ia.ordem
                        ),
                        '[]'::jsonb
                      )
                      from clube_novo.impeto_atributo_jogo ia
                      join clube_novo.atributo_jogo aj
                        on aj.codigo = ia.codigo_atributo
                      where ia.codigo_impeto = fin.codigo
                    )
                  )
                  order by ci.ordem
                ),
                '[]'::jsonb
              )
              from clube_novo.carta_impeto_jogo ci
              cross join lateral (
                select case
                  when ci.vaga then x.impeto_adicional_codigo
                  else ci.codigo_impeto
                end as codigo
              ) fin
              left join clube_novo.impeto_jogo ij
                on ij.codigo_jogo = fin.codigo
              where ci.card_id = x.card_id
            ),
            'atributos_completos', x.atributos_completos,
            'atualizacao_atributos', jsonb_build_object(
              'estado', case
                when x.atributos_completos then 'completa'
                when x.fila_atributos_confirmada then 'fila_confirmada'
                else 'sem_evidencia_de_fila'
              end,
              'fila_confirmada', x.fila_atributos_confirmada
            ),
            'atributos', (
              select coalesce(
                jsonb_agg(
                  jsonb_build_object(
                    'indice', ao.indice_otimizador,
                    'codigo', ao.codigo_atributo,
                    'nome', aj.nome_pt,
                    'grupo_origem', aj.grupo,
                    'grupo_tela', case
                      when ao.indice_otimizador between 0 and 6
                        or ao.indice_otimizador in (8, 9) then 'ataque'
                      when ao.indice_otimizador in (10, 11, 12, 15, 16) then 'atletismo'
                      when ao.indice_otimizador in (7, 13, 14) then 'fisico'
                      when ao.indice_otimizador between 17 and 20 then 'defesa'
                      when ao.indice_otimizador between 21 and 25 then 'goleiro'
                      else 'outro'
                    end,
                    'valor_base', ca.valor,
                    'valor_pos_evolucao', case
                      when x.sem_evolucao then ca.valor
                      else null
                    end,
                    'valor_final', case
                      when x.atributos_completos
                        then x.atributos_finais -> ao.indice_otimizador
                      else null
                    end,
                    'valor_jogo', case when x.atributos_completos then x.atributos_finais -> ao.indice_otimizador else null end,
                    'valor_sistema', case when jsonb_typeof(x.atributos_internos)='array' then
                      case when jsonb_array_length(x.atributos_internos)=26 then x.atributos_internos -> ao.indice_otimizador else null end
                      else null end,
                    'pontos', null
                  )
                  order by ao.indice_otimizador
                ),
                '[]'::jsonb
              )
              from clube_novo.atributo_ordem_otimizador ao
              join clube_novo.atributo_jogo aj
                on aj.codigo = ao.codigo_atributo
              left join clube_novo.carta_atributo_jogo ca
                on ca.card_id = x.card_id
               and ca.codigo_atributo = ao.codigo_atributo
            ),
            'atributos_total_pontos', null,
            'bonus_ia', x.bonus_ia,
            'bonus_pe', x.bonus_pe,
            'bonus_fisico_total', x.bonus_fisico_total
          )
        end,
        'builds_publicadas', (
          select coalesce(
            jsonb_agg(
              jsonb_build_object(
                'linha_id', p.id,
                'funcao', jsonb_build_object(
                  'id', fs.id,
                  'rotulo', fs.rotulo,
                  'sigla', fs.sigla
                ),
                'posicao', jsonb_build_object(
                  'id', pj.id,
                  'codigo', pj.codigo_pt,
                  'nome', pj.nome_pt
                ),
                'nota_final', p.nota_final,
                'selecionada', p.id = x.linha_id
              )
              order by
                p.nota_final desc nulls last,
                case
                  when jsonb_typeof(p.atributos_finais) = 'array'
                    then jsonb_array_length(p.atributos_finais) = 26
                  else false
                end desc,
                p.nota_publicada_em_v1 desc,
                p.id asc
            ),
            '[]'::jsonb
          )
          from publicadas p
          left join clube_novo.funcao_sistema fs
            on fs.id = p.funcao_id
          left join clube_novo.posicao_jogo pj
            on pj.id = p.posicao_id
        ),
        'builds_publicadas_total', (select count(*) from publicadas),
        'builds_salvas_total', 0,
        'interacoes', jsonb_build_object(
          'referencia_ideal', false,
          'build_atual', false,
          'criar_build', false,
          'ver_mais', false,
          'editar_distribuicao', false,
          'trocar_tecnico', false,
          'editar_habilidades', false,
          'salvar_build', false,
          'alterar_elenco', false
        )
      )
    end
)
from contexto x;
$function$
;
commit;
