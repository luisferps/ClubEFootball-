-- Contrato tipado de descoberta do Extrator. Não grava dados do jogo.
begin;

create table if not exists clube_novo.contrato_leitura_familia (
  familia_id bigint generated always as identity primary key,
  contrato_id text not null references clube_novo.contrato_leitura_jogo(contrato_id) on delete restrict,
  chave_familia text not null,
  leitor_id text not null,
  versao_leitor text not null,
  schema_payload jsonb not null,
  tipo_saida text not null,
  normalizador_id text not null,
  versao_normalizador text not null,
  identidade jsonb not null,
  papeis_fonte jsonb not null,
  comparacao_ativa boolean not null default true,
  obrigatoria boolean not null default true,
  proveniencia text not null,
  unique (contrato_id, chave_familia),
  check (btrim(chave_familia) <> ''),
  check (btrim(leitor_id) <> ''),
  check (btrim(versao_leitor) <> ''),
  check (btrim(tipo_saida) <> ''),
  check (btrim(normalizador_id) <> ''),
  check (btrim(versao_normalizador) <> ''),
  check (jsonb_typeof(schema_payload) = 'object'),
  check (jsonb_typeof(identidade) = 'object'),
  check (jsonb_typeof(papeis_fonte) = 'array')
);

create table if not exists clube_novo.contrato_leitura_fonte_localizador (
  localizador_id bigint generated always as identity primary key,
  contrato_id text not null references clube_novo.contrato_leitura_jogo(contrato_id) on delete restrict,
  papel_fonte text not null,
  ordem smallint not null default 1,
  template_caminho text not null,
  plataforma text not null default 'windows',
  obrigatorio boolean not null default true,
  proveniencia text not null,
  unique (contrato_id, papel_fonte, ordem),
  check (ordem > 0),
  check (btrim(template_caminho) <> ''),
  check (btrim(plataforma) <> '')
);

create table if not exists clube_novo.contrato_leitura_expectativa (
  expectativa_id bigint generated always as identity primary key,
  contrato_id text not null references clube_novo.contrato_leitura_jogo(contrato_id) on delete restrict,
  chave_familia text not null,
  chave_metrica text not null,
  valor_esperado bigint not null,
  comparador text not null default 'igual',
  obrigatoria boolean not null default true,
  proveniencia text not null,
  unique (contrato_id, chave_familia, chave_metrica),
  check (valor_esperado >= 0),
  check (comparador in ('igual','minimo','maximo')),
  check (btrim(chave_familia) <> ''),
  check (btrim(chave_metrica) <> '')
);

alter table clube_novo.contrato_leitura_arquivo
  add column if not exists leitor_id text,
  add column if not exists versao_leitor text,
  add column if not exists formato_saida text,
  add column if not exists tipo_saida text,
  add column if not exists serializacao_saida text;

alter table clube_novo.contrato_leitura_campo
  add column if not exists chave_familia text,
  add column if not exists expected_type text,
  add column if not exists normalizador_id text,
  add column if not exists versao_normalizador text,
  add column if not exists schema_payload jsonb,
  add column if not exists identidade_estavel jsonb,
  add column if not exists fk_destino text,
  add column if not exists nulidade text,
  add column if not exists serializacao_saida text;

update clube_novo.contrato_leitura_arquivo
set leitor_id = case decodificador when 'wesys_raw' then 'wesys_raw' when 'all_str_v1' then 'all_str_v1' else decodificador end,
    versao_leitor = coalesce(versao_leitor, 'v1'),
    formato_saida = coalesce(formato_saida, 'envelope_familia_v1'),
    tipo_saida = coalesce(tipo_saida, case when decodificador='all_str_v1' then 'objeto_textual' else 'registro_fisico' end),
    serializacao_saida = coalesce(serializacao_saida, 'json');

update clube_novo.contrato_leitura_campo
set chave_familia = coalesce(chave_familia, case split_part(chave_campo,'.',1)
  when 'carta' then case
    when entidade_destino like 'carta_atributo_jogo%' or entidade_destino like 'carta_corpo_jogo%' or entidade_destino like 'carta_habilidade_jogo%' or entidade_destino like 'carta_estilo_ia_jogo%' or entidade_destino like 'carta_posicao_jogo%' or entidade_destino like 'carta_posicao_principal_jogo%' or entidade_destino like 'carta_playstyle_jogo%' then 'relacoes'
    when entidade_destino like 'carta_impeto_jogo%' then 'impetos'
    else 'cartas' end
  when 'tecnico' then 'tecnicos' when 'impeto' then 'impetos' when 'texto' then 'textos'
  when 'catalogo' then 'catalogos' when 'clube' then 'dimensoes' when 'liga' then 'dimensoes'
  when 'nacionalidade' then 'dimensoes' else 'catalogos' end),
  expected_type = coalesce(expected_type, case when tipo_leitura='fixed_utf8_nul' then 'string' when tipo_leitura='all_str_parser' then 'objeto_textual' when tipo_leitura='membership' then 'boolean' when catalogo_tabela is not null then 'foreign_key' else 'integer' end),
  normalizador_id = coalesce(normalizador_id, case when tipo_leitura='fixed_utf8_nul' then 'utf8_nul_trim' when tipo_leitura='all_str_parser' then 'all_str_entry' when tipo_leitura='membership' then 'relacao_membership' when catalogo_tabela is not null then 'catalogo_fk' else 'identidade_numerica' end),
  versao_normalizador = coalesce(versao_normalizador, 'v1'),
  schema_payload = coalesce(schema_payload, jsonb_build_object('versao','envelope_campo_v1','raw','obrigatorio','normalizado','obrigatorio','proveniencia','obrigatorio')),
  identidade_estavel = coalesce(identidade_estavel, jsonb_build_object('campo_raiz',case when chave_campo like 'tecnico.%' then 'tecnico.id' when chave_campo like 'texto.%' then 'texto.chave' else 'carta.id' end,'catalogo_chave',catalogo_chave)),
  fk_destino = coalesce(fk_destino, nullif(requisito->>'fk','')),
  nulidade = coalesce(nulidade, 'nullable_explicit'),
  serializacao_saida = coalesce(serializacao_saida, 'json');

