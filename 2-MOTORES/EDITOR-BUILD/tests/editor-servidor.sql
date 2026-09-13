begin;
insert into auth.users(id,is_anonymous,aud,role) values
('b688e409-d0b8-4f19-946b-df3d56b3b031',false,'authenticated','authenticated'),
('2177eb7a-7852-4d2c-93c8-e379ae87a551',false,'authenticated','authenticated');
select set_config('request.jwt.claims','{"sub":"b688e409-d0b8-4f19-946b-df3d56b3b031","role":"authenticated"}',true);
do $$
declare input jsonb:='{"card_id":"88045755964138","funcao_id":2,"posicao_id":12,"tecnico_id":"17606144688129","barras":{"shooting":5,"passing":0,"dribbling":8,"dexterity":13,"lowerBodyStrength":10,"aerialStrength":0,"defending":0,"gk1":0,"gk2":0,"gk3":0},"habilidades":[6,5,3,54,56],"impetos":{"2":64},"condicoes":{}}';
 r jsonb; saved jsonb; updated jsonb; receipt jsonb; bad jsonb; count_tests integer:=0; x record; soma numeric:=0; maximo numeric:=0;
begin
 -- Contraexemplo manual: referência 99, proficiência limitada a 99, técnico +1 e ímpeto +4.
 if build_editor.atributo_v1(80,19,1.036,1,4,0,0)->>'jogo'<>'104' then raise exception 'Falha no caso manual Messi 104'; end if;
 if build_editor.atributo_v1(74,0,0.987,0,0,0,0)->>'jogo'<>'74' then raise exception 'Truncamento abaixo de 1 errado'; end if;
 if build_editor.atributo_v1(40,0,0.8,0,0,0,0)->>'jogo'<>'40' then raise exception 'Piso 40 errado'; end if;
 if build_editor.atributo_v1(80,0,1,0,0,7.5,0)->>'sistema'<>'86' then raise exception 'Metade da habilidade arredondada prematuramente'; end if;
 if build_editor.faixa_corpo_v1(7,7,8,9,10)<>-2 or build_editor.faixa_corpo_v1(10,7,8,9,10)<>1 then raise exception 'Limite inclusivo de faixa errado'; end if;
 -- Contra-prova manual independente: Messi função14 soma13/max20 = +0,9750.
 for x in select b.*,c.valor from clube_novo.bonificador_molde_corpo b
 join clube_novo.corpo_ordem o on o.pos=b.corpo_pos
 join clube_novo.carta_corpo_jogo c on c.codigo_corpo=o.codigo and c.card_id='89136409091415'
 where b.funcao_id=14 loop
 if x.direcao<>0 then soma:=soma+build_editor.faixa_corpo_v1(x.valor,x.corte1,x.corte2,x.corte3,x.corte4)*x.direcao*x.peso;maximo:=maximo+2*x.peso;end if;
 end loop;
 if soma<>13 or maximo<>20 or soma/maximo*1.5<>0.975 then raise exception 'Caso físico manual divergente %/%',soma,maximo; end if;
 r:=public.site_novo_editor_avaliar_v1(input);
 if r#>>'{atributos,6,jogo}'<>'90' or r#>>'{atributos,6,sistema}'<>'111'
   or r#>>'{ficha,atributos,6,valor_jogo}'<>'90' or r#>>'{ficha,atributos,6,valor_sistema}'<>'111'
 then raise exception 'Separação jogo/sistema ausente na avaliação ou na projeção pessoal'; end if;
 if abs((r->>'nota_final')::numeric-(9038::numeric/8342*100+2.4857))>0.0000001 or jsonb_array_length(r->'atributos')<>26 or r->'pontos'->>'restantes'<>'0' then raise exception 'Shevchenko: avaliação divergente';end if;
 -- Negativas: servidor recusa campos falsos, custo excedido, posição, nativas, habilidade de goleiro.
 for bad in select unnest(array[
 input||'{"nota_final":999}'::jsonb,
 jsonb_set(input,'{barras,shooting}','6'),
 jsonb_set(input,'{posicao_id}','0'),
 input||'{"habilidades":[6,6]}'::jsonb,
 input||'{"impetos":{"1":64}}'::jsonb,
 input||'{"habilidades":null}'::jsonb,
 input-'barras',
 jsonb_set(input,'{barras,shooting}','-1'),
 jsonb_set(input,'{barras,shooting}','1.5'),
 input||'{"habilidades":[999999]}'::jsonb
 ]) loop
 begin
   perform public.site_novo_editor_avaliar_v1(bad);
   raise exception using errcode='XX000',message='Entrada inválida aceita';
 exception when others then if sqlstate='XX000' then raise;end if; count_tests:=count_tests+1;
 end;
 end loop;
 r:=public.site_novo_editor_gemea_v1(input,6,1);
 if r->'entrada'->'habilidades'<>'[1,5,3,54,56]'::jsonb then raise exception 'Troca múltipla ou alvo errado';end if;
 begin perform public.site_novo_editor_gemea_v1(input,54,1);raise exception using errcode='XX000',message='Gêmea incompatível aceita';exception when others then if sqlstate='XX000' then raise;end if;end;
 saved:=public.site_novo_editor_salvar_v1(input,'Teste transacional',gen_random_uuid());
 if saved->>'revisao'<>'1' or saved->>'numero'<>'1' or saved#>>'{build,nota_final}' is null then raise exception 'Não gravou revisão, número ou projeção';end if;
 if jsonb_array_length(public.site_novo_editor_listar_v1(input->>'card_id'))<>1 then raise exception 'Não listou a build';end if;
 updated:=public.site_novo_editor_salvar_v1(input,'Teste revisado','d8827827-5289-4ac3-90a8-b47bd656fc21',(saved->>'id')::uuid,1);
 receipt:=public.site_novo_editor_salvar_v1(input,'Teste revisado','d8827827-5289-4ac3-90a8-b47bd656fc21',(saved->>'id')::uuid,1);
 if updated<>receipt or updated->>'revisao'<>'2' then raise exception 'Retry não idempotente';end if;
 begin perform public.site_novo_editor_salvar_v1(input,'Obsoleto',gen_random_uuid(),(saved->>'id')::uuid,1);raise exception using errcode='XX000',message='Sobrescreveu revisão obsoleta';exception when serialization_failure then null;end;
 perform set_config('request.jwt.claims','{"sub":"2177eb7a-7852-4d2c-93c8-e379ae87a551","role":"authenticated"}',true);
 if public.site_novo_editor_listar_v1(input->>'card_id')<>'[]' then raise exception 'Vazamento de build entre usuários';end if;
 begin perform public.site_novo_editor_salvar_v1(input,'Roubo',gen_random_uuid(),(saved->>'id')::uuid,2);raise exception using errcode='XX000',message='BOLA: outro dono alterou';exception when insufficient_privilege then null;end;
 begin perform public.site_novo_editor_excluir_v1((saved->>'id')::uuid,2);raise exception using errcode='XX000',message='Outro dono excluiu';exception when insufficient_privilege then null;end;
 perform set_config('request.jwt.claims','{"sub":"b688e409-d0b8-4f19-946b-df3d56b3b031","role":"authenticated"}',true);
 perform public.site_novo_editor_excluir_v1((saved->>'id')::uuid,2);
 if public.site_novo_editor_listar_v1(input->>'card_id')<>'[]' then raise exception 'Excluída ainda listada';end if;
 updated:=public.site_novo_editor_salvar_v1(input,'Segunda',gen_random_uuid());
 if updated->>'numero'<>'2' then raise exception 'Número excluído reutilizado';end if;
 perform set_config('request.jwt.claims','{}',true);
 perform public.site_novo_editor_avaliar_v1(input);
 begin perform public.site_novo_editor_salvar_v1(input,'Sem conta',gen_random_uuid());raise exception using errcode='XX000',message='Anônimo gravou na nuvem';exception when insufficient_privilege then null;end;
end $$;
select 'PASS: casos manuais, Shevchenko, 10 entradas inválidas, gêmeas, save/list/update, retry, revisão, isolamento e anônimo' resultado;
rollback;
