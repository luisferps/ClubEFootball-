-- Correção autorizada: acrescentar somente estas linhas antes da fila existente.
-- Históricos preservados em eventos e Builds; nenhuma ordem antiga é reescrita.
begin;
set local statement_timeout='120s';
set local lock_timeout='10s';
do $correcao$
declare
 v_lote_novo uuid:=gen_random_uuid(); v_lote_legado uuid:=gen_random_uuid();
 v_formula constant text:='5a7446b3dfa7b6b45ece1f611b1751fc1221f06e76c53cbd0827a83962c76e89';
 v_motor constant text:='otimizador-fila-producao-v3-local-20260903-goleiro-e-condicional-v11';
 v_agora timestamptz:=clock_timestamp();
 v_regua jsonb; v_contrato_fp text; v_fingerprint text;
 v_linhas int:=1222; v_cartas int; v_afetadas int; v_publicas int;
 v_antes text; v_depois text;
begin
 if exists(select 1 from clube_novo.otimizador_evento_producao_v3 where detalhe->>'contrato'='correcao_volta_marcar_0809_v1') then raise exception 'Correção já aplicada'; end if;
 create temp table _ids_volta on commit drop as select unnest(array[2543,2544,2553,2554,2577,2578,2579,2601,2602,2653,2654,2785,2786,2880,2881,2982,2983,2985,3039,6375,6376,9110,9112,9126,9128,13874,13876,13892,19223,19241,19243,19255,19257,19309,19355,19357,19437,19438,19452,23699,23742,23787,23797,23798,23805,23806,23815,23825,27040,27074,27095,27143,27145,27231,27233,27265,27267,27269,27301,27302,27371,27389,27391,30004,30088,30090,30137,30139,30152,30255,30257,31971,31973,31974,32321,32325,32326,32483,32539,32600,32608,32609,32618,32619,32622,32654,32688,32690,32731,32732,32734,33909,34194,34196,34197,34222,34223,34227,34238,34287,34289,34290,34330,34332,34338,34339,34340,34342,34343,34386,34401,34412,34415,34418,34505,34594,34623,34626,34627,34628,34817,34820,34821,34917,34921,34922,34923,34966,34967,34976,34977,36010,36028,36030,36031,36034,36035,36040,36062,36080,36088,36089,36090,36091,36102,36112,36153,36192,36195,36198,36235,36236,36237,36239,36240,36242,36278,36342,36365,36381,36395,36404,36411,36412,36423,36427,36428,36435,36436,36457,36495,36539,36545,36546,36563,36564,36565,36573,36574,36651,36656,36665,36671,36702,36785,36795,36948,36996,37024,37272,37293,37299,37317,37332,37389,37395,37417,37447,37553,37586,37620,37636,37676,37684,37732,37736,37737,37744,37764,37765,37780,37781,37809,37885,37886,37890,37915,37941,37942,37986,37988,38073,38269,38277,38278,38297,38298,39165,39174,39175,39185,39187,39195,39201,39202,39228,39229,39230,39231,39266,39330,39331,39332,39334,39335,39338,39341,39348,39349,39350,39351,342333,342334,342335,342336,342337,342338,342351,342352,342353,342354,342355,342356,359386,359387,363888,363889,363890,363990,363991,363996,363997,363998,364038,364039,364040,364086,364087,364088,364089,364090,364091,364104,364105,364106,364107,364108,364109,364116,364117,364118,364155,364156,364157,364176,364177,364178,364182,364183,364184,364206,364207,364208,364209,364210,364211,364233,364234,364235,364290,364291,364292,364308,364314,364315,364316,364350,364351,364352,364401,364402,364403,364404,364405,364406,364422,364423,364424,364470,364471,364472,364476,364477,364478,364524,364548,364549,364550,364608,364610,364660,364661,364728,364729,364730,364794,364795,364796,364800,364801,364802,364854,364855,364856,364908,364909,364910,364962,364963,364964,364965,364966,364967,364986,364987,364988,365011,365034,365035,365036,365037,365038,365039,365040,365041,365042,365043,365044,365045,365058,365059,365060,365064,365065,365066,365118,365148,365149,365150,365151,365152,365172,365173,365174,365184,365185,365186,365187,365188,365189,365196,365197,365198,365274,365275,365276,365346,365347,365348,365355,365356,365357,365358,365359,365360,365433,365434,365435,365463,365464,365465,365469,365470,365471,365571,365572,365573,365577,365578,365579,365747,365751,365752,365753,365799,365800,365801,365808,365809,365810,365817,365818,365819,365820,365821,365822,365940,365941,365942,365943,365944,365945,365970,365971,365972,366144,366192,366193,366194,366195,366196,366197,366291,366292,366293,366392,366444,366445,366533,366547,366548,366570,366571,366606,366607,366654,366655,366656,366807,366808,366809,366951,366952,366987,366988,366989,366990,366991,366992,367005,367006,367007,367008,367009,367010,367113,367114,367115,367116,367117,367118,367119,367120,367121,367122,367123,367124,367131,367132,367133,367134,367135,367136,367137,367138,367139,367187,367245,367246,367247,367248,367249,367250,367251,367252,367253,367257,367258,367259,367260,367261,367262,367485,367486,367487,367488,367489,367490,367491,367492,367493,367494,367495,367496,367602,367603,367604,367620,367621,367625,367632,367633,367680,367681,367682,367686,367687,367688,367719,367720,367721,367740,367741,367742,367764,367765,367766,367803,367804,367805,367833,367834,367835,367836,367837,367838,367851,367852,367853,367854,367855,367856,367863,367864,367865,367866,367867,367868,367956,367957,367958,371164,371165,371166,371167,371168,371193,371194,371195,371208,371209,371210,371211,371212,371213,371253,371254,371255,371295,371296,371297,371307,371308,371309,371310,371311,371312,371319,371320,371321,371628,371629,371630,371631,371632,371633,371646,371647,371648,371652,371653,371654,371655,371656,371657,371751,371752,371753,371754,371755,371756,371766,371767,371817,371818,371819,371820,371821,371822,371871,371872,371873,371874,371875,371876,371877,371878,371879,371880,371881,371882,371883,371885,371886,371888,371907,371908,371909,371910,371911,371912,371913,371914,371915,371919,371920,371921,371973,371974,371975,372097,372098,372207,372209,372231,372232,372233,372267,372268,372339,372340,372341,372347,372375,372376,372377,372495,372496,372497,372501,372502,372503,372582,372583,372584,372726,372727,372728,372918,372919,372920,372948,372949,372950,373026,373027,373028,373215,373216,373217,373218,373219,373220,373290,373291,373292,373302,373303,373304,373305,373306,373307,373407,373408,373409,373608,373609,373610,373611,373612,373613,373614,373615,373616,373626,373627,373628,373629,373630,373631,373848,373849,373850,373890,373891,373892,373893,373894,373895,373944,373945,373946,373968,373969,373970,374124,374125,374126,374130,374131,374132,374133,374134,374135,374136,374145,374146,374148,374149,374150,374151,374152,374153,374547,374548,374549,374551,374552,374901,374902,374903,374904,374905,374906,375033,375034,375035,375039,375040,375041,375042,375043,375044,375045,375046,375047,375051,375052,375053,375075,375076,375124,375125,375126,375127,375128,375139,379168,379169,379170,379171,379172,379173,379196,379197,379929,379937,379988,379989,380048,380049,380165,380329,380353,380361,380367,380369,380381,380531,380532,380535,380561,380569,380573,380574,380585,380586,380592,380593,380594,380607,380608,380628,380682,380684,380696,380698,380803,380806,380819,380827,380829,380830,380833,380834,380853,380854,380855,380861,380862,380867,380885,380886,380899,380900,380939,380941,380953,380954,380957,380983,381001,381015,381016,381030,381032,381044,381046,381060,381078,381080,381092,381142,381144,381183,381184,381187,381188,381202,381216,381217,381223,381228,381236,381238,381258,381274,381282,381283,381286,381298,381312,381320,381330,381332,381348,381350,381362,381363,381415,381416,381426,381429,381433,381441,381450,381516,381517,381520,381529,381537,381571,381572,381573,381575,381599,381600,381626,381663,381664,381705,381715,381718,381719,381755,381757,381758,381780,381786,381787,381800,381802,381803,381805,381820,381829,381876,381907,381927,381929,381935,381971,381973,381991,381996,382054,382055,382068,382086,382087,382092,382093,382101,382117,382118,382132,382133,382134,382135,382136,382175,382184,382189,382190,382193,382195,382196,382197,382198,382207,382208,382209,382219,382220,382246,382268,382288,382298,382315,382330,382333,382335,382336,382388,382399,382400,382401,382402,382403,382418,382453,382466,382470,382471,382472,382479,382497,382498,382516,382536,382550,382551,382835,382836,382854,382856,382881,382937,382947,382955,382957,382993,383011,383012,383042,383078,383079,383080,383081,383084,383104,383106,383122,383157,383159,383185,383187,383188,383189,383195,383196,383197,383198,383205,383207,383208,383209,383211,383227,383243,383251,383279,383280,383282,383283,383303,383326,383338,383339,383341,383355,383356,383357,383387,383419,383420,383437,383449,383457,383458,383459,383461,383467,383468,383494,383495,383508,383509,383523,383525,383526,383537,383538,383551,383552,383559,383560,383561,383562,383581,383582,383595,383596,383616,383634,383636,383637,383640,383641,383664,383665,383666,383668,383669,383670,383671,383684,383685,383686,383688,383702,383704,383705,383716,383718,383732,383786,383787,383788,383835,383843,383861,383879,383880,383888,383902,383922,383923,383926,383927,383949,383953,383954,383955,383996,383997,384016,384017,384020,384021,384022,384024,384026,384027,384028,384029,384032,384033,384034,384035,384036,384038,384062,384079,384099,384107,384113,384115,384123,384137,384153,384154,384155,384156,384159,384160,384165,384204,384229,384243,384245,384304,384310,384311,384337,384347,384348,384353,384357,384358,384390,384391,384399,384407,384409,384410,384412,384417,384435,384436,384437,384438,384441,384476,384486,384498,403239,403255,403299,403300,403301,403302,403313,403314,403318,403327,403339,403394,403412,403413,403427,403428]::bigint[]) id;
 perform 1 from clube_novo.build_linha_card where id in(select id from _ids_volta) for update;
 if (select count(*) from clube_novo.build_linha_card l join _ids_volta a using(id) where l.estado='pendente' and l.estado_otimizador='concluido' and l.funcao_id in(1,2,6,7,10,11,16,17,18,19))<>1222 then raise exception 'Alvos mudaram'; end if;
 if exists(select 1 from clube_novo.otimizador_lote_producao_linha_v3 q join _ids_volta a on a.id=q.linha_id where q.reserva_token is not null or q.worker_id is not null or q.reservada_em is not null) then raise exception 'Alvo reservado'; end if;
 select md5(string_agg(to_jsonb(q)::text,'|' order by q.lote_id,q.ordem_fila,q.linha_id)) into v_antes from clube_novo.otimizador_lote_producao_linha_v3 q where not exists(select 1 from _ids_volta a where a.id=q.linha_id);
 select public.otimizador_regua_v2() into v_regua;
 v_contrato_fp:=clube_novo.otimizador_producao_contrato_fingerprint_v3(v_regua);
 if not coalesce((v_regua->'gate'->>'pode_rodar')::boolean,false) or (select count(distinct (b->>'funcao_id')::int) from jsonb_array_elements(v_regua->'bloqueios') b where (b->>'skill_id')::int=56 and (b->>'funcao_id')::int in(1,2,6,7,10,11,16,17,18,19))<>10 then raise exception 'Régua inválida'; end if;
 create temp table _cartas_volta on commit drop as
 select c.card_id,c.overall,public.otimizador_carta_v3(c.card_id) entrada_otimizador,c.extraido_em::text carta_versao_bonificador,clube_novo.bonificador_carta_fingerprint_v1(c.card_id) carta_fingerprint_bonificador
 from clube_novo.carta_jogo c where c.card_id in(select distinct l.card_id from clube_novo.build_linha_card l join _ids_volta a using(id));
 if exists(select 1 from _cartas_volta where not coalesce((entrada_otimizador->'gate'->>'pode_rodar')::boolean,false) or carta_versao_bonificador is null or carta_fingerprint_bonificador is null) then raise exception 'Carta sem entrada selada'; end if;
 create temp table _alvo_volta on commit drop as
 select case when q.linha_id is null then v_lote_legado else v_lote_novo end lote_novo,l.id linha_id,l.card_id,q.ordem_fila ordem_origem,coalesce(q.overall_snapshot,c.overall) overall_snapshot,c.entrada_otimizador,
 encode(extensions.digest(convert_to(c.entrada_otimizador::text,'UTF8'),'sha256'),'hex') entrada_fingerprint_nova,
 c.carta_versao_bonificador,c.carta_fingerprint_bonificador,to_jsonb(l) linha_antes,to_jsonb(q) fila_antes,
 (select to_jsonb(a) from clube_novo.build_publicacao_linha_ativa_v1 a where a.linha_id=l.id) ativa_antes,
 (select to_jsonb(d) from clube_novo.build_pontuacao_final_v2_delta_v1 d where d.linha_id=l.id) delta_antes,
 (select to_jsonb(f) from clube_novo.build_finalizacao_fila_v1 f where f.linha_id=l.id) finalizacao_antes
 from clube_novo.build_linha_card l join _ids_volta a using(id) join _cartas_volta c using(card_id)
 left join clube_novo.otimizador_lote_producao_linha_v3 q on q.linha_id=l.id;
 select count(distinct card_id) into v_cartas from _alvo_volta;
 if (select count(*) from _alvo_volta)<>1222 or v_cartas<>480 then raise exception 'Contagem alvo inválida'; end if;
 v_fingerprint:=encode(extensions.digest(convert_to('correcao_volta_marcar_0809_v1:'||v_lote_novo::text||':'||v_contrato_fp,'UTF8'),'sha256'),'hex');
 insert into clube_novo.otimizador_lote_producao_v3(id,contrato,tipo_lote,estado,formula_fingerprint,contrato_fingerprint,motor_versao,regua_snapshot,fingerprint,cards,linhas,excluidas_incompletas,excluidas_impeto_condicional,excluidas_sem_linha,pode_publicar,preparo_total,preparo_concluido,preparo_fingerprint_final,criado_em,atualizado_em)
 select lote_novo,'otimizador_fila_producao_v3','integral','pausado',v_formula,v_contrato_fp,v_motor,v_regua,encode(extensions.digest(convert_to(v_fingerprint||lote_novo::text,'UTF8'),'sha256'),'hex'),count(distinct card_id),count(*),0,0,0,false,count(distinct card_id),count(distinct card_id),v_fingerprint,v_agora,v_agora from _alvo_volta group by lote_novo;
 insert into clube_novo.otimizador_lote_producao_carta_v3(lote_id,card_id,overall_snapshot,entrada_otimizador,entrada_contrato,entrada_fingerprint,carta_versao_bonificador,carta_fingerprint_bonificador)
 select distinct a.lote_novo,a.card_id,a.overall_snapshot,a.entrada_otimizador,'otimizador_entradas_v3',a.entrada_fingerprint_nova,a.carta_versao_bonificador,a.carta_fingerprint_bonificador from _alvo_volta a;
 insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
 select lote_novo,'lote_criado',jsonb_build_object('contrato','correcao_volta_marcar_0809_v1','linhas',count(*),'cartas',count(distinct card_id),'fila_anterior_md5',v_antes,'worker_iniciado',false) from _alvo_volta group by lote_novo;
 insert into clube_novo.otimizador_evento_producao_v3(lote_id,linha_id,evento,detalhe)
 select a.lote_novo,a.linha_id,'preparo_fatia_concluida',jsonb_build_object('contrato','arquivo_linha_antes_volta_0809_v1','linha_antes',a.linha_antes,'fila_antes',a.fila_antes,'publicacao_ativa_antes',a.ativa_antes,'delta_publico_antes',a.delta_antes,'finalizacao_antes',a.finalizacao_antes) from _alvo_volta a;
 delete from clube_novo.build_pontuacao_final_v2_delta_v1 d using _alvo_volta a where d.linha_id=a.linha_id;
 delete from clube_novo.build_publicacao_linha_ativa_v1 p using _alvo_volta a where p.linha_id=a.linha_id;
 get diagnostics v_publicas=row_count;
 if v_publicas<>1201 then raise exception 'Publicações mudaram: %',v_publicas; end if;
 delete from clube_novo.otimizador_lote_producao_linha_v3 q using _alvo_volta a where q.linha_id=a.linha_id;
 get diagnostics v_afetadas=row_count;
 if v_afetadas<>1215 then raise exception 'Fila antiga mudou: %',v_afetadas; end if;
  update clube_novo.build_linha_card l
     set lote_producao_id = a.lote_novo,
         build_otimizador_id = null,
         build_bonificador_id = null,
         estado_otimizador = 'pendente',
         erro_otimizador = null,
         otimizador_iniciado_em = null,
         otimizador_finalizado_em = null,
         lote_estado = 'pausado',
         lote_estado_atualizado_em = v_agora,
         lote_falha = null,
         otimizador_formula_fingerprint_esperado = v_formula,
         otimizador_contrato_fingerprint_esperado = v_contrato_fp,
         otimizador_motor_versao_esperada = v_motor,
         pendencias = '{}'::text[],
         publicacao_fingerprint = null,
         publicada_em = null,
         atributos_snapshot = null,
         atributos_snapshot_fingerprint = null,
         snapshot_otimizador_fingerprint = null,
         snapshot_bonificador_fingerprint = null,
         otimizador_motor_versao = null,
         otimizador_contrato_versao = null,
         bonificador_motor_versao = null,
         bonificador_contrato_versao = null,
         bonificador_lote_publicacao_id = null,
         nota_contrato = null,
         nota_otimizador_resultado_fingerprint = null,
         nota_bonificador_resultado_fingerprint = null,
         nota_carta_fingerprint = null,
         nota_formula_fingerprint = null,
         nota_contrato_fingerprint = null,
         nota_bruta_selada = null,
         nota_bonus_pe = null,
         nota_bonus_fisico_total = null,
         nota_bonus_posicao = null,
         nota_bonus_playstyle_1 = null,
         nota_bonus_playstyle_2 = null,
         nota_bonus_ia = null,
         nota_bonus_outros = null,
         nota_bonus_total = null,
         nota_numerador = null,
         nota_denominador = null,
         nota_do_motor = null,
         nota_final = null,
         nota_normalizacao_fingerprint = null,
         nota_calculo_fingerprint = null,
         nota_publicacao_fingerprint_v1 = null,
         nota_publicada_em_v1 = null,
         nota_calculada_em = null
  from _alvo_volta a
  where l.id = a.linha_id;
  get diagnostics v_afetadas = row_count;
  if v_afetadas <> v_linhas then
    raise exception 'Volta para marcar recusada: foram reabertas % linhas, esperadas %', v_afetadas, v_linhas;
  end if;


 insert into clube_novo.otimizador_lote_producao_linha_v3(lote_id,linha_id,card_id,ordem_fila,overall_snapshot,entrada_fingerprint,reserva_token,worker_id,reservada_em,finalizada_em,tentativas,resultado_fingerprint)
 select a.lote_novo,a.linha_id,a.card_id,row_number() over(partition by a.lote_novo order by a.linha_id),a.overall_snapshot,a.entrada_fingerprint_nova,null,null,null,null,0,null from _alvo_volta a;
 insert into clube_novo.build_finalizacao_fila_v1(linha_id,estado,prioridade,overall_origem,tentativas,origem_ultima,motivo,proxima_tentativa_em,ultima_tentativa_em,concluido_em,publicacao_fingerprint,atualizado_em)
 select linha_id,'aguardando',0,overall_snapshot,coalesce((finalizacao_antes->>'tentativas')::int,0),'correcao_volta_marcar_0809_v1','Aguardando recálculo do Otimizador sem adicional bloqueado',v_agora+interval '5 minutes',null,null,null,v_agora from _alvo_volta
 on conflict(linha_id) do update set estado='aguardando',origem_ultima=excluded.origem_ultima,motivo=excluded.motivo,proxima_tentativa_em=excluded.proxima_tentativa_em,ultima_tentativa_em=null,concluido_em=null,publicacao_fingerprint=null,atualizado_em=excluded.atualizado_em;
 update clube_novo.otimizador_lote_producao_v3 t set linhas=(select count(*) from clube_novo.otimizador_lote_producao_linha_v3 q where q.lote_id=t.id),atualizado_em=v_agora where t.id in(select distinct (fila_antes->>'lote_id')::uuid from _alvo_volta where fila_antes is not null);
 select md5(string_agg(to_jsonb(q)::text,'|' order by q.lote_id,q.ordem_fila,q.linha_id)) into v_depois from clube_novo.otimizador_lote_producao_linha_v3 q where not exists(select 1 from _ids_volta a where a.id=q.linha_id);
 if v_antes is distinct from v_depois then raise exception 'Fila anterior alterada'; end if;
 if (select count(*) from clube_novo.build_linha_card where lote_producao_id in(v_lote_novo,v_lote_legado) and estado_otimizador='pendente')<>1222 or exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 p join _ids_volta a on a.id=p.linha_id) then raise exception 'Readback falhou'; end if;
end $correcao$;
commit;
select e.lote_id,e.detalhe,(select count(*) from clube_novo.otimizador_fila_prioridade_v1 q where q.lote_id=e.lote_id) linhas_aptas from clube_novo.otimizador_evento_producao_v3 e where e.detalhe->>'contrato'='correcao_volta_marcar_0809_v1';
