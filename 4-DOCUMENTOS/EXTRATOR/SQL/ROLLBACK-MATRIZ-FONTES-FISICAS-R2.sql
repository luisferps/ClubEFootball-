-- Rollback cirúrgico de R2. Não toca dados de jogo, legado, motor ou UI.
begin;

update clube_novo.contrato_leitura_familia
set papeis_fonte=case chave_familia
  when 'textos' then '["dt261_bra"]'::jsonb
  when 'tecnicos' then '["dt870_updated","dt261_bra"]'::jsonb
  when 'catalogos' then '["dt870_updated","dt261_bra"]'::jsonb
  when 'dimensoes' then '["dt870_updated","dt261_bra"]'::jsonb
  else '["dt870_updated"]'::jsonb
end,
precedencia_fontes='[]'::jsonb,
proveniencia='rollback r2-fontes'
where contrato_id='clubef-dt870-2026-r1';

delete from clube_novo.contrato_leitura_fonte_localizador
where contrato_id='clubef-dt870-2026-r1' and papel_fonte in ('dt200','dt870_original');

update clube_novo.contrato_leitura_fonte_localizador
set sha256_cpk=null
where contrato_id='clubef-dt870-2026-r1';

update clube_novo.contrato_leitura_jogo
set versao_contrato='r1',
    fingerprint_contrato_sha256='86723a63b116c3fb31fcc9c1f01728f5072869b548b34f1dab5196b710dcb2fd',
    fingerprint_fontes_sha256='719e580013a0eedb2d6a8a777653bc366eabd2d4a1becc7579a493493cb0cd35',
    politica_fonte=jsonb_build_object('modo','somente_leitura','fonte_ativa','dt870_updated','texto_pt_br','dt261_bra','fallback_numerico','proibido'),
    observacao=null
where contrato_id='clubef-dt870-2026-r1';

commit;
