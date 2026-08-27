# REVISÃO DA CONVERSA INTEIRA — o que foi pedido × o que foi feito
**25/08/2026.** Relidas as **59 mensagens** do Luis nesta sessão, do começo ao fim.
Feito antes de começar a executar, a pedido dele.

---

## ⛔ O QUE FICOU PARA TRÁS (e eu não tinha na lista)

### 1 · ORGANIZAR E RENOMEAR A PASTA — pedido, feito pela metade, nunca aplicado
> *"Você consegue organizar ela, excluindo os duplicados, organizando os arquivos
> juntando os relacionados em pastas internas e **renomeando os arquivos para uma forma
> mais intuitiva**? Pode apagar o que quiser, já fiz backup."*

Eu organizei — e entreguei dentro de `CLUBEFOOTBALL-OFICINA.zip`. **A pasta continua
como estava**, com o site velho solto na raiz. Foi isso que te fez abrir o arquivo
errado hoje. ⏳ **PENDENTE.**

### 2 · A PROVENIÊNCIA POR CAMPO — pedida hoje, ainda só no papel
> *"Fazer a data de como foi feita a coleta dos dados que a gente tem, e também onde foi
> feito. **Não pode esquecer disso.**"*

Hoje existe `clube.coleta` (3 registros: fonte, arquivo, linhas, quando) — mas a marca é
**por carga inteira**, não por campo. ⏳ **PENDENTE:** cada valor com sua fonte e sua data.

### 3 · O STATUS DE COMPLETUDE (3 escopos) — desenho existe, não foi carregado
> *"Existem insumos que o motor precisa pra rodar, eles têm que estar completos — porque
> se faltar, o motor roda mesmo assim e dá resultado errado, e a gente pensa que está
> certo."*

O GPT já desenhou exatamente isso em `cards_v2`: `motor_otimizacao_completo`,
`motor_bonus_completo`, `cadastro_nativo_completo`, `completeness_rule_version`,
`completeness_validated_at`, mais a tabela de avaliação com `missing_*`. **Só 6 de
42.807 cartas foram avaliadas** e a casa nova não trouxe nada. ⏳ **PENDENTE.**

### 4 · A AUDITORIA DOS MOTORES — a metade que falta do item C
Li a casca inteira, mas **os motores em Python não foram auditados** — que era o pedido
original. E o GPT deixou isso aberto **por ordem sua, desde 15/08**:
*"o motor de atributos nunca foi auditado atrás de número inventado ou valor padrão
disfarçado"*. Ganha peso agora, porque o motor vira o servidor que calcula. ⏳ **PENDENTE.**

### 5 · OS 127 AMBÍGUOS E 44 PENDENTES da lista de ímpetos
Estão carregados em `clube.impeto_divergencia` e marcados para o motor — mas a decisão
**um a um** nunca foi feita. ⏳ **PENDENTE** (decisão sua, carta a carta).

### 6 · A SKILL DE AUDITORIA ESTÁ DESATUALIZADA
Ela não conhece: a regra da **cobertura**, a regra **casa × matéria-prima**, o erro do
**parâmetro morto**, o erro da **fonte única escolhida em silêncio**, nem a **chave dupla
herdada**. Ou seja: a próxima sessão vai repetir o que erramos hoje. ⏳ **PENDENTE.**

---

## ✅ O QUE ESTÁ FEITO

| pedido dele | estado |
|---|---|
| analisar o site que voltou do GPT | ✅ |
| Falso nove ≠ Centroavante móvel | ✅ provado (Σ\|Δalvo\|=93,5) |
| chave única por função (não pelo nome) | ✅ `clube.funcao` por código |
| caderno de implementações | ✅ vivo, com as regras 00, 01 e 02 |
| perguntar ao GPT | ✅ 3 rodadas, respostas absorvidas |
| os 870 ímpetos errados: achar e MARCAR | ✅ 1.321 cartas · 5.711 builds marcadas |
| furo do nome das funções | ✅ as 6.824 cópias não migraram |
| banco vivo (princípio 0) | ✅ documentado, com dono de cada porta |
| pasta de trabalho única | ✅ regra 00 |
| manual técnico "como está / como vai ficar" | ✅ v2.2 |
| casa primeiro, moradores depois | ✅ |
| validar e testar toda implementação | ✅ skill + auditoria (46 conferências) |
| auditoria só para a migração | ✅ |
| siglas MC→MLG, MO→MAT, PD→PTD, PE→PTE | ✅ + achado GK→GO |
| script de navegador para coletar em paralelo | ✅ entregue |
| a casa nova (fases 0-8) | ✅ |
| **não publicar** | ✅ nada foi publicado |
| ler a casca INTEIRA | ✅ 3,0 MB · 14.500 linhas |
| cruzar tudo com o banco | ✅ |
| falta na casca ou no banco? | ✅ 2.608 estavam em casa |
| o motor não pode ficar exposto | ✅ desenho (a conta muda de lado) |
| a nota da tela = a nota do motor | ✅ desenho (é o mesmo motor) |
| o Alvo é ferramenta do admin | ✅ resolvido no servidor, não na tela |
| recoletar tudo | ✅ decidido |
| ordenar pelo overall que temos | ✅ decidido |
| **a auditoria de cobertura** | ✅ **IMPLEMENTADA** (migração 0021) |
| casa × matéria-prima | ✅ regra 01 |

---

## ⏳ O QUE ESTÁ PLANEJADO E AINDA NÃO EXECUTADO

| item | onde está |
|---|---|
| fechar a porta do molde (`arows`/`frows` públicos) | Etapa 0 |
| os 11 insumos do legado → casa | Etapa 1 |
| separar `carta` de `carta@posição` (o cadastro único) | Etapa 2 |
| o que precisa nascer (FILA, B5V, formações, textos, escadas) | Etapa 3 |
| a casca emagrece + simulador no servidor | Etapa 4 |
| a coleta (1.300 campos + 28.776 cartas + imagens) | Etapa 5 |
| consertos: `eval()`, senha em texto limpo, 22 funções duplicadas, 2º popstate | Etapa 6 |
| **rotação das chaves vazadas em 05/08** | por ÚLTIMO, antes de lançar (ordem sua) |
| login + comercial (Stripe, entitlement real) | depois da casa |
| a RODADA ÚNICA do motor | **ordem sua**, na sua máquina |
| decisão: cadeado comercial 🔒 do MODO B fica ou sai | pergunta aberta |

---

## A ORDEM ACORDADA

```
AGORA        o coletor pronto → roda sozinho por dias
EM PARALELO  1 · os 11 insumos do legado (a coleta não traz)
             2 · fechar a porta do molde
             3 · o cadastro único (carta × carta@posição)
             4 · a casca emagrece + o simulador
             + os 6 esquecidos acima, encaixados: a pasta (1) e a skill (6) são
               rápidos e entram já; proveniência (2) e completude (3) entram
               junto com a Etapa 1, porque são a mesma carga; a auditoria dos
               motores (4) entra antes do simulador, porque é ele que vai rodar
QUANDO A COLETA FECHAR
             5 · carrega, compara com o que o motor usou, marca o que mudou
             6 · a rodada única (ordem sua)
```
