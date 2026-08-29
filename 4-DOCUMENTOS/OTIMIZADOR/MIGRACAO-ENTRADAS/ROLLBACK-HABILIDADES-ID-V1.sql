begin;

drop table if exists clube_novo.habilidade_funcao_incidencia_otimizador;
drop table if exists clube_novo.habilidade_funcao_bloqueio_otimizador;

update clube_novo.habilidade_jogo
set efeito=null, efeito_por_codigo=null, efeito_legivel=null, fabricavel=null,
    efeito_desconhecido=true, pode_rodar=false, falta_o_que='efeito nao apurado',
    extras='{"fonte":"PlayerSkill.bin","fonte_bit":"dt870 atualizacao / Player.bin","vinculo_bit":"805 cartas; presenca exata e unica no bit 676"}'::jsonb
where skill_id=17 and bit_na_carta=676;

update clube_novo.habilidade_jogo
set efeito=null, efeito_por_codigo=null, efeito_legivel=null, fabricavel=null,
    efeito_desconhecido=true, pode_rodar=false, falta_o_que='efeito nao apurado',
    extras='{"fonte":"PlayerSkill.bin","fonte_bit":"dt870 atualizacao / Player.bin","vinculo_bit":"805 cartas; presenca exata e unica no bit 610"}'::jsonb
where skill_id=33 and bit_na_carta=610;

commit;
