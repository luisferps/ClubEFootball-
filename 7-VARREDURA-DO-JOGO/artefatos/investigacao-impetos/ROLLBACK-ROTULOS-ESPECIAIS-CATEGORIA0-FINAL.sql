-- Rollback dos rótulos especiais categoria 0; gerado antes da transação.
begin;
update clube_novo.impeto_jogo set nome_pt='Bearer of Fate', falta_o_que='id_texto; secao_texto' where codigo_jogo=56;
update clube_novo.impeto_jogo set nome_pt='Son of God', falta_o_que='id_texto; secao_texto; rotulo_operacional_confirmado_usuario; especial_exclusivo_nao_replicavel; ponte_fisica_texto_codigo_pendente' where codigo_jogo=57;
update clube_novo.impeto_jogo set nome_pt='King of Football', falta_o_que='id_texto; secao_texto; rotulo_operacional_confirmado_usuario; especial_exclusivo_nao_replicavel; ponte_fisica_texto_codigo_pendente' where codigo_jogo=58;
update clube_novo.impeto_jogo set nome_pt='The Undisputed', falta_o_que='id_texto; secao_texto; rotulo_operacional_confirmado_usuario; especial_exclusivo_nao_replicavel; ponte_fisica_texto_codigo_pendente' where codigo_jogo=134;
update clube_novo.impeto_jogo set nome_pt='Le Petit Prince', falta_o_que='id_texto; secao_texto; rotulo_operacional_confirmado_usuario; especial_exclusivo_nao_replicavel; ponte_fisica_texto_codigo_pendente' where codigo_jogo=135;
update clube_novo.impeto_jogo set nome_pt='Magical', falta_o_que='id_texto; secao_texto' where codigo_jogo=142;
update clube_novo.impeto_jogo set nome_pt='Striking', falta_o_que='id_texto; secao_texto; rotulo_operacional_confirmado_usuario; especial_exclusivo_nao_replicavel; ponte_fisica_texto_codigo_pendente' where codigo_jogo=143;
update clube_novo.impeto_jogo set nome_pt='Natural-Born', falta_o_que='id_texto; secao_texto; rotulo_operacional_confirmado_usuario; especial_exclusivo_nao_replicavel; ponte_fisica_texto_codigo_pendente' where codigo_jogo=144;
update clube_novo.impeto_jogo set nome_pt='Controle de bola', falta_o_que='id_texto; secao_texto; rotulo_operacional_confirmado_usuario; especial_exclusivo_nao_replicavel; ponte_fisica_texto_codigo_pendente' where codigo_jogo=250;
update clube_novo.impeto_jogo set nome_pt=null, falta_o_que='nome_pt; id_texto; secao_texto' where codigo_jogo=261;
update clube_novo.impeto_jogo set nome_pt='Velocidade', falta_o_que='id_texto; secao_texto' where codigo_jogo=263;
update clube_novo.impeto_jogo set nome_pt='Contato físico', falta_o_que='id_texto; secao_texto; rotulo_operacional_confirmado_usuario; especial_exclusivo_nao_replicavel; ponte_fisica_texto_codigo_pendente' where codigo_jogo=265;
update clube_novo.impeto_jogo set nome_pt='Equilíbrio', falta_o_que='id_texto; secao_texto; rotulo_operacional_confirmado_usuario; especial_exclusivo_nao_replicavel; ponte_fisica_texto_codigo_pendente' where codigo_jogo=266;
update clube_novo.impeto_jogo set nome_pt='Salto', falta_o_que='id_texto; secao_texto' where codigo_jogo=267;
commit;
