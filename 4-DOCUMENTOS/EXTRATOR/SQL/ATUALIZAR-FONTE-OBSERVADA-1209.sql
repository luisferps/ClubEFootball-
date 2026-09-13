begin;
set local lock_timeout='5s';
set local statement_timeout='30s';
do $update$
declare p jsonb := '{"schema":"clubef-atualizacao-fonte-v1","papel_fonte":"dt870_updated","sha256_anterior":"4f71570c2ea691e74bff58f5038fb9dfb7bb8aed712b1e77249fc408f14bb0ea","sha256_observado":"051491deb87eacc3772cc254b66ec8649860dda5351e80c28524b3aad3de8f5d","contrato_id":"clubef-dt870-2026-r1","estrutura_compativel":true,"validacao_semantica_concluida":false,"database_write":false,"arquivos":[{"arquivo_id":2,"arquivo":"Coach.bin","sha256_anterior":"d64bc0570043e9ef116c49e7f2d70b997afa39f9a0570ab0525c1501a8e1f1ed","sha256_observado":"cb2484b8d29d4d966a22202cf463719c51c968a75f83fad05667263f4955eced","bytes":263120,"tamanho_registro":176,"registros":1495},{"arquivo_id":9,"arquivo":"CompetitionEntry.bin","sha256_anterior":"3ac5e7f9d07b95b09de2ed781cfa09e70a35b437422a804244a8523a96d0c4f8","sha256_observado":"3ac5e7f9d07b95b09de2ed781cfa09e70a35b437422a804244a8523a96d0c4f8","bytes":8544,"tamanho_registro":12,"registros":712},{"arquivo_id":8,"arquivo":"CompetitionUnit.bin","sha256_anterior":"f6161dd2a0e80865e9f7fd37566f99b9a12880d90757b89a17550b97fa20737c","sha256_observado":"f6161dd2a0e80865e9f7fd37566f99b9a12880d90757b89a17550b97fa20737c","bytes":185400,"tamanho_registro":2472,"registros":75},{"arquivo_id":3,"arquivo":"Country.bin","sha256_anterior":"6dcb876a1922281cc5bf513f8ee117846fbeed42e48936f40af2007232c1b0a7","sha256_observado":"6dcb876a1922281cc5bf513f8ee117846fbeed42e48936f40af2007232c1b0a7","bytes":318432,"tamanho_registro":1488,"registros":214},{"arquivo_id":1,"arquivo":"Player.bin","sha256_anterior":"a679eec7804fa487bb09ba586c822fa8f9a22652d7934fe6ea3b96bcb502b888","sha256_observado":"39bba595b27033ed7449b06b7527b13fbfaad8d961faad3016a116c86a5dfabc","bytes":17454000,"tamanho_registro":400,"registros":43635},{"arquivo_id":10,"arquivo":"PlayerAppearance.bin","sha256_anterior":"a5b5cf3bbd5ff30f3e70190e7d1085fe9c1cec1b1008f474ec781cac8535b988","sha256_observado":"412ce0329ea7c0739734c9cbbf552e9efac0977768d7a92cff51d923b72b3d6e","bytes":2792640,"tamanho_registro":64,"registros":43635},{"arquivo_id":5,"arquivo":"PlayerBooster.bin","sha256_anterior":"798acdfd65c7b833cd6ef18c3dd825c7287a6d13baffbfc9d69a28eafeab4e3e","sha256_observado":"19aeb2710c676671ef6b9699760bd6607905820c24abeee64f5afc507df2d7d2","bytes":16440,"tamanho_registro":40,"registros":411},{"arquivo_id":6,"arquivo":"PlayerDeleteList.bin","sha256_anterior":"788e8f3976ff635898e014b051b5141b5f1551c3a11609bac5841a65e900b453","sha256_observado":"f40cccafe822e1117013c29625aa36c1720be8bfe7efc562617e499af3fa1438","bytes":64408,"tamanho_registro":8,"registros":8051},{"arquivo_id":11,"arquivo":"PlayerSkill.bin","sha256_anterior":"0028916b9904fcc03b9862b3cc6bf084048e5d6c54dea7dcefe4e64d35b07795","sha256_observado":"0028916b9904fcc03b9862b3cc6bf084048e5d6c54dea7dcefe4e64d35b07795","bytes":7488,"tamanho_registro":104,"registros":72},{"arquivo_id":12,"arquivo":"Playstyle.bin","sha256_anterior":"67a3f34ba9c63e5b84396e2891e3b0ac10a315125f4a6ae0eebeb032a06d0d38","sha256_observado":"67a3f34ba9c63e5b84396e2891e3b0ac10a315125f4a6ae0eebeb032a06d0d38","bytes":6048,"tamanho_registro":168,"registros":36},{"arquivo_id":7,"arquivo":"Team.bin","sha256_anterior":"959c0b9db337006c40b2da4a1f344048e4dd50f9bc39544e313ecf703aa2508b","sha256_observado":"0737c9eb8b303293a4172756021067bcb6d8265ef795cc89658ca7cbdc12751d","bytes":1569600,"tamanho_registro":1600,"registros":981}]}'::jsonb; n integer;
begin
perform 1 from clube_novo.contrato_leitura_jogo where contrato_id=p->>'contrato_id' and estado='ativo' for update;
if not found then raise exception 'Contrato ativo mudou'; end if;
update clube_novo.contrato_leitura_politica_revisao
set cobertura_aprovada=false,carga_autorizada=false,
decisao=jsonb_build_object('estado','fonte_nova_aguarda_comparacao','evidencia_estrutural',p),atualizado_em=now()
where contrato_id=p->>'contrato_id';
if not found then raise exception 'Politica de revisao ausente'; end if;
update clube_novo.contrato_leitura_arquivo a
set sha256_arquivo=x.sha256_observado,versao_arquivo='dt870-atualizacao-observada-20260912',
proveniencia=a.proveniencia || '; Fonte observada pelo Extrator em 12/09/2026; estrutura conferida, comparacao semantica pendente.'
from jsonb_to_recordset(p->'arquivos') x(arquivo text,sha256_anterior text,sha256_observado text,tamanho_registro integer)
where a.contrato_id=p->>'contrato_id' and a.papel_fonte=p->>'papel_fonte'
and a.arquivo=x.arquivo and a.sha256_arquivo=x.sha256_anterior and a.tamanho_registro is not distinct from x.tamanho_registro;
get diagnostics n=row_count;
if n<>11 then raise exception 'Arquivos mudaram concorrentemente: %',n; end if;
update clube_novo.contrato_leitura_fonte_localizador
set sha256_cpk=p->>'sha256_observado'
where contrato_id=p->>'contrato_id' and papel_fonte=p->>'papel_fonte' and ordem=1 and sha256_cpk=p->>'sha256_anterior';
get diagnostics n=row_count;
if n<>1 then raise exception 'Localizador mudou concorrentemente'; end if;
end;
$update$;
commit;
