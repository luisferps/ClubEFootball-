'use strict';

const fs = require('fs');
const path = require('path');
const assert = require('assert');

const raiz = path.resolve(__dirname, '..', '..', '..');
const arquivos = [
  path.join(raiz, '1-SISTEMA', 'motor-e-ficha-base.js'),
  path.join(raiz, 'SITE-ATUALIZADO-2026-08-24', 'motor-e-ficha-base.js'),
  path.join(raiz, 'SITE-ATUALIZADO-2026-08-24', 'TELA-CLUBEFOOTBALL-UNICA.html'),
];

for (const arquivo of arquivos) {
  const fonte = fs.readFileSync(arquivo, 'utf8');
  const trecho = fonte.match(/function mult\(x,m\)\{[\s\S]*?\n\s*return Math\.min\(99,[\s\S]*?\}\n/);

  assert(trecho, `funcao mult aprovada nao encontrada em ${arquivo}`);
  const mult = Function(`${trecho[0]}; return mult;`)();
  assert.strictEqual(mult(98, 1.036), 99);
  assert.strictEqual(mult(99, 1.036), 99);
  assert.strictEqual(mult(99, 1.036) + 1 + 4, 104);
  assert(
    fonte.includes('x   = mult(pre, st.m);'),
    `a proficiencia nao entra antes dos impetos em ${arquivo}`
  );
  assert(
    fonte.includes('x  += tec[i] + nm[i] + imp[i];'),
    `boost e impetos nao entram depois da proficiencia em ${arquivo}`
  );
  assert(
    fonte.includes('e3  = mult(pre, st.m) + tec[i] + (e2 - pre);'),
    `a cascata visual nao segue proficiencia -> boost -> impetos em ${arquivo}`
  );
}

console.log('OK: tres interfaces usam proficiencia com teto -> boost -> impetos; Messi fecha em 104');