alter table clube_novo.contrato_leitura_arquivo alter column leitor_id set not null, alter column versao_leitor set not null, alter column formato_saida set not null, alter column tipo_saida set not null, alter column serializacao_saida set not null;
alter table clube_novo.contrato_leitura_campo alter column chave_familia set not null, alter column expected_type set not null, alter column normalizador_id set not null, alter column versao_normalizador set not null, alter column schema_payload set not null, alter column identidade_estavel set not null, alter column nulidade set not null, alter column serializacao_saida set not null;

insert into clube_novo.contrato_leitura_familia (contrato_id,chave_familia,leitor_id,versao_leitor,schema_payload,tipo_saida,normalizador_id,versao_normalizador,identidade,papeis_fonte,proveniencia)
select c.contrato_id, f.chave_familia, case when f.chave_familia='textos' then 'all_str_v1' else 'wesys_raw' end, 'v1',
 jsonb_build_object('versao','envelope_familia_v1','registro',jsonb_build_object('raw','obrigatorio','normalizado','obrigatorio','tipo','obrigatorio','identidade','obrigatorio','proveniencia','obrigatorio')),
 'envelope_familia','normalizacao_por_campo','v1',jsonb_build_object('campo_raiz',min(f.identidade_estavel->>'campo_raiz')),
 coalesce((select jsonb_agg(distinct a.papel_fonte order by a.papel_fonte) from clube_novo.contrato_leitura_arquivo a join clube_novo.contrato_leitura_campo x on x.arquivo_id=a.arquivo_id and x.contrato_id=a.contrato_id where x.contrato_id=c.contrato_id and x.chave_familia=f.chave_familia),'[]'::jsonb),
 'promovido de contrato_leitura_campo e arquivo; sem inferência de mapa local'
from clube_novo.contrato_leitura_jogo c join clube_novo.contrato_leitura_campo f on f.contrato_id=c.contrato_id
group by c.contrato_id,f.chave_familia
on conflict (contrato_id,chave_familia) do nothing;

insert into clube_novo.contrato_leitura_fonte_localizador (contrato_id,papel_fonte,ordem,template_caminho,plataforma,obrigatorio,proveniencia)
select a.contrato_id,a.papel_fonte,1,case a.papel_fonte
 when 'dt870_updated' then '%ProgramData%\\KONAMI\\eFootball\\ST\\Download\\dt870_console_win.cpk'
 when 'dt261_bra' then '%ProgramFiles(x86)%\\Steam\\steamapps\\common\\eFootball\\cpk\\dt261_bra_console_win.cpk'
 when 'dt200' then '%ProgramFiles(x86)%\\Steam\\steamapps\\common\\eFootball\\cpk\\dt200_console_all.cpk'
 when 'dt870_original' then '%ProgramFiles(x86)%\\Steam\\steamapps\\common\\eFootball\\cpk\\dt870_console_win.cpk' else '%' end,
 'windows',a.obrigatorio,'fonte promovida de contrato ativo; caminho versionado no banco'
from (select distinct contrato_id,papel_fonte,obrigatorio from clube_novo.contrato_leitura_arquivo) a
where a.papel_fonte in ('dt870_updated','dt261_bra','dt200','dt870_original')
on conflict (contrato_id,papel_fonte,ordem) do nothing;

insert into clube_novo.contrato_leitura_expectativa (contrato_id,chave_familia,chave_metrica,valor_esperado,comparador,proveniencia)
select c.contrato_id,e.chave_familia,e.chave_metrica,e.valor_esperado,'igual','regressão promovida de validador local; agora versionada pelo contrato'
from (values ('cartas','registros',43072::bigint),('textos','chaves',11679::bigint),('tecnicos','registros',1478::bigint),('impetos','efeitos',2072::bigint),('impetos','condicoes',407::bigint),('impetos','faixas',696::bigint)) e(chave_familia,chave_metrica,valor_esperado)
cross join (select contrato_id from clube_novo.contrato_leitura_jogo where estado='ativo') c
on conflict (contrato_id,chave_familia,chave_metrica) do nothing;

commit;
