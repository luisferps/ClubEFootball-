-- Dependências de catálogos declaradas pela família: nenhuma lista local é
-- usada para completar o pedido. Não grava dados extraídos do jogo.
begin;

alter table clube_novo.contrato_leitura_familia
  add column if not exists catalogos_requeridos jsonb not null default '[]'::jsonb;

update clube_novo.contrato_leitura_familia
set catalogos_requeridos=case chave_familia
  when 'dimensoes' then '[{"schema":"clube_novo","tabela":"nacionalidade_jogo","chave":"codigo_jogo"},{"schema":"clube_novo","tabela":"clube_jogo","chave":"codigo_jogo"},{"schema":"clube_novo","tabela":"liga_jogo","chave":"codigo_jogo"},{"schema":"clube_novo","tabela":"tipo_carta_jogo","chave":"tipo_carta_id"}]'::jsonb
  when 'tecnicos' then '[{"schema":"clube_novo","tabela":"estilo_jogo_tecnico","chave":"codigo"},{"schema":"clube_novo","tabela":"afinidade_tecnico_jogo","chave":"codigo_jogo"},{"schema":"clube_novo","tabela":"atributo_ordem_otimizador","chave":"indice_otimizador"}]'::jsonb
  when 'impetos' then '[{"schema":"clube_novo","tabela":"impeto_jogo","chave":"codigo_jogo"},{"schema":"clube_novo","tabela":"impeto_atributo_jogo","chave":"codigo_impeto,codigo_atributo"},{"schema":"clube_novo","tabela":"impeto_condicao_jogo","chave":"codigo_impeto"},{"schema":"clube_novo","tabela":"impeto_condicao_liga_membro_jogo","chave":"codigo_liga_alvo_base,codigo_liga_membro"},{"schema":"clube_novo","tabela":"tipo_impeto_jogo","chave":"codigo_raw"}]'::jsonb
  when 'relacoes' then '[{"schema":"clube_novo","tabela":"atributo_jogo","chave":"codigo"},{"schema":"clube_novo","tabela":"posicao_jogo","chave":"id"},{"schema":"clube_novo","tabela":"playstyle","chave":"id_jogo"}]'::jsonb
  else '[]'::jsonb
end,
proveniencia=proveniencia||'; dependências de catálogo declaradas no contrato'
where contrato_id='clubef-dt870-2026-r1';

commit;
