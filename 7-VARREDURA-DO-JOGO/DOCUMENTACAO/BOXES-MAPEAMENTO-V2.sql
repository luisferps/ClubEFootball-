begin;
insert into clube_novo.box_leitor_endereco_jogo_v1 (leitor_versao,executavel_versao,executavel_sha256,campo,origem_objeto,endereco_ou_offset,largura_ou_layout,derivacao,validacao,ativo) values ('boxes-cmd-get-myclub-agentlist-detalhes-v2','6.0.0.0','a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4','total_participantes_agente','agente convertido','agente+0x128','UInt32; 4 bytes','Parser 0x1457ebbff: player_list_total raw+0x158; conversor 0x1445d87ae: destino+0x128','150 Summer Transfer; 11 Worldwide; PFA 11 IDs distintos conferidos com total 11. Captura f13bbd9d-d0af-47fb-81b6-948aa5d3ab82',true) on conflict (leitor_versao,campo) do update set derivacao=excluded.derivacao,validacao=excluded.validacao,ativo=true;
insert into clube_novo.box_leitor_endereco_jogo_v1
(leitor_versao,executavel_versao,executavel_sha256,campo,origem_objeto,endereco_ou_offset,largura_ou_layout,derivacao,validacao,ativo)
select 'boxes-cmd-get-myclub-agentlist-detalhes-v2',executavel_versao,executavel_sha256,campo,origem_objeto,endereco_ou_offset,largura_ou_layout,derivacao,validacao,true
from clube_novo.box_leitor_endereco_jogo_v1 where leitor_versao='boxes-cmd-get-myclub-agentlist-v1'
on conflict (leitor_versao,campo) do update set ativo=true;
insert into clube_novo.box_leitor_endereco_jogo_v1
(leitor_versao,executavel_versao,executavel_sha256,campo,origem_objeto,endereco_ou_offset,largura_ou_layout,derivacao,validacao,ativo)
select 'boxes-cmd-get-myclub-agentlist-detalhes-v2','6.0.0.0','a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4',v.*,true
from (values
('participantes_completos','objeto B','B+0x380/B+0x388/B+0x390','vetor MSVC; stride 0xf0; card_id +8 UInt64','Resposta de Procurable/StandardDraft; callback Procurable 0x14467d940','150 IDs unicos e fisicos confirmados em 13/09; captura 8aa7f1cc-fb36-4ecc-a703-0a0640c35ef0'),
('total_participantes','objeto B','B+0x398','UInt32; 4 bytes','Quantidade total declarada para o vetor de recrutamento','Quantidade lida deve ser igual ao total'),
('indice_inicial','objeto B','B+0x3d4','UInt32; 4 bytes','Inicio da pagina de recrutamento','Exigir zero para lista completa')
) v(campo,origem_objeto,endereco_ou_offset,largura_ou_layout,derivacao,validacao)
on conflict (leitor_versao,campo) do update set endereco_ou_offset=excluded.endereco_ou_offset,derivacao=excluded.derivacao,validacao=excluded.validacao,ativo=true;
update clube_novo.box_leitor_endereco_jogo_v1 set ativo=false where leitor_versao='boxes-cmd-get-myclub-agentlist-v1';
commit;
insert into clube_novo.box_leitor_endereco_jogo_v1
(leitor_versao,executavel_versao,executavel_sha256,campo,origem_objeto,endereco_ou_offset,largura_ou_layout,derivacao,validacao,ativo)
values ('boxes-cmd-get-myclub-agentlist-detalhes-v2','6.0.0.0','a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4','agente_consultado','objeto B','B+0x280','UInt64; 8 bytes','0x14467d8d3 copia B+0x280 para Option+0x228; serializer 0x1452b9eb3 usa agent_id','ID 1365 validado na Worldwide 10 Sep 2026; exigir correspondencia e releitura estavel',true)
on conflict (leitor_versao,campo) do update set derivacao=excluded.derivacao,validacao=excluded.validacao,ativo=true;
