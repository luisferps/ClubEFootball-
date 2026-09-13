# CONTRAPROVA — o cálculo físico do Bonificador

**04/09/2026 · somente leitura · nada foi executado, alterado ou reprocessado**

> **CONTRAPROVA HISTÓRICA ENCERRADA.** O defeito físico provado neste documento
> foi corrigido pela V10. Em 07/09, a correção de estilo gerou a identidade V11,
> sem desfazer a fórmula física aprovada. O estado vigente está em
> `BONIFICADOR/REGISTRO-OPERACIONAL-CORRECAO-ESTILO-V11.md`.

Esquema usado: `clube_novo`. O `clube` aparece uma vez só, como prova histórica da
régua. Nenhuma linha, contrato, lote, versão ou publicação foi tocado.

---

# 1 · VEREDITO

**CONFIRMADO. O cálculo físico atual está errado.** Não é suspeita: é reprodutível
linha a linha, e a causa está escrita no código.

O defeito não é um sinal trocado. São **três defeitos independentes** que se somam,
e cada um sozinho já invalidaria o número.

A medida mais crua do estrago está na própria tabela de regras:

| `direcao` | regras | o que o Python faz |
|---|---:|---|
| `-1` menor é melhor | **62** | trata como "maior é melhor" — **sinal invertido** |
| `0` não conta | **105** | soma na nota **e** no divisor — **peso fantasma** |
| `+1` maior é melhor | **61** | correto |

**167 das 228 regras (73%) são aplicadas erradas.** As 61 certas são as que estão
certas por acaso — são justamente aquelas em que "não inverter" coincide com a regra.

E o divisor denuncia sozinho: o Python usa **16 fixo nas 19 funções**, enquanto o
peso que deveria contar varia de **6 a 15**:

```
Atacante criador ....... deveria contar 10 · Python usa 16
Zagueiro de combate .... deveria contar  6 · Python usa 16
Ala finalizador ........ deveria contar  6 · Python usa 16
Goleiro defensivo ...... deveria contar 15 · Python usa 16
```

**Nenhuma das 19 funções escapa.** Todas têm pelo menos uma medida neutra somada
indevidamente.

---

# 2 · CASO MESSI — refeito do zero

Card `89136409091415`, "Big Time FC Barcelona 18 Apr '07", 170 cm / 67 kg.
Função `Atacante criador` (`funcao_id` 14).

Confirmei o pareamento antes de calcular: no `motor-e-ficha-base.js`, o `MF_DIRF` de
`"Atacante criador"` e o de `"Ponta criadora"` são **idênticos, medida por medida**.
É o mesmo perfil físico com nome novo — o pareamento do seu levantamento está certo.

## As 12 medidas, medidas no banco

| medida | valor | direção | peso | nota aprovada | contribuição aprovada | parcela do Python |
|---|---:|---:|---:|---:|---:|---:|
| **Altura** | 170 | −1 | 5 | −2 | **+10** | 0,00 |
| Compr. braço | 5 | −1 | 1 | −1 | **+1** | 0,50 |
| Alt. ombro | 2 | −1 | 1 | −2 | **+2** | 0,00 |
| Tam. pescoço | 6 | +1 | 1 | 0 | 0 | 0,50 |
| Compr. pescoço | 9 | +1 | 1 | 0 | 0 | 0,75 |
| Larg. ombro | 9 | −1 | 1 | 0 | 0 | 0,75 |
| Coxa | 9 | **0** | 1 | — | **fora** | 0,75 |
| Panturrilha | 10 | **0** | 1 | — | **fora** | 1,00 |
| Cintura | 3 | **0** | 1 | — | **fora** | 0,00 |
| Peito | 9 | **0** | 1 | — | **fora** | 1,00 |
| Tam. braço | 7 | **0** | 1 | — | **fora** | 0,75 |
| Compr. perna | 8 | **0** | 1 | — | **fora** | 0,75 |
| | | | | **soma 13** | **teto 20** | **soma 6,75 · divisor 16** |

