# MANUAL DA TELA — ClubEfootball

## Normalização e estrelas — decisão de 09/09/2026

O site oficial é `Site Novo`. Nas Boxes, substituir a etiqueta do card por cinco estrelas preenchidas/vazias segundo o campo `estrelas` vindo do banco. Preservar os textos antigos na legenda do cabeçalho. Não mostrar percentuais nos cards nem calcular a equivalência no navegador. Nota oficial: curva fixa da função aplicada ao bruto do Otimizador, depois bônus integral; banco realiza toda a conta. A Ficha e o editor pessoal usam a mesma normalização. Separação dos estilos de goleiro vale para a vitrine; não restringe escolhas pessoais. Especificação e limites: [NORMALIZACAO-0909/REGRA-APROVADA.md](NORMALIZACAO-0909/REGRA-APROVADA.md).

## Política vigente de habilidades — 09/09/2026

A política `habilidades-funcao-20260909-v1` está aplicada no `clube_novo` e no runtime oficial da Máquina 1. A matriz vigente tem 325 pares habilidade/função. O motor conserva de zero a cinco adicionais úteis; não preenche vagas sem ganho. Todas as sugestões automáticas, inclusive gêmeas de builds antigas, respeitam os bloqueios atuais da função. A escolha manual do usuário e as habilidades nativas continuam livres desses vetos estratégicos.

Banco, fontes, executável e fotografias locais foram sincronizados; lotes continuam pausados e na mesma ordem. A normalização da nota não mudou. A revisão local identificou 4.509 linhas para análise posterior; nenhum resultado antigo foi regravado ou despublicado nesta etapa. A instalação na Máquina 2 e a publicação do frontend são estados separados.

Regra completa, matriz, migrações, testes e evidências: [Habilidades por função V12](OTIMIZADOR/HABILIDADES-0909/REGRA-APROVADA.md). Os registros anteriores abaixo conservam o contexto da época e não substituem esta revisão.

> A tela é HTML + JS estático. Ela **só lê** o banco; nunca calcula nota, nunca
> escreve. Publicação por **Netlify Drop**. Atualizado em 07/09/2026.

---

## 1 · ONDE A TELA MORA

```
C:\Users\Luis Fernando\Downloads\ClubEFootball--main\ClubEFootball--main\1-SISTEMA\
```

⚠️ Repare na **pasta repetida** — é assim mesmo nessa máquina.

| arquivo | papel | linhas |
|---|---|---|
| `index.html` | a casca; carrega os JS **nesta ordem** | 375 |
| `dados-e-catalogos.js` | catálogos congelados ⚠️ 1,5 MB — pendência antiga | — |
| `clube-novo-read-model.js` | **o contrato de leitura** — todo acesso ao banco passa aqui | 1.273 |
| `user-state-repository.js` | o que é do usuário (elenco, builds salvas) | 19 KB |
| `motor-e-ficha-base.js` | o espelho do motor e as ferramentas do Elenco | 4.443 |
| `elenco.js` | Meu time / Elenco | 245 KB |
| `ficha-ajustes.js` | **a ficha de build** + as abas do cabeçalho + Boxes | 4.390 |
| `ficha-cadastral-view.js` | a ficha cadastral (modal) | 118 |
| `modulos-elenco-paginas.js` | as 5 análises do Elenco | 89 KB |
| `como-funciona.js` | a página "Como funciona" | 8 KB |
| `paginas-e-navegacao.js` | **RouteState** — dono único de rota, URL e histórico | 745 |
| `arows-sob-demanda.js` | busca o `arows` só quando precisa | 6 KB |
| `clubefut.css` | todo o visual | 275 KB |
| `test\clube-novo-read-model.test.js` | os 9 testes do contrato de leitura | — |

**A ordem no `index.html` importa.** `paginas-e-navegacao.js` carrega por **último**
de propósito: ele lê o `window.T6_ROUTE_DEFINITIONS` que os outros deixaram, e é
quem sobrescreve `window.abrir`, `window.reabrir` e `window.t6AbreFichaCadastral`.
Trocar essa ordem quebra a navegação inteira.

---

## 2 · DE ONDE A TELA LÊ

Tudo por PostgREST em `https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/`, com a
**chave publicável** (só leitura). O domínio operacional vive em `clube_novo`.
As views `public.frontend_*` são a porta pública atual e isolada; outras views
`public.*` antigas, `clube` e `clubef_read_v2` são legado e não são usadas.

