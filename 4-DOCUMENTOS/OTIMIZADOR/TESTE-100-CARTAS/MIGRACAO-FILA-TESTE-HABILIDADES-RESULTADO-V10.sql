-- V10: amplia exclusivamente a projeção de leitura V1 com IDs das habilidades
-- já persistidas em build_otimizador. Não altera tabelas, fila, fórmula ou dados.
begin;

create or replace function public.otimizador_fila_teste_v1(p_lote_id uuid)
returns jsonb language sql stable security definer set search_path=''
as $$
select coalesce(jsonb_agg(jsonb_build_object(
 'linha_id',l.id,'card_id',l.card_id,'funcao_id',l.funcao_id,
 'funcao_codigo_compat',f.codigo_legado,'funcao_nome',f.rotulo,
 'posicao_id',l.posicao_id,'posicao_codigo',p.codigo_pt,'posicao_nome',p.nome_pt,
 'ordem_card',l.amostra_ordem,'estado',l.estado_otimizador,
 'carta_versao',l.carta_versao,'carta_fingerprint',l.carta_fingerprint,
 'lote_fingerprint',l.lote_teste_fingerprint,'erro',l.erro_otimizador,
 'b1',b.pontuacao,'pontuacao_final',b.pontuacao,'barras',b.barras,
 'tecnico_id',b.tecnico_id,'habilidades_adicionais',b.habilidades_adicionais,
 'segundos',case when l.otimizador_iniciado_em is not null and l.otimizador_finalizado_em is not null
                 then round(extract(epoch from (l.otimizador_finalizado_em-l.otimizador_iniciado_em))::numeric,2)
            end,
 'otimizador_iniciado_em',l.otimizador_iniciado_em,
 'otimizador_finalizado_em',l.otimizador_finalizado_em
) order by l.amostra_ordem,f.ordem,l.posicao_id),'[]'::jsonb)
from clube_novo.build_linha_card l
join clube_novo.funcao_sistema f on f.id=l.funcao_id
join clube_novo.posicao_jogo p on p.id=l.posicao_id
left join clube_novo.build_otimizador b on b.id=l.build_otimizador_id
where l.lote_teste_id=p_lote_id and l.execucao_tipo='teste_isolado';
$$;

commit;