## As duas contas

```
APROVADA   13 / 20 × 1,5                    = +0,9750
ATUAL     ((6,75 / 16) × 2 − 1) × 1,5       = −0,234375  →  −0,2344
```

**Gravado no banco: `−0,2344`.** Reproduzido exatamente.

## A resposta

> **O valor correto é `+0,9750`.**

Nem `−0,2344`, nem `+0,9000`. E a leitura em português do defeito é essa:
**os 170 cm do Messi são a maior vantagem dele nessa função — valem +10 dos 13
pontos — e a conta atual os transformou em zero.** A altura é a única medida de
peso 5; errar o sinal dela é errar metade da conta.

⚠️ São **2 linhas** desse card nessa função (com e sem ímpeto condicional), ambas
com o mesmo `−0,2344`. As duas mudam.

---

# 3 · CAUSA — as cinco diferenças, uma a uma

## Regra aprovada (`1-SISTEMA/motor-e-ficha-base.js`)

```js
mfNota(v,c)  = v<=c[0] ? -2 : v<=c[1] ? -1 : v<=c[2] ? 0 : v<=c[3] ? 1 : 2;
mfSoma       = Σ  mfNota(medida) * mfDir(medida,funcao) * MF_PESO(medida)
MF_TETO      = Σ  MF_PESO(medida)*2   ... SOMENTE onde mfDir != 0
mfPct        = clamp(-100,+100, soma/teto*100)
fisBonus     = pct/100 * CORPO_MAX          // CORPO_MAX = 1.5
```

## Código atual (`2-MOTORES/BONIFICADOR/motor_bonus.py`, linhas 245-285)

```python
def nota_da_medida(valor, cortes):
    n = 0
    for c in cortes:
        if valor >= c: n += 1      # <- DIFERENÇA 5
    return n / 4.0                 # <- 0..1, não -2..+2

if (regra.get('direcao') or '') == '-':   # <- DIFERENÇAS 1, 2 e 3
    n = 1.0 - n
soma += n * p
peso_total += p                    # <- DIFERENÇA 4: soma TODOS os pesos
bonus = round((pct * 2 - 1) * corpo_max, 4)
```

### Diferença 1 — o tipo do sentido

O banco declara o formato na própria migração
(`SQL/MIGRAR-REGUA-CANONICA-CLUBE-NOVO-V1.sql`, linha 48):

```sql
direcao integer not null check (direcao in (-1,0,1))
```

E a régua publica o inteiro cru para o Python
(`MIGRAR-REGUA…`, linha 216): `'direcao', m.direcao`. Conferido na resposta viva de
`bonificador_regua_v2()`: sai `"direcao": -1`, `"direcao": 0`, `"direcao": 1`.

**O Python compara esse inteiro com o texto `"-"`.** `-1 == '-'` é sempre falso.

### Diferença 2 — a comparação nunca dispara

Consequência direta: as **62 regras** de "menor é melhor" recebem o tratamento de
"maior é melhor". Card baixo em função que quer baixo é punido em vez de premiado.
É literalmente o caso Messi.

### Diferença 3 — o `or ''` destrói o zero antes da comparação

Detalhe venenoso que merece registro próprio: em Python, `0` é *falsy*. Então

```python
regra.get('direcao') or ''     # com direcao = 0  →  ''
```

O zero **vira string vazia antes de qualquer teste**. Mesmo que alguém consertasse a
comparação para `== -1`, o `or ''` continuaria apagando as 105 regras neutras. São
dois bugs empilhados na mesma linha.

### Diferença 4 — as medidas neutras entram na soma e no divisor

O Python não tem nenhum `continue` para `direcao == 0`. As **105 regras** que não
deveriam existir naquela função:

- entram no numerador com a nota delas;
- entram no denominador com o peso delas.

É por isso que o divisor é 16 em todas as 19 funções: `5 + 1×11 = 16`, o peso total
das 12 medidas, sempre. O teto aprovado é `2 × Σpeso(direcao≠0)` — e varia.

