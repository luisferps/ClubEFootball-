const runWithCommon=require('./common-harness.cjs').run;
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const source = fs.readFileSync(path.join(root, 'site-shell.js'), 'utf8');
function element(route) {
  return { dataset: { route }, attributes: {}, handlers: {}, innerHTML: '',
    classList: { toggle() {} },
    setAttribute(k, v) { this.attributes[k] = v; },
    removeAttribute(k) { delete this.attributes[k]; },
    addEventListener(k, v) { this.handlers[k] = v; },
    focus() { this.focused = true; }
  };
}
const main = element(), theme = element(), search = element();
const links = [...html.matchAll(/data-route="([^"]+)"/g)].map(m => element(m[1]));
const location = { hash: '' }, handlers = {}, pending = [];let boxRequest;
const document = { title: '', documentElement: { dataset: { theme: 'escuro' } },
  getElementById: id => id === 'conteudo' ? main : id === 'sn-theme' ? theme : null,
  querySelectorAll: () => links, querySelector: () => search
};
runWithCommon(source, {
  document,
  location,
  URLSearchParams,
  window: {
    addEventListener: (key, fn) => { handlers[key] = fn; },
    scrollTo() {},
    SiteNovoBoxes: {
      unmount() {},
      mount(node, active = false, box = null) {
        boxRequest = { active, box };
        node.innerHTML = '<h1>' + (active ? 'Boxes em andamento' : 'Boxes cadastradas') + '</h1>';
      }
    },
    SiteNovoSearch: {
      unmount() {},
      sync() {},
      mount(node, term) { node.innerHTML = '<h1>Buscar Cards</h1><p>' + term + '</p>'; }
    }
  },
  setTimeout: fn => pending.push(fn)
});
assert.match(main.innerHTML, /Falha de carregamento/);
location.hash='#ranking';handlers.hashchange();
assert.match(main.innerHTML,/Falha de carregamento/);
assert.doesNotMatch(main.innerHTML,/ainda não está conectado|Área reservada/);
assert.doesNotMatch(source,/O Ranking ainda não está conectado|As boxes ainda não estão conectadas/);
const routes = ['inicio', 'ranking', 'elenco', 'boxes', 'boxes-em-andamento', 'busca', 'ficha', 'como-funciona'];
for (const route of routes) {
  location.hash = '#' + route; handlers.hashchange();
  assert.match(main.innerHTML, /<h1>/, route);
  assert.doesNotMatch(document.title, /não encontrada/, route);
  assert.ok(main.focused);
  for (const link of links) assert.equal(link.attributes['aria-current'], link.dataset.route === route ? 'page' : undefined);
  for (const match of main.innerHTML.matchAll(/href="#([^"]+)"/g)) assert.ok(routes.includes(match[1]), match[1]);
}
location.hash = '#ficha'; handlers.hashchange();
assert.match(main.innerHTML, /action="ficha.html" method="get" target="_blank" rel="noopener"/);
const idPattern = new RegExp('^(?:' + main.innerHTML.match(/pattern="([^"]+)"/)[1] + ')$');
for (const id of ['1', '55068997045101', '900719925474099312345']) assert.ok(idPattern.test(id));
for (const id of ['0', '000', '-1', '1.3', ' 123 ', '<script>', '1e3']) assert.ok(!idPattern.test(id));
const line = { value: '', disabled: false };
const form = { matches: () => true, elements: { namedItem: () => line } };
main.handlers.submit({ target: form }); assert.equal(line.disabled, true);
pending.pop()(); assert.equal(line.disabled, false);
line.value = '900719925474099312345'; main.handlers.submit({ target: form });
assert.equal(line.disabled, false); assert.equal(line.value, '900719925474099312345');
pending.pop()();
const beforeSkip = main.innerHTML; location.hash = '#conteudo'; handlers.hashchange();
assert.equal(main.innerHTML, beforeSkip);
location.hash = '#<img src=x onerror=alert(1)>'; handlers.hashchange();
assert.match(document.title, /Página não encontrada/); assert.doesNotMatch(main.innerHTML, /onerror/);
for (const m of html.matchAll(/(?:src|href)="([^"#][^"]*)"/g)) {
  assert.ok(fs.existsSync(path.join(root, m[1].split('?')[0])), m[1]);
}
assert.doesNotMatch(source, /\bfetch\s*\(|XMLHttpRequest|localStorage|service_role|1-SISTEMA|2-MOTORES/);
assert.doesNotMatch(source, /busca ainda não|Aguardando o catálogo/);
console.log('OK: 8 rotas, links locais, foco, rota inválida e entrada da Ficha sem perda de ID. Sem chamadas de rede no shell.');

location.hash='#boxes-em-andamento?box='+encodeURIComponent('Legends & amigos');handlers.hashchange();assert.equal(boxRequest.active,true);assert.equal(boxRequest.box,'Legends & amigos');
