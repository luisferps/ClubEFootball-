-- Conferencia somente de leitura; valores esperados derivados da decisao do usuario.
-- Nao usa o resultado da V11 como gabarito. Falha encerra a consulta com erro.
do $testes$
declare
  c record;
  r jsonb;
  v_id integer;
  v_bloqueou boolean;
  v_p jsonb;
begin
  select politica into strict v_p from clube_novo.bonificador_politica_estilo
    where versao='estilos-funcao-20260909-v1';
  if (select count(*) from jsonb_object_keys(v_p->'principal_por_funcao'))<>19
     or (select count(*) from jsonb_each_text(v_p->'principal_por_funcao') where value='defesa')<>6
     or jsonb_array_length(v_p->'excecoes')<>2
     or jsonb_array_length(v_p->'pendentes_ativacao')<>4
     or (v_p->>'promocao_generica_secundario')::boolean then
    raise exception 'A politica registrada diverge da decisao aprovada.';
  end if;
  for c in select * from (values
    ('Shevchenko CA',1,12,257,344,1.0,0.5),
    ('Shevchenko SA',3,11,257,344,0.0,0.5),
    ('Shevchenko PTD',14,10,257,344,0.0,0.5),
    ('Shevchenko MLD',12,7,257,344,0.0,0.0),
    ('Desailly combate',18,1,256,329,0.0,1.0),
    ('Desailly saida',19,1,256,329,0.0,1.0),
    ('Vieira Primeiro Volante nos dois',17,4,392,392,0.5,1.0),
    ('Defensor Criativo combate e Basico',18,1,271,256,1.0,0.0),
    ('Defensor Criativo saida e Basico',19,1,271,256,1.0,0.0),
    ('Defensor Criativo e Destruidor',19,1,271,329,0.5,1.0),
    ('Lateral Defensivo LE e Basico',6,2,268,256,1.0,0.0),
    ('Lateral Defensivo LD e Basico',6,3,268,256,1.0,0.0),
    ('Lateral Defensivo e Cobertura',6,2,268,349,0.5,1.0),
    ('Lateral Defensivo com Destruidor inativo em LD',6,3,268,329,1.0,0.0),
    ('Atacante Surpresa nao e excecao',19,1,266,256,0.5,0.0),
    ('Orquestrador construcao',16,4,276,256,1.0,0.0),
    ('Orquestrador contencao nao herda principal',17,4,276,256,0.5,0.0),
    ('Defensor participativo MLG armador secundario',10,5,256,347,0.0,0.5),
    ('Makelele defensor participativo VOL principal',17,4,256,347,0.0,1.0),
    ('Cech Basico e Goleiro defensivo',4,0,256,337,0.0,1.0),
    ('Gerrard Meia versatil nos dois',11,5,391,391,1.0,0.5),
    ('Basico nos dois',8,8,256,256,0.0,0.0),
    ('Lateral Defensivo inativo em ZC',19,1,268,256,0.0,0.0),
    ('Defensor Criativo inativo em LD',6,3,271,256,0.0,0.0),
    ('Lateral Ofensivo nao e excecao em funcao defensiva',6,2,267,256,0.5,0.0)
  ) as t(nome,funcao,posicao,ataque,defesa,esperado_ataque,esperado_defesa) loop
    r:=clube_novo.conferir_bonus_estilo_0909_v1(c.funcao,c.posicao,c.ataque,c.defesa);
    if not (r->>'pode_calcular')::boolean
       or (r->>'bonus_ataque')::numeric<>c.esperado_ataque
       or (r->>'bonus_defesa')::numeric<>c.esperado_defesa
       or (r->>'bonus_total')::numeric<>c.esperado_ataque+c.esperado_defesa then
      raise exception 'Caso %: esperado ataque %, defesa %, obtido %',
        c.nome,c.esperado_ataque,c.esperado_defesa,r;
    end if;
  end loop;
  foreach v_id in array array[87,95,96,34] loop
    if v_id=34 then
      r:=clube_novo.conferir_bonus_estilo_0909_v1(4,0,v_id,256);
    else
      r:=clube_novo.conferir_bonus_estilo_0909_v1(17,4,256,v_id);
    end if;
    if (r->>'pode_calcular')::boolean or r->>'pendencia'<>'ativacao_sem_definicao'
       or r ? 'bonus_total' then
      raise exception 'Estilo pendente % recebeu resultado em vez de pendencia: %',v_id,r;
    end if;
  end loop;
  v_bloqueou:=false;
  begin
    perform clube_novo.conferir_bonus_estilo_0909_v1(18,1,329,256);
  exception when raise_exception then v_bloqueou:=true;
  end;
  if not v_bloqueou then raise exception 'Destruidor no slot de ataque aceito indevidamente'; end if;
  v_bloqueou:=false;
  begin
    perform clube_novo.conferir_bonus_estilo_0909_v1(17,4,null,392);
  exception when raise_exception then v_bloqueou:=true;
  end;
  if not v_bloqueou then raise exception 'Ausencia de estilo foi convertida em Basico'; end if;
end;
$testes$;

select jsonb_build_object(
  'politica_validada','estilos-funcao-20260909-v1',
  'casos_numericos',25,'estilos_pendentes_verificados',4,'entradas_invalidas_recusadas',2,
  'registro',(select jsonb_build_object('estado',estado,'fingerprint',politica_fingerprint,
    'aprovada_em',aprovada_em,'registrada_em',registrada_em)
    from clube_novo.bonificador_politica_estilo where versao='estilos-funcao-20260909-v1'),
  'regua_operacional_apta',public.bonificador_regua_v3()->'pode_rodar',
  'regua_operacional_fingerprint',public.bonificador_regua_v3()->>'contrato_fingerprint',
  'politica_ligada_a_producao',false
) as resultado;