### Diferença 5 — a borda dos cortes

O JS usa `v <= corte`; o Python conta `v >= corte`. As duas contas coincidem em todo
lugar **exceto exatamente nos quatro valores de corte**, onde divergem em um degrau.

🔑 **Um detalhe algébrico que importa para o plano:** as diferenças 1-4 são as
estruturais. Se todas as direções fossem `+1`, as duas fórmulas seriam
**algebricamente idênticas** (`n_js = 4·n_py − 2` faz uma virar a outra). Ou seja: a
fórmula do Python não é uma fórmula diferente — é a fórmula certa **com o sentido e a
exclusão amputados**. Isso é bom: o conserto é cirúrgico, não é reescrita.

### Sobre a conta híbrida de `+0,9000`

Confirmo sua conclusão: **não serve.** Reconstruí a híbrida (corrige sentido e
exclusão, mantém a borda `>=` e a escala 0..1) e ela diverge da regra aprovada em
**57.501 dos 57.582** resultados que consegui recalcular.

⚠️ Meu número não bate com os `46.717` do seu levantamento. Como a híbrida não é a
regra oficial de nenhum dos dois lados, não vale gastar rodada reconciliando: as
duas medições chegam à mesma decisão — **a híbrida está fora.** Só registro que os
números divergem para ninguém citar o meu como confirmação do seu.

---

# 4 · AUTORIZAÇÃO — não existe. E o que existe diz o contrário.

**Não encontrei nenhuma ordem do Luis para trocar a regra física aprovada pela conta
atual.** Não deduzo autorização e não achei nenhuma.

O que encontrei é o oposto — uma autorização **explicitamente limitada**, no
`CHECKLIST-MIGRACAO-CLUBE-NOVO-2026-08-28.md`:

```
linha 364:  [x] usuário autorizou corrigir exclusivamente a referência,
                sem mudar o molde;

linha 216:  ...composição dos moldes ou regras de negócio sem nova
            autorização específica e prova;
```

A autorização foi para trocar a **chave** de busca do molde (rótulo `"Centroavante
fixo"` → `funcao_id`). Isso é referência. **A matemática do sentido e da exclusão
nunca esteve nessa autorização.**

E o `MANUAL-DO-BONIFICADOR.md` §9 abre com a trava que foi violada:

> "É proibido alterar fórmulas matemáticas, pesos, cortes, ordem de cálculo,
> composição dos moldes ou regras de negócio do Bonificador (…) sem nova
> autorização explícita e específica do usuário, precedida de prova própria."

## Respondendo às suas três perguntas

**1. Por que o lote rodou sabendo da incompatibilidade?**

Porque ela foi **classificada como observação, não como bloqueio**. O manual §9
registra o defeito no meio de uma lista chamada *"três comportamentos pré-existentes
ficam documentados separadamente"*, e encerra o item com:

> "`molde_corpo.direcao` é numérico (`-1/0/1`), enquanto o código histórico testa o
> texto `"-"`. **Esta migração não corrige essa fórmula.**"

"Esta migração não corrige" é uma frase de escopo. Ela declara o que a migração não
faz — e não declara que **nada pode rodar** enquanto não for corrigido. Nenhum
documento marcou isso como impeditivo de produção. Não achei nenhuma autorização
para rodar assim; achei a **ausência de um freio**, que é coisa diferente e pior:
ninguém decidiu rodar com o defeito, ninguém decidiu não rodar, e o lote foi.

**2. Existiu ordem expressa?**

**Não.** A única prova de autorização no assunto é a linha 364 acima, e ela exclui
o molde por escrito.

**3. Por que foi classificado como preservação da fórmula em vez de bloqueio?**

Porque a preservação foi medida **contra o retrato anterior, não contra a regra
aprovada**. O critério aplicado foi *"o comportamento é o mesmo de antes"* — e era
mesmo. O critério que faltou foi *"o comportamento é o que o Luis aprovou"*. A
próxima seção mostra que os testes foram construídos em cima do critério errado, e
por isso passaram todos.

