-- Restaura apenas as 613 linhas capturadas pelo snapshot da promocao V1.
-- Não remove resultados, não toca linhas fora do snapshot e não inicia motores.
begin;

do $$
declare v_revertidas integer;
begin
  update clube_novo.build_linha_card l
     set execucao_tipo = s.anterior_execucao_tipo,
         lote_teste_id = s.anterior_lote_teste_id,
         lote_teste_semente = s.anterior_lote_teste_semente,
         lote_teste_fingerprint = s.anterior_lote_teste_fingerprint,
         amostra_ordem = s.anterior_amostra_ordem,
         sorteada_em = s.anterior_sorteada_em,
         pendencias = s.anterior_pendencias,
         publicada_em = s.anterior_publicada_em,
         publicacao_fingerprint = s.anterior_publicacao_fingerprint,
         bonificador_lote_publicacao_id = s.anterior_bonificador_lote_publicacao_id,
         atualizado_em = clock_timestamp()
    from clube_novo.bonificador_promocao_publicacao_snapshot_v1 s
   where l.id = s.linha_id
     and l.publicada_em = s.promovida_em
     and l.publicacao_fingerprint = s.selo_final_fingerprint;
  get diagnostics v_revertidas = row_count;

  if v_revertidas <> 613 then
    raise exception 'rollback promocao V1 interrompido: esperadas 613 linhas, revertidas %', v_revertidas;
  end if;

  update clube_novo.bonificador_lote_publicacao_v1 b
     set estado = 'revertido', concluido_em = null
   where exists (
     select 1 from clube_novo.bonificador_promocao_publicacao_snapshot_v1 s
     where s.lote_promocao_id = b.id
   );
end
$$;

notify pgrst, 'reload schema';
commit;
