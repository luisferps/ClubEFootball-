const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../ficha-editor.js'),'utf8');
const code=source.slice(source.indexOf('  function renderImpulses(){'),source.indexOf('  function renderControls(){'));
function node(tag,css,text){return{tag,className:css||'',textContent:text||'',children:[],attrs:{},classList:{add(){}},append(...xs){this.children.push(...xs)},replaceChildren(...xs){this.children=xs},setAttribute(k,v){this.attrs[k]=v}}}
const target=node('div'),session={saving:false,input:{impetos:{},condicoes:{2:3}},catalog:{adicionais:[],slots:[{slot:2,codigo:99,nome:'Física',vaga:false,condicional:true,maximo:3,cor:2,efeitos:[{nome:'Equilíbrio',delta:3}]}]}};
let changes=0;
const context={session,colors:{2:'amarelo'},field:()=>target,el:node,button:(text,fn,css)=>{const b=node('button',css,text);b.type='button';b.onclick=fn;return b},changed:()=>{changes++},Number};
vm.createContext(context);vm.runInContext(code,context);
function shown(){context.renderImpulses();const box=target.children[0],title=box.children[0],button=title.children[1];assert.equal(button.tag,'button');assert.ok(!JSON.stringify(box).includes('select'));return button}
let b=shown();assert.equal(b.textContent,'+3');b.onclick();assert.equal(session.input.condicoes[2],1);
b=shown();assert.equal(b.textContent,'+1');b.onclick();assert.equal(session.input.condicoes[2],2);
b=shown();assert.equal(b.textContent,'+2');b.onclick();assert.equal(session.input.condicoes[2],3);assert.equal(changes,3);
session.input.condicoes[2]=0;b=shown();assert.equal(b.textContent,'+3');assert.equal(session.input.condicoes[2],3);
console.log('OK: botão condicional alterna +3, +1, +2 e nunca oferece zero.');