🔑 E há um agravante que achei no Projeto. Em **15/08**, o documento
`ESTADO-1508-B-O-MODAL-a-nomenclatura-e-o-que-ficou-aberto.md` já registrava, na
lista "O QUE CONTINUA ABERTO":

> "**O bloco FÍSICO**: 11 das 16 medidas com peso 0 no `MF_DIRF` (…). Ou o molde
> ficou defasado, ou o documento. **Decisão do Luis.**"

A existência de medidas neutras foi levantada, marcada como decisão sua — e **nunca
decidida**. Treze dias depois a migração implementou o tratamento delas por conta
própria, tratando todas como se contassem.

---

# 5 · TESTES — a falha de cobertura está confirmada

Os três testes que você apontou fazem exatamente o que você desconfiou. Li os três.

## `SQL/VALIDAR-PONTE-CANONICA-MOLDES-V1.sql` — o mais grave

Ele compara `old_formula` com `new_formula`. Li as duas. **São a mesma fórmula.**
Ambas contam `>= corte`, ambas dividem por `sum(peso)` de todas as medidas — e,
o ponto decisivo:

```sql
new_rules as (
  select ...
    (e.value ->> 'direcao')::numeric as direcao,     -- <- EXTRAI a direção
    ...
new_formula as (
  select ... sum(( ... ) * nr.peso) / sum(nr.peso) ...   -- <- NUNCA a usa
```

**A validação extrai `direcao` e não a usa em lugar nenhum da matemática.**
Divergência zero ali não era um resultado — era uma identidade algébrica. O teste
comparou a fórmula defeituosa consigo mesma e, claro, não achou diferença.

## `TESTES/testar_trava_formula_ponte_moldes.py`

Compara o AST de `bonus_do_corpo` antes/depois, pulando a linha que mudou a chave.
Isso prova **imutabilidade**, não **correção**. É um congelador: se o código estava
errado antes, ele garante que continue errado. Cumpriu o papel dele — o papel é que
era insuficiente sozinho.

## `TESTES/testar_migracao_bonificador.py`

```python
assert bonus_do_corpo(regua["molde_corpo"], carta_controle["corpo"], 1, ...) is not None
```

Exige apenas que a função **não devolva vazio**. Qualquer número passa: `−0,2344`,
`+0,9750`, `+42`. Não há valor esperado em lugar nenhum.

## Veredito dos testes

**Nenhum dos três jamais poderia ter pego este defeito.** Não é que falharam:
eles testam outra coisa. A cobertura que falta, e que precisa entrar antes de
qualquer reprocessamento:

| caso a cobrir | por quê |
|---|---|
| `direcao = -1` | as 62 regras hoje invertidas |
| `direcao = 0` | as 105 hoje somadas indevidamente — conferir que saem do numerador **e do denominador** |
| `direcao = +1` | não regredir as 61 que estão certas |
| valor **exatamente** em cada um dos 4 cortes | a diferença 5, a borda `<=` × `>=` |
| valor abaixo de `corte1` e acima de `corte4` | as pontas `-2` e `+2` |
| altura com **peso 5** | é metade do teto; errar aqui domina o resultado |
| teto por função | conferir que é `2×Σpeso(direcao≠0)` e que **varia** entre as 19 — se der 16 em todas, o defeito voltou |
| limites `-1,5` / `+1,5` | o `clamp` |
| soma do `bonus_fisico_detalhe` | tem de fechar **exatamente** com `bonus_fisico_total` |
| **caso ouro: Messi `89136409091415` × função 14 = `+0,9750`** | o caso de controle |

⚠️ **O detalhamento também está contaminado.** `bonus_do_corpo_writer` (linhas
288-310) deriva as contribuições de `(2·nota − 1)·peso/peso_total·corpo_max`, com a
mesma escala 0..1, os mesmos pesos fantasmas e o mesmo sentido perdido — e joga todo
o resíduo de arredondamento na última medida. Corrigir só o total deixaria a ficha
mostrando um detalhamento que não soma o total exibido. **Os dois se corrigem juntos.**

