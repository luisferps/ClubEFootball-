-- Executar somente depois de a paridade banco x tela e os gates V2 fecharem zero.
begin;

do $gates$
declare
  v_total integer;
  v_divergencias integer;
  v_pagina_1 integer;
  v_pagina_2 integer;
  v_pagina_3 integer;
begin
  select count(*) into v_total
  from clube_novo.build_pontuacao_final_v2;

  select count(*) into v_divergencias
  from clube_novo.build_pontuacao_normalizada_v2 n
  where abs(n.pontuacao_normalizada_recomputada_evidencia
      - n.pontuacao_otimizador_normalizada) > 0.000000000001
     or abs(n.overall_final_recomputado_evidencia
      - n.overall_final) > 0.000000000001
     or n.bonus_total_bonificador <> round(
       n.bonus_pe + n.bonus_fisico_total + n.bonus_posicao
       + n.bonus_playstyle_1 + n.bonus_playstyle_2 + n.bonus_ia, 4);

  select count(*) into v_pagina_1
  from public.frontend_build_publicada_v2(null, null, 500, 0);
  select count(*) into v_pagina_2
  from public.frontend_build_publicada_v2(null, null, 500, 500);
  select count(*) into v_pagina_3
  from public.frontend_build_publicada_v2(null, null, 500, 1000);

  if v_total <> 613 or v_divergencias <> 0
     or v_pagina_1 <> 500 or v_pagina_2 <> 113 or v_pagina_3 <> 0 then
    raise exception 'PARE: gate V2 recusou total=% divergencias=% paginas=[%,%,%]',
      v_total, v_divergencias, v_pagina_1, v_pagina_2, v_pagina_3;
  end if;
end
$gates$;

grant execute on function public.frontend_build_publicada_v2(text, bigint, integer, integer),
  public.frontend_build_estado_v2(text)
  to anon, authenticated;

notify pgrst, 'reload schema';
commit;
