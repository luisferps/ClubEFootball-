const fs=require('node:fs'),assert=require('node:assert/strict'),vm=require('node:vm');
const root=require('node:path').resolve(__dirname,'../../..')+'/';
const s=fs.readFileSync(root+'Site Novo/ficha-editor.js','utf8');
const fn=s.slice(s.indexOf('  function twinsFor('),s.indexOf('  function renderSkills('));
const policy=JSON.parse(fs.readFileSync(root+'4-DOCUMENTOS/OTIMIZADOR/HABILIDADES-0909/politica-aprovada.json','utf8'));
const session={catalog:{bloqueios_sugestao:policy.bloqueios,habilidades:[{id:32,gemeas_cadastradas:[34]},{id:10,fabricavel:true,vetada:false},{id:34,fabricavel:true,vetada:false},{id:15,fabricavel:true,vetada:false},{id:999,gemeas_cadastradas:[10,15]}]},input:{habilidades:[32,999],funcao_id:17}};
const ctx={session};vm.createContext(ctx);vm.runInContext(fn,ctx);
const twins=x=>Array.from(ctx.twinsFor(x));
assert.deepEqual(twins(32),[]); // Cruzamento bloqueado no volante; gêmea não contorna.
assert.deepEqual(twins(999),[15]); // Drible bloqueado; Cabeçada permitida.
session.input.funcao_id=16;assert.deepEqual(twins(999),[10,15]);
session.input.funcao_id=7;assert.deepEqual(twins(999),[10]);
session.input.funcao_id=8;assert.deepEqual(twins(999),[10]);assert.deepEqual(twins(32),[]);
session.input.funcao_id=12;assert.deepEqual(twins(32),[34]);
session.input.funcao_id=1;assert.deepEqual(twins(32),[]); // bloqueio anterior
assert(session.catalog.habilidades.some(h=>h.id===34)); // catálogo manual intacto
delete session.catalog.bloqueios_sugestao;assert.deepEqual(twins(32),[]); // sem regra não inventa sugestões
console.log('9 casos: bloqueios antigos/novos, gêmeas, troca de função, duas exceções de drible e catálogo manual livre: OK.');