| assunto | recurso | quem consome |
|---|---|---|
| Início | view `frontend_home_v1` | a vitrine da Início |
| Boxes | view `frontend_boxes_v1` e RPC `site_novo_boxes_v1` | Boxes cadastradas; acervo histórico e ofertas cadastradas, excluindo da listagem histórica um título igual ao de uma oferta em andamento. A busca ignora acentos e aceita um erro curto de digitação em termos com pelo menos cinco caracteres. |
| Busca | view `frontend_busca_v1` | busca do cabeçalho |
| Ficha cadastral | view `frontend_ficha_v1` | o modal do cadastro |
| Builds | **RPC** `frontend_build_publicada_v2` | Ranking, Elenco e a ficha de build |

Chamada só pelo `ClubeNovoReadModel`. **Nenhum outro arquivo fala com o banco.**

`frontend_boxes_v1` lê somente a relação comercial oficial. O campo legado
`carta_jogo.box` e o rótulo de `PlayerVariationDetail.bin` não participam. A
paginação do read model busca todas as páginas em blocos de até 1.000 linhas;
uma página vazia encerra a leitura. Em 07/09/2026, o readback público retornou
6.695 vínculos distribuídos em 1.021 títulos cadastrados.

### As leituras síncronas e a repetição (04/09)

A carga de boot é **síncrona** (`lerPaginaSync` / `lerRpcSync`) — ela trava a tela
até responder. Antes não tinha repetição: um soluço de rede virava tela de erro
permanente até o F5. Aconteceu em 03/09 às 14:34, com o projeto medido
`ACTIVE_HEALTHY` e a RPC respondendo 500 linhas em 1,3 s.

Agora ela **tenta 3 vezes**, com 600 ms de pausa entre as tentativas:

- repete quando pode melhorar sozinho — falha de rede (status 0), 408, 429 e 5xx
- **não** repete 4xx: um 400 ou 404 não melhora repetindo, sobe na primeira
- para em 3 e desiste; não fica repetindo para sempre

Medido: rede boa = 1 chamada · 2 falhas seguidas = 3 chamadas e a tela abre ·
rede caída = 3 chamadas, ~10 s, e a Início abre com "Builds indisponíveis" no canto
em vez de morrer inteira.

---

## 3 · A NAVEGAÇÃO — quem manda

**`RouteState` (`paginas-e-navegacao.js`) é o dono único** de rota, URL e histórico.
Ninguém mais pode escrever no `history`.

### As rotas

| rota | tela | aba acesa |
|---|---|---|
| `inicio` | a vitrine | Início |
| `meutime` | Elenco | Elenco |
| `ranking` | Ranking | Ranking |
| `boxatual` | Boxes cadastradas | Boxes cadastradas |
| `busca` | resultado da busca do cabeçalho | nenhuma |
| `ficha` | a ficha do card | nenhuma |
| `como-funciona` | página própria | Como funciona |
| `melhorfuncao` · `timefraco` · `melhorformacao` · `tecnicotime` · `comparartime` | as 5 análises | Elenco |

`boxant` ("Boxes anteriores") é **reescrita para `boxatual`** em 4 lugares. Existe
uma única tela canônica de boxes. Link antigo continua abrindo, só que na tela nova.

### As portas

```
Logo CLUBeFOOTBALL ....................... inicio
Abas do cabeçalho ........................ inicio · meutime · ranking · boxatual
Aba Como funciona ........................ como-funciona
Home "Ver no ranking" / "Ver ranking →" .. ranking
Home "Organizar elenco" .................. meutime
Home "Ver todas →" ....................... boxatual
Card em qualquer lista ................... ficha
Elenco → as 5 análises ................... as 5 rotas próprias
```

### O "voltar" das páginas próprias (04/09)

O `navega()` guarda em `estado.origemPagina` de onde o leitor veio, e o
`voltaDaPagina()` devolve **para lá** — não mais para uma rota fixa.

```
Ranking → Como funciona → voltar  →  ranking
Início  → Como funciona → voltar  →  inicio
Elenco  → Time fraco    → voltar  →  meutime
```

Entre duas páginas próprias a origem é descartada e vale o `returnRoute` declarado
pelo módulo. Isso evita laço.

---

## 4 · A FICHA DO CARD — uma tela, um desenho

Existem **duas** superfícies de card, e elas não são intercambiáveis:

| | ficha de BUILD | ficha CADASTRAL |
|---|---|---|
| onde | `ficha-ajustes.js` · `t6TelaFicha` | `ficha-cadastral-view.js` |
| mostra | o que o **motor escolheu** — barras, ímpeto, técnico, habilidades | a carta **como o jogo entrega** |
| desenho | o aprovado | modal, prefixo `t6fc-` |
| dono | `FichaController` (`window.abrir`, `window.reabrir`) | `t6AbreFichaCadastral` |

**Regra 1 (04/09):** toda porta tenta primeiro a **ficha de build**. A cadastral só
entra quando o card **não tem build publicada** — é melhor mostrar o cadastro do que
não mostrar nada.

