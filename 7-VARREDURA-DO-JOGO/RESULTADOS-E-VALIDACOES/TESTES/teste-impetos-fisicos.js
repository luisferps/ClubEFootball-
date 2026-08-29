'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm');
const root=path.resolve(__dirname,'..','..');
for(const file of ['mapeamento-fisico.js','catalog-source-map.js','extrator-core.js']) vm.runInThisContext(fs.readFileSync(path.join(root,'app',file),'utf8'),{filename:file});
const paths={
 dt870_updated:path.join(process.env.ProgramData||'C:\\ProgramData','KONAMI','eFootball','ST','Download','dt870_console_win.cpk'),
 dt200:path.join(process.env['ProgramFiles(x86)']||'C:\\Program Files (x86)','Steam','steamapps','common','eFootball','cpk','dt200_console_all.cpk'),
 dt870_original:path.join(process.env['ProgramFiles(x86)']||'C:\\Program Files (x86)','Steam','steamapps','common','eFootball','cpk','dt870_console_win.cpk'),
 dt261_bra:path.join(process.env['ProgramFiles(x86)']||'C:\\Program Files (x86)','Steam','steamapps','common','eFootball','cpk','dt261_bra_console_win.cpk')};
function ok(v,m){if(!v)throw new Error(m)}
(async()=>{
 const bytes=Object.fromEntries(Object.entries(paths).map(([k,p])=>[k,new Uint8Array(fs.readFileSync(p))]));
 const desc={};for(const[k,b]of Object.entries(bytes))desc[k]={sha256:await CLUBEF_CORE.sha256(b)};
 const result=await CLUBEF_CORE.extractMetadataByFamily(bytes,desc);
 const imp=result.catalogs.impetos, byId=new Map(imp.records.map(r=>[Number(r.id),r]));
 ok(imp.contract==='clubef-impetos-physical-v1','contrato de ímpetos ausente');
 ok(imp.records.length===440,'união deve manter 440 códigos');
 ok(result.catalogs.tecnicos.records.length===1478,'Técnicos regrediu');
 ok(result.catalogs.textos.records.length===11679,'Textos regrediu');
 const messi=byId.get(507);ok(messi&&messi.criterio_codigo==='quantidade_jogadores_nacionalidade_regiao'&&messi.alvo_codigo===144,'Messi507 divergente');
 ok(JSON.stringify(messi.faixas)===JSON.stringify([{quantidade_minima:1,quantidade_maxima:7,delta:1},{quantidade_minima:8,quantidade_maxima:10,delta:2},{quantidade_minima:11,quantidade_maxima:23,delta:3}]),'faixas Messi divergentes');
 const ney=byId.get(170);ok(ney&&ney.criterio_codigo==='quantidade_jogadores_liga_categoria'&&ney.alvo_codigo===149,'Neymar170 divergente');
 ok(JSON.stringify(ney.faixas)===JSON.stringify([{quantidade_minima:1,quantidade_maxima:13,delta:1},{quantidade_minima:14,quantidade_maxima:19,delta:2},{quantidade_minima:20,quantidade_maxima:23,delta:3}]),'faixas Neymar divergentes');
 const membros=imp.liga_membros.filter(x=>x.codigo_liga_alvo_base===149).map(x=>x.codigo_liga_membro);
 ok(JSON.stringify(membros)===JSON.stringify([588,149]),'expansão física 149/588 divergente');
 ok(result.catalogs.efeitos_de_impeto.supported&&result.catalogs.efeitos_de_impeto.records.length===2072,`efeitos completos divergentes: ${result.catalogs.efeitos_de_impeto.records.length}`);
 ok(imp.records.filter(r=>r.preferred_source==='dt870_updated').length===408,'PlayerBooster atual deve ter 408 registros preferidos');
 console.log(JSON.stringify({passed:true,contract:imp.contract,codes:imp.records.length,effects:result.catalogs.efeitos_de_impeto.records.length,messi507:messi.faixas,neymar170:{target:ney.alvo_codigo,members:membros,ranges:ney.faixas},preserved:{technicians:result.catalogs.tecnicos.records.length,texts:result.catalogs.textos.records.length}},null,2));
})().catch(e=>{console.error(e.stack||e.message);process.exitCode=1});
