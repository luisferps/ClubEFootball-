-- V53: prazo exclusivo da fotografia inicial local.
--
-- V52 removeu as recontagens e OFFSETs que causavam timeout. Estas três
-- funções continuam normalmente rápidas, mas a primeira leitura em uma
-- conexão fria não pode ser cancelada pelo limite padrão de 8 segundos da
-- Data API. O limite de 30 s vale somente dentro das RPCs de download;
-- não muda prazo global, cálculo, worker, fila, publicação ou resultados.

begin;

alter function public.otimizador_producao_pacote_local_manifesto_v2(uuid)
  set statement_timeout to '30s';
alter function public.otimizador_producao_pacote_local_cartas_v2(uuid, text, integer)
  set statement_timeout to '30s';
alter function public.otimizador_producao_pacote_local_linhas_v2(uuid, bigint, integer)
  set statement_timeout to '30s';

comment on function public.otimizador_producao_pacote_local_manifesto_v2(uuid) is
  'V53: manifesto V2 com timeout local de 30 s só para fotografia inicial portátil.';
comment on function public.otimizador_producao_pacote_local_cartas_v2(uuid, text, integer) is
  'V53: página de cartas V2 com timeout local de 30 s só para fotografia inicial portátil.';
comment on function public.otimizador_producao_pacote_local_linhas_v2(uuid, bigint, integer) is
  'V53: página de linhas V2 com timeout local de 30 s só para fotografia inicial portátil.';

notify pgrst, 'reload schema';
commit;
