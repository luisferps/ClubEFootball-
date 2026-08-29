-- Validação somente leitura após a migração.
begin transaction read only;
select current_setting('transaction_read_only') as transaction_read_only;
select count(*) total, count(distinct id) ids_unicos,
       count(*) filter (where idade is not null) com_idade,
       count(*) filter (where codigo_nacionalidade is not null) com_nacionalidade,
       count(*) filter (where codigo_afinidade is not null) com_afinidade,
       min(idade) idade_min, max(idade) idade_max
from clube_novo.tecnico_jogo;
select count(*) nacionalidades, count(distinct codigo_jogo) codigos_unicos from clube_novo.nacionalidade_jogo;
select count(*) afinidades, count(*) filter (where rotulo_confirmado) rotulos_confirmados from clube_novo.afinidade_tecnico_jogo;
select codigo_afinidade,count(*) from clube_novo.tecnico_jogo where codigo_afinidade is not null group by codigo_afinidade order by codigo_afinidade;
select t.id,t.nome_en,t.idade,t.codigo_nacionalidade,n.nome_pt_br,n.sigla,t.codigo_afinidade,a.nome_pt,a.nome_tela,
       t.arquivo_campos_apresentacao,t.registro_campos_apresentacao,t.hash_campos_apresentacao
from clube_novo.tecnico_jogo t
left join clube_novo.nacionalidade_jogo n on n.codigo_jogo=t.codigo_nacionalidade
left join clube_novo.afinidade_tecnico_jogo a on a.codigo_jogo=t.codigo_afinidade
where t.id in (17601044514701,17601312850052,17608292273375,17609097478250)
order by t.id;
select * from clube_novo.mapa_do_jogo where assunto = any(array['tecnico.idade','tecnico.nacionalidade','tecnico.afinidade','nacionalidade.codigo','nacionalidade.nome_pt_br','nacionalidade.sigla','afinidade_tecnico.rotulo.codigo_5']) order by assunto;
rollback;