---

# 6 · ALCANCE — medição independente

Recalculei a regra aprovada em SQL, direto no `clube_novo`, e comparei com
`bonus_fisico_total` gravado. Somente leitura.

| medida | seu levantamento | **minha medição** |
|---|---:|---:|
| resultados avaliados | 57.950 | **57.582** |
| coincidem por acaso | 264 | **259** |
| mudariam | 57.686 | **57.323** |
| subiriam | 25.289 | **25.148** |
| cairiam | 32.397 | **32.175** |
| menor alteração | −2,1719 | **−2,1719** ✅ |
| maior alteração | +2,0625 | **+2,0625** ✅ |
| alteração absoluta média | 0,5134 | **0,5130** |
| cards afetados | 3.573 | **3.555** |
| funções afetadas | 19 | **19** ✅ |

## A diferença é explicada, e é um achado por si só

```
57.950 resultados em build_bonificador
57.582 que consegui recalcular
   368 ÓRFÃOS — não têm nenhuma linha apontando para eles
```

**368 resultados do Bonificador não estão ligados a nenhuma `build_linha_card`.**
Eles existem na tabela e ninguém os referencia. Sua contagem de 57.950 os inclui; a
minha não, porque sem linha não há `funcao_id` e não há como recalcular.

Isso não muda nenhuma conclusão — as duas medições dão a mesma resposta com
diferença de 0,6% — mas **os 368 precisam de destino explícito no plano**, e ninguém
tinha reparado neles até agora.

Confirmei também os outros dois números operacionais:

```
2.148 linhas com resultado do Bonificador e SEM resultado do Otimizador
55.434 linhas publicadas  (publicacao_fingerprint preenchido)
```

*(Seu levantamento fala em 2.516 sem ligação ao Otimizador; medi 2.148 agora. A
outra frente está mexendo no `clube_novo` — o número é móvel, e é exatamente por
isso que ele é uma condição de partida, não um dado fixo.)*

## Distribuição da alteração absoluta

| alteração | seu | **meu** |
|---|---:|---:|
| nenhuma | 264 | **259** |
| até 0,25 | 16.936 | **16.844** |
| 0,25 a 0,50 | 15.928 | **15.840** |
| 0,50 a 1,00 | 18.043 | **17.922** |
| 1,00 a 1,50 | 5.994 | **5.940** |
| acima de 1,50 | 785 | **777** |

**Confirmado: todo o corpo publicado está afetado.** Não existe recorte seguro. Não
dá para consertar "só os piores" — 99,5% dos resultados mudam, e a média de meio
ponto é o suficiente para virar posição de ranking em massa.

---

# 7 · PLANO MÍNIMO SEGURO — proposto, não executado

**Nada abaixo foi feito.** Cada etapa depende da sua autorização, e as etapas 4 em
diante dependem do resultado medido da anterior.

## Condições de partida (bloqueiam o início)

1. **A outra frente termina primeiro.** Enquanto houver linha com Bonificador e sem
   Otimizador, o alcance é móvel e a conferência não fecha. Medir até estabilizar.
2. **Decidir o destino dos 368 órfãos** antes de tocar em qualquer coisa.
3. **Assentar o lote preso em `rodando`** pelas portas oficiais
   (`controlar_v1('pausar')` → `assentar_parada_v1('pausar')`), nunca por UPDATE.
   ⚠️ **Não reaproveitar esse lote** para o reprocessamento — ele carrega o snapshot
   e o histórico da rodada defeituosa. O novo trabalho nasce em lote novo.

## Etapa 1 · Corrigir o fonte — e só o fonte

Em `motor_bonus.py`, `bonus_do_corpo` e `bonus_do_corpo_writer` passam a implementar
a regra do `motor-e-ficha-base.js`, **sem inventar nada**:

