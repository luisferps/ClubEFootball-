-- Fecha a lacuna entre "campo físico encontrado" e "mapeamento individual provado".
-- Os três campos de GO continuam rastreáveis, mas não podem participar de contrato ativo.

update clube_novo.contrato_leitura_campo
set status_prova='provisorio',
    prova=prova || '; associação individual ainda é convenção de ordenação aprovada, sem prova física independente'
where contrato_id='clubef-dt870-2026-r1'
  and chave_campo in ('impeto.efeito.bit.192','impeto.efeito.bit.197','impeto.efeito.bit.256');

create or replace function clube_novo.validar_ativacao_contrato_leitura()
returns trigger
language plpgsql
security invoker
set search_path = clube_novo, pg_temp
as $$
begin
  if new.estado = 'ativo' then
    if not new.cobertura_total then
      raise exception 'contrato não pode ativar: cobertura integral não confirmada';
    end if;
    if exists (
      select 1 from clube_novo.contrato_leitura_campo f
      where f.contrato_id = new.contrato_id
        and f.ativo
        and f.status_prova <> 'comprovado'
    ) then
      raise exception 'contrato não pode ativar: há campo ativo sem prova física individual';
    end if;
    if exists (
      select 1 from clube_novo.contrato_leitura_cadeia c
      where c.contrato_id = new.contrato_id
        and c.requer_selo_contrato
        and c.estado <> 'conforme'
    ) then
      raise exception 'contrato não pode ativar: cadeia satélite ainda possui elo pendente';
    end if;
  end if;
  return new;
end;
$$;
