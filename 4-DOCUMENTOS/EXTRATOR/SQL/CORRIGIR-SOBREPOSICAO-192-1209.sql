do $$
declare n integer;
begin
 if not exists(select 1 from clube_novo.contrato_leitura_arquivo where contrato_id='clubef-dt870-2026-r1' and arquivo_id=2 and sha256_arquivo='cb2484b8d29d4d966a22202cf463719c51c968a75f83fad05667263f4955eced') then
 raise exception 'Coach.bin mudou; refazer prova de Sobreposicao'; end if;
 update clube_novo.contrato_leitura_campo set bit_inicio=192,
 prova='Coach.bin SHA256 cb2484b8d29d4d966a22202cf463719c51c968a75f83fad05667263f4955eced; registros 176 bytes; bit192/w7 unsigned little-endian; 65/65 tecnicos de tecnico_efhub_20260912 conferidos em 12/09/2026; bit135 rejeitado 0/65; Conte 17609097478250=69. Evidencia: 4-DOCUMENTOS/EXTRATOR/SOBREPOSICAO-192-1209.json'
 where contrato_id='clubef-dt870-2026-r1' and campo_id=13 and chave_campo='tecnico.estilo.sobreposicao' and bit_inicio=135 and largura_bits=7;
 get diagnostics n=row_count;
 if n<>1 then raise exception 'Contrato mudou: esperado exatamente um campo antigo'; end if;
end $$;

-- O leitor tipado também consulta este catálogo. Correção executada e relida.
update clube_novo.estilo_jogo_tecnico set bit=192, confirmado_em=clock_timestamp() where codigo='overload' and bit=135 and largura=7;
select codigo,bit,largura from clube_novo.estilo_jogo_tecnico where codigo='overload';