**Regra 2 (04/09):** a ficha abre na build **que foi clicada**, venha o clique de onde
vier. Ranking, Início, Boxes, busca e endereço com `?card=` mostram todos o número da
build **publicada** — então é ela que abre (`FichaController.openFromRoute`). O
Elenco entra pelas portas dele (`abrir` / `reabrir`) e preserva a build que o dono
aplicou.

### ⛔ A ARMADILHA DA FOTO DO MOTOR

`_t6FotoMotor(c)` (`ficha-ajustes.js`) tira **uma** foto da build do motor e a
**congela para sempre** em `c._t6MotorOriginal`. Se a foto for tirada antes de as
linhas da build chegarem do banco, ela congela vazia — e nunca mais se refaz.

O sintoma é traiçoeiro, porque **a tela não dá erro**: ela abre com
`Nível 0 · 0/68 · 68 sobrando`, todas as barras em zero e nenhuma habilidade
adicionada, enquanto a PONTUAÇÃO TOTAL no topo mostra a nota certa da build
publicada. **Número de uma build, desenho de outra.**

Medido no James Rodríguez (`106788187841133`), que no banco tem
`Passe 6 · Chute 3 · Drible 12 · Destreza 11 · Força pernas 8` e 5 habilidades, e
aparecia com tudo zerado — inclusive depois de clicar em "MELHOR BUILD POSSÍVEL".

Corrigido em 04/09: a foto **só congela quando já existe conteúdo** (`sis` não
vazio). Enquanto o card está vazio ela é recalculada a cada chamada, e a primeira
chamada com dado real é a que fica.

⚠️ Quem mexer nessa função de novo: **nunca cachear estado de card antes de o dado
chegar.** Vale para qualquer cache do card, não só este.

Antes as duas disputavam o mesmo endereço: a ficha de build escrevia `?card=<id>` na
URL, e recarregar a página com esse `?card=` abria a **cadastral**. Mesmo endereço,
tela diferente. Corrigido.

### O rótulo da vaga de ímpeto

| situação | o que a tela mostra |
|---|---|
| tem nome | o nome |
| tem código, sem nome | `Ímpeto 182` — correto: 426 dos 440 ímpetos ainda não têm `id_texto` |
| é vaga (código `null`) | **"Vaga livre"** |

⛔ Nunca inventar nome de ímpeto e **nunca copiar da tabela legada** (erro já
cometido e desfeito em 03/09).

---

## 5 · O VOCABULÁRIO — build ≠ função

- **Função** é o **ofício**: Atacante Infiltrador, Meia Armador, Zagueiro de
  combate. São 19. É o alvo.
- **Build** é o **conjunto de escolhas** que o motor montou para render mais naquela
  função: barras, ímpeto, técnico, habilidades. É a resposta.

O mesmo card pode ter **várias builds na mesma função** — é o que "BUILDS SALVAS"
guarda. Por isso as duas palavras não podem virar uma só na tela.

---

## 6 · AS REGRAS QUE NÃO SE DISCUTEM

1. **Só existe o schema `clube_novo`.** Legado é só para conferência.
2. **Nome não é chave.** Chave é o código do jogo.
3. **`null` é ausência de resposta.** Onde não se sabe, a tela diz "não apurado" —
   nunca zero, nunca inventado.
4. Entrega sempre em **arquivo completo**, pronto para colar. Nunca trecho solto.
5. **Netlify trata warning de ESLint como ERRO FATAL** (`CI=true`). Variável
   declarada e não usada quebra o build.
6. **Netlify Drop:** o HTML principal tem que se chamar `index.html`.
7. Um passo de cada vez, com o caminho completo do arquivo.

---

## 7 · COMO PUBLICAR

