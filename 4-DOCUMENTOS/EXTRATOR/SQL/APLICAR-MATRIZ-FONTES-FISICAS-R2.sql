-- Matriz física versionada do Extrator. Estrutura de contrato somente;
-- não lê nem grava tabelas de dados do jogo.
begin;

alter table clube_novo.contrato_leitura_familia
  add column if not exists precedencia_fontes jsonb not null default '[]'::jsonb;

alter table clube_novo.contrato_leitura_fonte_localizador
  add column if not exists sha256_cpk text;

do $$ begin
  if not exists (select 1 from pg_constraint where conname='contrato_leitura_familia_precedencia_fontes_array' and conrelid='clube_novo.contrato_leitura_familia'::regclass) then
    alter table clube_novo.contrato_leitura_familia
      add constraint contrato_leitura_familia_precedencia_fontes_array
      check (jsonb_typeof(precedencia_fontes) = 'array') not valid;
  end if;
end $$;

-- A ordem é semântica e não é fallback: os três CPKs são lidos quando a
-- família os solicita; o primeiro somente resolve uma divergência já
-- reportada com procedência preservada.
update clube_novo.contrato_leitura_familia
set papeis_fonte = case chave_familia
  when 'cartas' then '["dt870_updated"]'::jsonb
  when 'textos' then '["dt261_bra"]'::jsonb
  when 'tecnicos' then '["dt870_updated","dt870_original","dt200"]'::jsonb
  when 'catalogos' then '["dt870_updated","dt870_original","dt200"]'::jsonb
  when 'dimensoes' then '["dt870_updated","dt870_original","dt200"]'::jsonb
  else '["dt870_updated","dt870_original","dt200"]'::jsonb
end,
precedencia_fontes = case chave_familia
  when 'cartas' then '["dt870_updated"]'::jsonb
  when 'textos' then '["dt261_bra"]'::jsonb
  when 'tecnicos' then '["dt870_updated","dt870_original","dt200"]'::jsonb
  when 'catalogos' then '["dt870_updated","dt870_original","dt200"]'::jsonb
  when 'dimensoes' then '["dt870_updated","dt870_original","dt200"]'::jsonb
  else '["dt870_updated","dt870_original","dt200"]'::jsonb
end,
proveniencia = 'r2-fontes: CPKs fisicamente presentes; precedência explícita, sem fallback'
where contrato_id='clubef-dt870-2026-r1';

insert into clube_novo.contrato_leitura_fonte_localizador
  (contrato_id,papel_fonte,ordem,template_caminho,plataforma,obrigatorio,proveniencia,sha256_cpk)
values
  ('clubef-dt870-2026-r1','dt200',1,'%ProgramFiles(x86)%\\Steam\\steamapps\\common\\eFootball\\cpk\\dt200_console_all.cpk','windows',true,'r2-fontes: fonte física comprovada','fd920cd8e7f3f1089892ef4051c68c1c5c56c49000ecf6f751025a0ae2c94a50'),
  ('clubef-dt870-2026-r1','dt870_original',1,'%ProgramFiles(x86)%\\Steam\\steamapps\\common\\eFootball\\cpk\\dt870_console_win.cpk','windows',true,'r2-fontes: fonte física comprovada','ae0d8cef26804439e9930ef8959f8d9425754d0e290d056b3e4d1f7b999edd5c'),
  ('clubef-dt870-2026-r1','dt870_updated',1,'%ProgramData%\\KONAMI\\eFootball\\ST\\Download\\dt870_console_win.cpk','windows',true,'r2-fontes: fonte física comprovada','44df868c2613d532292d87072c0863a907d6a5f0cc40f914d355e56d74edfcc5')
on conflict (contrato_id,papel_fonte,ordem) do update
  set template_caminho=excluded.template_caminho, obrigatorio=excluded.obrigatorio, proveniencia=excluded.proveniencia, sha256_cpk=excluded.sha256_cpk;

update clube_novo.contrato_leitura_jogo
set versao_contrato='r2-fontes',
    fingerprint_contrato_sha256='7141fa3257037137b4be25257095a05fe0d66f5d6e70ba5d9abdb24a275799d8',
    fingerprint_fontes_sha256='9019aeaa69a4c9c9c54499a0dbf987a44c913bb6c323b3af81dd9f584d8de06c',
    politica_fonte=jsonb_build_object(
      'modo','somente_leitura',
      'fontes_fisicas',jsonb_build_array('dt200','dt870_original','dt870_updated'),
      'precedencia_padrao',jsonb_build_array('dt870_updated','dt870_original','dt200'),
      'dt261','somente quando declarado pela família',
      'fallback','proibido'),
    observacao='r2-fontes: matriz física declarada no contrato; sem carga produtiva'
where contrato_id='clubef-dt870-2026-r1';

commit;
