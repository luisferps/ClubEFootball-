-- Extensão idempotente da família Técnicos: Sobreposição de Antônio Conte.
-- Escopo exclusivo: três objetos já existentes em clube_novo.
-- Não cria tabela/coluna, não toca clube, carta, motor ou executável.
begin;
set local lock_timeout = '10s';
set local statement_timeout = '60s';
select pg_advisory_xact_lock(hashtextextended('clubef-coach-overload-v1', 0));

do $$
begin
  if (select count(*) from clube_novo.estilo_jogo_tecnico) <> 6 then
    raise exception 'pré-voo: catálogo de estilos não contém 6 registros';
  end if;
  if not exists (
    select 1 from clube_novo.estilo_jogo_tecnico
    where codigo='overload' and nome_pt='Sobreposição' and ordem=6
      and secao_texto='Any10T' and id_texto=793
  ) then
    raise exception 'pré-voo: registro canônico overload divergiu';
  end if;
  if not exists (
    select 1 from clube_novo.tecnico_jogo
    where id=17609097478250 and nome_en='Antonio Conte'
      and fonte_autoritativa='dt870_updated'
      and registro_dt870_atualizacao=1476
      and hash_coach_bin='092a07c62d1df0f19da6ad0e4e1252de07e5e1df8e9090760734829044c0d42a'
  ) then
    raise exception 'pré-voo: Antônio Conte atual não corresponde ao Coach.bin provado';
  end if;
  if not exists (
    select 1 from clube_novo.tecnico_jogo
    where id=17601312850052 and nome_en='Fabio Capello'
      and fonte_autoritativa='dt870_updated'
      and registro_dt870_atualizacao=1453
      and hash_coach_bin='092a07c62d1df0f19da6ad0e4e1252de07e5e1df8e9090760734829044c0d42a'
  ) then
    raise exception 'pré-voo: controle negativo Fabio Capello divergiu';
  end if;
end $$;

update clube_novo.estilo_jogo_tecnico
set bit=135,
    largura=7,
    arquivo_fonte='Coach.bin',
    cpk_fonte='dt870_console_win.cpk',
    pode_rodar=true,
    falta_o_que=null,
    confirmado_em=now()
where codigo='overload';

insert into clube_novo.tecnico_estilo_jogo
  (tecnico_id,codigo_estilo,proficiencia,fonte,cpk_origem,arquivo,
   registro,bit,largura,hash_coach_bin,confirmado,carregado_em)
values
  (17609097478250,'overload',96,'dt870_updated','dt870_console_win.cpk',
   'Coach.bin',1476,135,7,
   '092a07c62d1df0f19da6ad0e4e1252de07e5e1df8e9090760734829044c0d42a',
   true,now())
on conflict (tecnico_id,codigo_estilo) do update set
  proficiencia=excluded.proficiencia,
  fonte=excluded.fonte,
  cpk_origem=excluded.cpk_origem,
  arquivo=excluded.arquivo,
  registro=excluded.registro,
  bit=excluded.bit,
  largura=excluded.largura,
  hash_coach_bin=excluded.hash_coach_bin,
  confirmado=excluded.confirmado,
  carregado_em=now();

-- Zero é ausência legítima: nenhuma relação de Sobreposição é criada para os
-- outros 1.477 técnicos. Reexecução também reconcilia sobras indevidas.
delete from clube_novo.tecnico_estilo_jogo
where codigo_estilo='overload' and tecnico_id<>17609097478250;

insert into clube_novo.mapa_do_jogo
  (assunto,cpk,arquivo,chave,endereco,registro,aberto,medido_em,observacao)
values
  ('tecnico.estilo.sobreposicao',
   'dt870_console_win.cpk (atualização)',
   'Coach.bin',
   'tecnico_jogo.id u64 -> estilo_jogo_tecnico.codigo=overload',
   'bit 135, largura 7, unsigned little-endian bitfield',
   '176 bytes; índice em tecnico_estilo_jogo.registro',
   true,
   date '2026-08-28',
   'Coach.bin SHA-256 092a07c62d1df0f19da6ad0e4e1252de07e5e1df8e9090760734829044c0d42a; distribuição física: 96 somente em Antônio Conte ID 17609097478250 registro 1476, zero nos demais 1.477; controle Fabio Capello registro 1453 = 0; contrato clubef-sobreposicao-conte-physical-proof-v1')
on conflict (assunto,arquivo) do update set
  cpk=excluded.cpk,
  chave=excluded.chave,
  endereco=excluded.endereco,
  registro=excluded.registro,
  aberto=excluded.aberto,
  medido_em=excluded.medido_em,
  observacao=excluded.observacao;

comment on table clube_novo.estilo_jogo_tecnico is
  'Catálogo vivo dos estilos de jogo de técnico, separado do playstyle de jogador; seis estilos com fonte física comprovada.';
comment on table clube_novo.tecnico_estilo_jogo is
  'Proficiência física por técnico e estilo; cinco históricos por técnico e Sobreposição somente quando o campo físico for não zero.';

do $$
begin
  if (select count(*) from clube_novo.estilo_jogo_tecnico) <> 6 then
    raise exception 'readback: catálogo de estilos != 6';
  end if;
  if (select count(*) from clube_novo.estilo_jogo_tecnico where pode_rodar) <> 6 then
    raise exception 'readback: estilos aptos != 6';
  end if;
  if (select count(*) from clube_novo.tecnico_estilo_jogo) <> 7391 then
    raise exception 'readback: relações de estilo != 7391';
  end if;
  if (select count(*) from clube_novo.tecnico_estilo_jogo where codigo_estilo='overload') <> 1 then
    raise exception 'readback: relações de Sobreposição != 1';
  end if;
  if not exists (
    select 1 from clube_novo.tecnico_estilo_jogo
    where tecnico_id=17609097478250 and codigo_estilo='overload'
      and proficiencia=96 and registro=1476 and bit=135 and largura=7
      and confirmado
  ) then
    raise exception 'readback: relação Conte/Sobreposição divergiu';
  end if;
  if exists (
    select 1 from clube_novo.tecnico_estilo_jogo
    where tecnico_id=17601312850052 and codigo_estilo='overload'
  ) then
    raise exception 'readback: controle Capello recebeu Sobreposição indevida';
  end if;
  if not exists (
    select 1 from clube_novo.tecnico_estilo_principal_jogo
    where tecnico_id=17609097478250 and codigo_estilo='overload'
      and proficiencia=96 and principal and not gemea
  ) then
    raise exception 'readback: estilo principal derivado de Conte divergiu';
  end if;
  if (select count(*) from clube_novo.mapa_do_jogo
      where assunto='tecnico.estilo.sobreposicao' and arquivo='Coach.bin') <> 1 then
    raise exception 'readback: mapa físico de Sobreposição ausente';
  end if;
end $$;
commit;
