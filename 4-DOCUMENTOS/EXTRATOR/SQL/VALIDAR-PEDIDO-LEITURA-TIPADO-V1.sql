begin read only;
select (clube_novo.obter_pedido_leitura_tipado_ativo()->>'contrato_formato')='pedido_leitura_tipado_v1' as formato_correto;
select jsonb_array_length(clube_novo.obter_pedido_leitura_tipado_ativo()->'familias') as familias,
       jsonb_array_length(clube_novo.obter_pedido_leitura_tipado_ativo()->'campos') as campos,
       jsonb_array_length(clube_novo.obter_pedido_leitura_tipado_ativo()->'localizadores_fontes') as localizadores;
rollback;