1. Confirme que o arquivo principal se chama `index.html`
2. Abra o [Netlify Drop](https://app.netlify.com/drop)
3. Arraste a pasta **`1-SISTEMA`** inteira
4. Espere o endereço aparecer e teste **2 ou 3 vezes com calma**

Para testar antes de publicar, abra o arquivo local no Chrome:

```
file:///C:/Users/Luis%20Fernando/Downloads/ClubEFootball--main/ClubEFootball--main/1-SISTEMA/index.html
```

⚠️ Depois de trocar qualquer `.js`, sempre **Ctrl+Shift+R** — senão o Chrome serve o
arquivo velho do cache e você testa a versão errada.

---

## 8 · COMO DEPURAR — F12 → aba Console

```js
// onde a navegação acha que está
RouteState.inspect()
// { atual, estavel, origem, origemPagina, fichaCard, painel, transicoes, commits }

// o estado da ficha de build
FichaController.inspect()
// { key, aberta, ocupado, transicoes, desenhos, fechamentos, pedidos, ultimoMotivo }

// a última leitura do banco: código, mensagem e detalhes
ClubeNovoReadModel.diagnostico()

// a página Como funciona
ComoFuncionaPage.inspect()
```

Erros que a tela guarda sozinha, quando acontecem:

```js
window._T6_ERRO_CASCA        // o cálculo da casca estourou ao abrir um card
window._T6_ERRO_DESENHO      // o desenho da ficha estourou
window._T6_ERRO_CARGA_CARD   // não deu para carregar as funções do card
```

Para conferir a foto do motor de um card aberto:

```js
(()=>{const k=window._T6_CHAVE_ATUAL,[i,t]=k.split('|'),c=D.find(x=>x.id===i&&x.tipo===t);
return {chave:k, barras_do_card:c&&c.sisBar,
        foto_congelada:c&&c._t6MotorOriginal&&c._t6MotorOriginal.sisBar,
        atributos:c&&c.sis&&c.sis.length};})()
```

Se `foto_congelada` vier zerada e `barras_do_card` não, a foto foi tirada cedo demais.

### Sintomas conhecidos

| o que você vê | o que é |
|---|---|
| "Builds publicadas ainda indisponíveis" + `Failed to execute 'send'` | rede. Depois de 04/09 só aparece se as **3** tentativas falharem |
| "Builds indisponíveis" no canto da Início | a RPC não respondeu, mas o resto da tela abriu |
| a ficha abre com outro desenho | não deve mais acontecer. Se acontecer, o card não tem build publicada |
| barras zeradas com a nota certa no topo | a foto do motor congelou vazia — ver seção 4. Confira com o comando abaixo |
| tela em branco depois de trocar um `.js` | cache. **Ctrl+Shift+R** |

---

## 9 · ANTES DE DIZER QUE ESTÁ PRONTO

```
node --check <arquivo>              sintaxe (warning de ESLint derruba o Netlify)
node test/clube-novo-read-model.test.js    os 9 testes do contrato de leitura
```

Depois, no navegador: abrir, **Ctrl+Shift+R**, e percorrer Início → Ranking →
Elenco → Boxes → Como funciona → uma ficha, conferindo o Console limpo.

---

## 10 · PENDÊNCIAS ANOTADAS

- `dados-e-catalogos.js` tem **1,5 MB de dado congelado** dentro do arquivo. Deveria
  vir do banco.
- A rota `boxant` é normalizada em **4 lugares** diferentes. Frágil.
- Os nomes individuais de ímpeto (`all.str` do jogo) ainda não foram carregados —
  426 dos 440 aparecem como `Ímpeto <código>`.
- Rótulo "FUNÇÕES QUE EXERCE": discutida a troca para "MELHOR BUILD POR FUNÇÃO".
  **Não aplicada** — decisão em aberto.

## 09/09/2026 — correcao pontual completa e refila V12

Correcao de habilidade no Otimizador tambem atualiza atributos fisicos/internos, composicao e normalizacao persistidos; a ficha deve ler a nova publicacao, sem calculo local substituto. Os adicionais manuais continuam livres e as sugestoes automaticas respeitam bloqueios/gemeas por funcao. Refila e provas: `OTIMIZADOR/HABILIDADES-0909/CORRECAO-PONTUAL-E-REFILA.md`.


## Revisão das fotografias de Boxes — 09/09/2026

Autorização posterior: atualizar as avaliações congeladas para a normalização vigente, não apenas o desenho das estrelas. `clube_novo.box_avaliacao_revisao_0909` guarda nova fotografia por box/card/degrau, consumida por `site_novo_box_card_analise_snapshot_v1`; o leitor original e os 2.621 snapshots antigos permanecem preservados. Esta revisão substitui a orientação anterior de manter exclusivamente a avaliação antiga na tela.

Foram capturadas 20.094 fotografias (6.698 vínculos de cards, 1.022 boxes, três degraus), contendo 44.827 análises. Cards sem publicação elegível ficam sem avaliação; nenhuma nota foi inventada. As faixas de contratação e os motores permanecem iguais. Não há atualização contínua dessa fotografia: nova revisão exige decisão própria. Fontes: publicações exibíveis vigentes, melhor linha por função/degrau e topo global da função, como na régua de contratação existente.

Readback: zero divergências de identidade, nota, degrau ou estrelas inválidas. Cristiano Ronaldo `89138556572074`, Living Legends 2026, degrau 3: Centroavante fixo, linha 364310, nota 111,3542550014243, cinco estrelas. SQL de implantação: `4-DOCUMENTOS/NORMALIZACAO-0909/06-RENOVAR-AVALIACOES-BOXES.sql`. A correção é no banco e já é consumida pelo site publicado; não exige novo deploy nem pacote para a Máquina 2.
