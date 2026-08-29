# LEIA-ME PRIMEIRO — o mapa desta pasta

**Atualizado em 25/08/2026.**

Esta pasta é **o código final do sistema**. Regra do Luis. Por isso o mapa tem que estar
escrito, e não na cabeça de ninguém.

---

## ⚠️ EXISTEM DUAS VERSÕES DA TELA NESTA PASTA. LEIA ISTO ANTES DE MEXER.

Elas se parecem, têm o mesmo nome de arquivo, e **leem views diferentes do banco**:

| onde | lê do banco | o que é |
|---|---|---|
| **`1-SISTEMA\`** | `casa_lista` + `casa_tela` + `casa_arows` | ✅ **A VERSÃO QUE VALE.** A migrada, a que está sendo trabalhada |
| **arquivos soltos na raiz** | `tela_encaixe` | ⛔ **VERSÃO LEGADA.** É a que está no ar hoje |
| `SITE-ATUAL-EXATO-2026-08-24\` | `tela_encaixe` | ⛔ Cópia da mesma coisa (conferido: byte a byte igual à da raiz) |
| `SITE-ATUALIZADO-2026-08-24\` | — | ⛔ Outra cópia antiga |

**O `mtime` engana.** Os arquivos da raiz têm data de hoje porque foram baixados hoje —
mas o **conteúdo** é anterior à migração. Só o conteúdo diz a verdade, e o conteúdo
está conferido acima por md5.

### O que apagar quando quiser limpar

Estes são cópia da versão legada e não são usados por nada:

```
Clubefootball 2026-08-25\elenco.js
Clubefootball 2026-08-25\ficha-ajustes.js
Clubefootball 2026-08-25\motor-e-ficha-base.js
Clubefootball 2026-08-25\modulos-elenco-paginas.js
Clubefootball 2026-08-25\paginas-e-navegacao.js
Clubefootball 2026-08-25\dados-e-catalogos.js
Clubefootball 2026-08-25\user-state-repository.js
Clubefootball 2026-08-25\como-funciona.js
Clubefootball 2026-08-25\como-funciona.css
Clubefootball 2026-08-25\clubefut.css
Clubefootball 2026-08-25\ClubEfootball-DATA-BOXES-CORRIGIDA-CARDS-LARGOS.html
Clubefootball 2026-08-25\TELA-CLUBEFOOTBALL-UNICA.html
```

⚠️ **Só apague depois de confirmar que o site no ar já foi trocado pela versão de
`1-SISTEMA\`.** Enquanto o ar rodar a versão legada, guarde-as.

---

## As pastas

| pasta | o que é |
|---|---|
| **`1-SISTEMA\`** | A tela. **É esta que vale.** |
| **`2-MOTORES\`** | `travas.py` — o portão que não deixa o motor rodar com insumo faltando |
| **`3-ALIMENTADOR\`** | Aplicativo com interface para subir os lotes da coleta para o banco |
| **`4-DOCUMENTOS\`** | Manual técnico e os relatórios |
| **`5-COLETA-EM-PARALELO\`** | O coletor V8 e os lotes coletados (8 de 30 prontos) |
| **`6-AVALIADOR-NO-RAILWAY\`** | O serviço que faz a conta no servidor. ⚠️ **não é o que está no ar** — ver abaixo |
| **`7-VARREDURA-DO-JOGO\`** | O contexto para varrer os arquivos do jogo na outra máquina |

### Manuais principais

- `4-DOCUMENTOS\MANUAL-DO-OTIMIZADOR.md` — entradas, fórmula, nota, técnicos,
  evidências, limites e testes do **Otimizador**;
- `4-DOCUMENTOS\MANUAL-TECNICO.md` — arquitetura geral do ClubEfootball;
- `4-DOCUMENTOS\MANUAL-DAS-TABELAS.md` — contrato do banco;
- `7-VARREDURA-DO-JOGO\DOCUMENTACAO\MANUAL-DO-EXTRATOR.md` — Extrator eFootball.

`motor`, `2-MOTORES` e RPCs com `_motor` são nomes técnicos históricos mantidos por
compatibilidade. O nome do componente para uso e documentação é **Otimizador**.

---

## ⛔ Três coisas quebradas que você precisa saber

### 1. O que está no ar no Railway não é o que está em `6-AVALIADOR-NO-RAILWAY\`

A pasta tem `app.py` (rotas `/saude`, `/recarregar`, `/avaliar`, `/otimizar`) e um
Procfile dizendo `gunicorn app:app`. Mas o serviço no ar responde `200` em `POST /nota`
— **rota que não existe no `app.py`** — e o *Custom Start Command* das Settings do
Railway aponta para `servidor:app`, arquivo que não está aqui.

**Não é deploy que não pegou. É arquivo diferente.** Antes de mexer no serviço, baixe do
repositório o que está realmente rodando.

### 2. O serviço recusa as builds que o próprio motor fez

Testado com 4 builds gravadas: as 4 voltaram `HTTP 400 — "esta carta nao aceita: …"`,
citando habilidades que o motor pôs. Causa medida: o pool de habilidades do banco
discorda do que o motor usou em **2.681 de 2.836 cartas**, nos dois sentidos.
**Decisão sua:** qual pool vale.

### 3. O molde está público

O `arows` que a tela recebe carrega **peso e alvo** de cada atributo — que *são* o
molde. Com a chave que está no próprio JS, dá para reconstruir **as 19 funções em 2,4
segundos**. Só fecha quando a conta for para o servidor e o `arows` parar de sair do
banco.

---

## O estado das etapas

```
etapa 7  · a casca                     FEITA
etapa 8  · conferência lote a lote     FEITA (com a trava do nulo)
etapa 9  · a fila da rodada            FEITA (6.339 builds prontas para rodar)
etapa 10 · homologação                 REPROVADA — ver os itens 1 e 2 acima
etapa 11 · login, comercial, chaves    o molde está aberto — ver o item 3
```