- nota em 5 faixas `-2..+2` com `v <= corte`;
- `direcao` lida como **número**, multiplicando a nota;
- `direcao == 0` → `continue`: fora do numerador **e** do denominador;
- teto `= Σ peso×2` só das medidas com `direcao != 0`;
- `clamp(-1,5 … +1,5)`;
- o detalhamento derivado da **mesma** escala, somando exatamente o total.

⛔ Nenhum peso, corte, ordem ou composição de molde é tocado. O que muda é
tradução de regra, não regra.

## Etapa 2 · Versão e assinatura novas — inegociável

```
motor_versao:  v9-3108-clube-novo-writer-v1   ->   v10-0409-fisico-regra-aprovada
```

O `resultado_fingerprint` muda por consequência. **É isto que impede a mistura**:
com versões diferentes, nenhuma consulta confunde resultado velho com novo, e dá
para contar os dois lados a qualquer momento.

## Etapa 3 · Provar antes de rodar — a trava que faltou da primeira vez

Rodar a bateria da seção 5 **contra valores esperados**, com o caso ouro do Messi em
`+0,9750`. Só depois disso qualquer coisa roda.

🔑 **Regra nova, e é a lição do episódio:** um teste que compara o novo com o retrato
anterior não prova correção — prova imobilidade. **Todo teste de fórmula tem de ter
pelo menos um valor esperado calculado à mão a partir do documento aprovado.**

## Etapa 4 · Manter fonte, componente e executável na mesma versão

`motor_bonus.py`, `BonificadorComponente.bin` e `Bonificador ClubEfootball.exe` saem
juntos. ⚠️ Este sistema já foi mordido por `.exe` com código congelado — se os três
não subirem juntos, a Máquina 2 roda a versão velha em silêncio.

## Etapa 5 · Gerar o novo, sem apagar o velho

Os 57.950 resultados atuais **ficam**. São histórico e estão referenciados por
retratos de publicação. Apagar não é conserto — é perder a prova do que aconteceu.

Os novos resultados nascem ao lado, com a versão nova. A troca é da **ligação**
(`build_linha_card.build_bonificador_id`), controlada e reversível, não da linha.

⚠️ O gravador atual é idempotente e **recusa** gravar em linha que já tem
Bonificador. O plano precisa de um caminho explícito de substituição — que **não
existe hoje** e é a peça que falta desenhar. É o item mais delicado do plano e não
vou improvisá-lo aqui.

## Etapa 6 · Tirar da exposição antes de trocar

Retirar da publicação as combinações antigas **antes** da troca. Se a nota vier da
linha velha e o detalhamento da nova, a tela mostra uma ficha que não fecha consigo
mesma — e é a única parte disso que o seu usuário final enxerga.

## Etapa 7 · Recalcular nota final e publicar por linha

A finalizadora canônica é chamada quando chega o segundo resultado compatível. Ela
normaliza o vetor real do Otimizador, soma o bônus V10, grava a nota, atualiza o
read model incremental e ativa a linha na mesma transação. Um retry durável cobre
eventos perdidos; não existe passagem global nem corte manual.

## Etapa 8 · ⛔ O Otimizador NÃO roda

O defeito é exclusivamente do bônus físico. Conferido no seu próprio caso de
controle: nota bruta `466,8` e normalizada `110,53405193532582` são **idênticas** no
legado e hoje. O Otimizador está certo e não tem nada a refazer.

## Prestação de contas

Cada etapa entrega, antes e depois: contagem, readback e a lista do que mudou.
Nenhuma etapa começa sem a anterior conferida.

---

# O QUE EU NÃO FIZ

Não alterei código, banco, contrato, fila, lote, publicação, versão ou executável.
Não reabri linha. Não rodei lote. Não apaguei nada.

O lote terminou sozinho às **13h05** e não grava desde então — não há sangramento em
curso. **Mas ele continua marcado `rodando`**, e enquanto estiver assim, um clique no
`RODAR-LOTE-BONIFICADOR.bat` é recusado pela trava de estado. Isso hoje está a nosso
favor: é um freio acidental. Não o solte antes da decisão.
