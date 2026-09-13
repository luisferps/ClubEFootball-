const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../ficha-editor.js'),'utf8');
const code=source.slice(source.indexOf('  function technicianOptionLabel('),source.indexOf('  function renderControls('));
const context={};vm.createContext(context);vm.runInContext(code,context);
assert.equal(context.technicianOptionLabel({nome:'Gennaro Gattuso',proficiencia:89,atributos:[{nome:'Passe Alto',delta:1},{nome:'Aceleração',delta:1}]}),'Gennaro Gattuso · 89 · Passe Alto +1 · Aceleração +1');
assert.equal(context.technicianOptionLabel({nome:'Sem bônus',proficiencia:60,atributos:[]}),'Sem bônus · 60');
assert.equal(context.technicianSelectedLabel({nome:'Gennaro Gattuso',proficiencia:89,atributos:[{nome:'Passe Alto',delta:1}]}),'Gennaro Gattuso · 89');
assert.equal(context.technicianSelectedLabel(null),'Sem técnico');
console.log('OK: opções de técnico exibem proficiência e atributos do catálogo.');
