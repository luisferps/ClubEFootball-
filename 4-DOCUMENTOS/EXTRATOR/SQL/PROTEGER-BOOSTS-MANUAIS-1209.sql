do $$
declare n integer;
begin
 if (select count(*) from clube_novo.tecnico_atributo_jogo c join clube_novo.tecnico_efhub_20260912 e on e.tecnico_id=c.tecnico_id
 join clube_novo.atributo_jogo a on a.codigo=c.codigo_atributo
 where c.fonte='efhub_manual_20260912' and c.delta=1 and a.nome_pt=case c.ordem when 1 then e.boost1 when 2 then e.boost2 end)<>106 then
 raise exception 'Os 106 boosts manuais precisam ser reconferidos'; end if;
 insert into clube_novo.valor_do_dono(destino_schema,destino_tabela,chave,coluna,valor,porque)
 select 'clube_novo','tecnico_atributo_jogo',jsonb_build_object('tecnico_id',c.tecnico_id,'ordem',c.ordem),
 v.coluna,v.valor,'Correcao manual aprovada por Luis; 106 boosts conferidos por codigo/nome/ordem contra tecnico_efhub_20260912. Proteger contra recarga do Extrator.'
 from clube_novo.tecnico_atributo_jogo c join clube_novo.tecnico_efhub_20260912 e on e.tecnico_id=c.tecnico_id
 cross join lateral(values('codigo_atributo',to_jsonb(c.codigo_atributo)),('delta',to_jsonb(c.delta)),('confirmado','true'::jsonb))v(coluna,valor)
 where c.fonte='efhub_manual_20260912'
 on conflict(destino_schema,destino_tabela,chave,coluna) do nothing;
 get diagnostics n=row_count;
 if n<>318 then raise exception 'Esperadas 318 protecoes, recebidas %',n; end if;
end $$;
