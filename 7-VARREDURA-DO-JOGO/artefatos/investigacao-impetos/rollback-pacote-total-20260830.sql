-- Rollback cirurgico da etiqueta operacional monitorada "Pacote total".
-- Alvo exclusivo: clube_novo.impeto_jogo, codigos 96,101,132,133,170,171,208.
-- O guard impede desfazer uma alteracao posterior diferente desta revisao.
begin;

update clube_novo.impeto_jogo
   set nome_pt = 'Total Package',
       falta_o_que = 'id_texto; secao_texto'
 where codigo_jogo in (96, 101, 132, 133, 170, 171, 208)
   and nome_pt = 'Pacote total'
   and falta_o_que = 'rotulo_operacional_monitorado; confirmacao_visual_usuario; padrao_fisico_26_atributos_condicional; ponte_textual_oficial_secao_texto_id_texto_pendente'
   and secao_texto is null
   and id_texto is null;

-- Antes de confirmar o rollback, o operador deve validar que ROW_COUNT = 7.
commit;
