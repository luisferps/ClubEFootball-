do $$
declare n integer;
begin
 if (select count(*) from clube_novo.tecnico_efhub_20260912)<>65 or exists(
 select 1 from clube_novo.tecnico_efhub_20260912 e left join clube_novo.tecnico_estilo_jogo c
 on c.tecnico_id=e.tecnico_id and c.codigo_estilo='overload'
 where c.tecnico_id is null or c.proficiencia is distinct from e.overload) then
 raise exception 'Referencia manual de Sobreposicao mudou; reconferir'; end if;
 insert into clube_novo.valor_do_dono(destino_schema,destino_tabela,chave,coluna,valor,porque)
 select 'clube_novo','tecnico_estilo_jogo',
 jsonb_build_object('tecnico_id',e.tecnico_id,'codigo_estilo','overload'),v.coluna,v.valor,
 'Correcao manual aprovada por Luis; referencia tecnico_efhub_20260912, reforcada por Coach.bin bit192/w7 em 65/65 tecnicos, SHA256 cb2484b8d29d4d966a22202cf463719c51c968a75f83fad05667263f4955eced. Extrator nao pode sobrescrever.'
 from clube_novo.tecnico_efhub_20260912 e
 cross join lateral (values ('proficiencia',to_jsonb(e.overload)),('confirmado','true'::jsonb)) v(coluna,valor)
 on conflict(destino_schema,destino_tabela,chave,coluna) do nothing;
 get diagnostics n=row_count;
 if n<>130 then raise exception 'Esperadas 130 novas protecoes, recebidas %; reconferir registro existente',n; end if;
end $$;
