# CONTEXTO E PLANO — sessão 12/09/2026
## ClubEfootball / Sistema Encaixe — o que foi feito e o que falta implementar

Documento de passagem. Contém (A) o estado do sistema, (B) tudo que foi
CONSERTADO nesta sessão e já está aplicado, (C) as descobertas de método que
mudam como se decide daqui pra frente, (D) a decisão do molde v6 com as
medições que a sustentam, e (E) o plano de implementação passo a passo.

Nada aqui é suposição: todo número foi medido no banco e a consulta está junto.

---

# A. O SISTEMA

- **Banco:** Supabase, projeto `trqqpsnafpbudtvvicch`.
- **Esquema ATIVO: `clube_novo`.** Todo o resto é legado. O esquema `clube` é
  a base antiga e não deve ser tocado.
- **Site (Site Novo):** `https://imaginative-granita-ace1ca.netlify.app`,
  publicado por Netlify Drop (arrastar o zip na aba Deploys do projeto
  `imaginative-granita-ace1ca`). Fonte na máquina 1, pasta `Site Novo`.
- **Máquina 1** (`C:\Users\Luis Fernando\Downloads\ClubEFootball--main\ClubEFootball--main`):
  oficial. Manuais e código-fonte ficam atualizados aqui.
- **Máquina 2** (`C:\Users\luis-\Downloads\ClubEFootball--main`): só roda o
  Otimizador e o enviador de resultados. Pode ficar bagunçada.

## As três peças de cálculo

1. **Otimizador** — escolhe barras, ímpeto, técnico e habilidades para
   maximizar a nota (B1). Roda LOCAL, na máquina 2, a partir de um pacote
   selado baixado do banco.
2. **Bonificador** — aplica bônus de altura, IA e estilo de jogo sobre a build.
3. **Tela** — o site lê o resultado publicado.

## Conceitos que aparecem o tempo todo

- **valor interno x valor de tela.** `build_otimizador.atributos_internos` é o
  valor COM a valoração das habilidades (passa de 99). `atributos_finais` é o
  número que a tela do videogame mostra. A régua mede o INTERNO.
- **Molde** = por função, para cada um dos 26 atributos, um `alvo` e um `peso`.
  Tabela `clube_novo.otimizador_molde`, PK `(versao, funcao_id, codigo_atributo)`.
- **Régua** = `public.otimizador_regua_v2()`. Lê `max(versao)` do molde e monta
  o contrato que vai selado dentro do pacote local.
- **contrato_fingerprint** = hash da régua. Muda quando o molde muda. É o que
  distingue build calculada com régua nova de build com régua velha.

---

# B. O QUE FOI CONSERTADO NESTA SESSÃO (já aplicado)

## B1. Fila do Otimizador — o HTTP 400 da fotografia

**Sintoma:** na máquina 2, `BAIXAR-FILA-NOVA-1209.bat` devolvia
`RuntimeError: fotografia recusada pelo banco: HTTP 400`.

**Causa 1 — estado do lote.** `public.otimizador_producao_pacote_local_manifesto_v2`
exige `estado in ('pausado','concluido')`. O preparo entrega o lote em `parado`.
O enviador de resultados (`public.otimizador_producao_importar_json_local_v1`)
exige o mesmo `estado = 'pausado'`.

> **`pausado` é o estado operacional do ciclo local inteiro** — baixar o pacote
> e enviar resultado. Caminho oficial para sair de `parado`, sem UPDATE cru:
> ```sql
> select public.otimizador_producao_controlar_lote_v3('<lote>','iniciar');
> select public.otimizador_producao_controlar_lote_v3('<lote>','pausar');
> ```
> Com zero linhas em `processando`, `pausar` grava `pausado` direto.

**Causa 2 — lentidão.** O manifesto levava **46 s de média e 119 s no pior
caso** (medido em `pg_stat_statements`), porque a fila cresceu para 192 mil
linhas e ele monta um hash sobre todas. O cliente local desiste em 90 s e
traduz qualquer resposta ruim como 400 — por isso funcionava às vezes.

O plano do banco fazia *nested loop* com 192.276 voltas, lendo 1,43 milhão de
páginas. Correções aplicadas:

```sql
create index build_linha_card_pendente_fila_idx
  on clube_novo.build_linha_card (id)
  include (funcao_id, posicao_id, impeto_condicional_codigo,
           impeto_condicional_nivel, estado)
  where estado_otimizador = 'pendente';

create index carta_nivel_evidencia_coerente_idx
  on clube_novo.carta_nivel_evidencia_v1 (card_id)
  include (nivel_maximo, orcamento_real, captura_id)
  where nivel_maximo >= 1 and orcamento_real = 2 * (nivel_maximo - 1);

alter function public.otimizador_producao_pacote_local_manifesto_v2(uuid)
  set enable_nestloop = off;
```

**Resultado: 46 s → 4 a 9 s.** Buffers de 1,43 M para 151 mil.

## B2. Três exclusões que a fila escondia

**1.571 cartas sem evidência física** (12.955 linhas retiradas).
`clube_novo.otimizador_prioridade_orcamento_v1` exige linha em
`clube_novo.carta_nivel_evidencia_v1` com `nivel_maximo >= 1` e
`orcamento_real = 2*(nivel_maximo-1)`. 1.561 dessas cartas são
`tipo_carta_id = 'player_delete_list'` (fora do jogo); 10 são cartas comuns
(Raphinha 83, Rúben Dias 82, De Paul 82, Pavlović 81, Grimaldo 81,
Dean Henderson 81, Malen 80, Akliouche 80, Lamlaoui 79, Sawakami 76).
O criador do lote as aceita, a fotografia as exclui — seriam pendentes eternas.
Marcadas `estado_otimizador='interrompido'` com motivo gravado.

**131.938 linhas pendentes presas em lotes aposentados.**
`preparar_fatia_v5` cria linhas NOVAS em `build_linha_card`; não reaproveita as
antigas. Quando um lote é aposentado, as linhas dele que estavam `pendente`
continuam `pendente` apontando para o lote morto — e a máquina 2 só processa o
lote vivo. Estavam em 7 lotes `concluido`. 124.504 eram gêmeas exatas de linhas
da fila nova. Retiradas.

**1.184 cartas de ímpeto condicional excluídas por contrato velho.**
`public.otimizador_producao_criar_lote_integral_v6` filtra
`not exists (carta_impeto_jogo where condicional)`. Mas o contrato do pacote v2
já declara `impetos_condicionais='por_degrau'`, `preparar_fatia_v5` já
multiplica a carta pelos 3 degraus, e o banco já tem 29.511 linhas condicionais
concluídas com 27.430 publicadas. Foram inseridas à mão em
`otimizador_lote_producao_candidata_v5`, `preparo_total` somou 1.184, o lote
voltou a `preparando` e o preparo rodou até 20.602/20.602.

> ⚠️ **PENDÊNCIA VIVA:** `criar_lote_integral_v6` continua com esse filtro.
> **Toda fila integral nova vai precisar do aditivo manual das condicionais**
> até isso ser corrigido no corpo da função.

## B3. Fila 1209 — estado atual

| | |
|---|---|
| Lote | `12090000-0000-4000-8000-000000001209` |
| Estado | `pausado` |
| Candidatas preparadas | 20.602 / 20.602 |
| Linhas criadas | 205.231 |
| **Linhas pendentes** | **192.276** (19.030 cartas) |
| Com ímpeto condicional | 35.856, por degrau |
| Bloco 1 (orçamento > 0) | 113.642 linhas / 11.999 cartas |
| Bloco 2 (orçamento = 0) | 78.634 linhas / 7.031 cartas |
| Linhas pendentes fora dessa fila, no banco inteiro | **0** |
| Fórmula | `a1cc830af3366e2d0c9ac12138d892058b3e57ed216e43d68242d105b33cb9d2` |
| Motor | `otimizador-fila-producao-v3-local-20260909-habilidades-v12` |

**Ordem da fila:** bloco 1 = cartas com `orcamento > 0`; bloco 2 = `orcamento = 0`
(inclui 1/1 e 0/1). Dentro de cada bloco: overall decrescente, desempate por
`card_id collate "C"`, depois função, posição e degrau condicional.
A `ordem_fila` foi renumerada com offset temporário `+100000000` por causa do
`UNIQUE (lote_id, ordem_fila)`.

> Observação de campo: o cliente local coloca as cartas **sem overall coletado**
> na frente, por regra própria dele. São 356 linhas do bloco 1. Depois disso ele
> segue a ordem do pacote. Não é defeito.

## B4. Site Novo — coluna JOGO na ficha

O banco **já publicava** `valor_jogo` (= `atributos_finais`) e a tela não
mostrava. Adicionada a coluna JOGO entre BASE e FINAL, nos cinco grupos.

- `ficha.js`: `group-jogo` no cabeçalho e `attr-jogo` na linha, lendo
  `item.valor_jogo`.
- `ficha.css`: grid de 4 colunas escopado em `#attribute-columns`
  (`minmax(0,1fr) 38px 38px 50px`) para não afetar o editor de build, que
  continua com três colunas.
- `ficha.html`: cache-buster `?v=2026091203` em `ficha.css` e `ficha.js`.
- Publicado. Pacote: `Site Novo/site-novo-deploy-1209b.zip`.

Conferido no ar (Andrea Pirlo): Drible 78 / 92 / 99 · Passe rasteiro 85 / 95 / 116.
O selo "Régua antiga" continua funcionando.

---

# C. DESCOBERTAS DE MÉTODO (valem daqui pra frente)

## C1. A régua tem TETO DE GANHO no 9º ponto acima do alvo

Lido em `2-MOTORES/OTIMIZADOR/regua.py`:

```python
DEG = [1, .88, .76, .64, .52, .40, .28, .16, .04]   # nove degraus
TETO_PUN = 9    # a punição também para no 9º ponto abaixo
```

- **Acima do alvo:** ganha `DEG[k] * peso` no k-ésimo ponto. **Do 10º ponto
  acima em diante o ganho é ZERO.**
- **Abaixo do alvo:** pune, com teto no 9º ponto.
- **Peso 1 (acessório) não pune:** `if peso == 1: t[v] = 0.0`.

**Consequência prática, e foi a chave de tudo:** quando um card está 9 pontos
acima do alvo, o motor PARA de investir naquele atributo — o ponto seguinte
não vale nada, com peso 3 ou com peso 12. Quem destrava é o ALVO, que move a
janela de ganho. O PESO só multiplica o que já existe.

## C2. O PESO não se escolhe — ele cai da posição do alvo na fila

Regra do método (skill `truefootball-peso`), aplicada por função:

```
alvo arredondado PARA CIMA
alvo >= 80 -> entra na fila, do MAIOR alvo para o menor:
    5 primeiros -> peso 12  (Indispensável)
    4 seguintes -> peso  7  (Desejável)
    4 seguintes -> peso  3  (Útil)
    resto       -> peso  1  (Acessório)
alvo == 79 -> peso 1 ;  alvo < 79 -> peso 0
Cobrança de falta -> teto 1, SEMPRE
```

Desempate observado no molde atual: por `indice_otimizador` crescente.

**Exceções cravadas à mão que EXISTEM e não podem ser quebradas:**
Goleiro Salto 7→3; Goleiro Passe rasteiro, Passe alto e Potência de chute 0→1;
Cobrança de falta teto 1.

> Por isso **não se recalcula o peso de todas as funções por script** — isso
> apagaria as exceções do goleiro. Mexe-se só na função tratada.

## C3. A nota da tela já é normalizada entre funções

Medido: o topo de cada família chega quase ao mesmo aproveitamento sobre o
próprio teto — MEIO 97,8%, DEFESA 97,2%, ATAQUE 97,0%, GOLEIRO 93,8%.
A régua é justa no topo. O que separa as famílias no ranking é a **mediana**:
MEIO −25,0 · ATAQUE −36,8 · DEFESA −58,0 · GOLEIRO −80,1.

Ou seja: defesa e goleiro aparecem pouco no ranking geral porque a MASSA de
cards está longe dos próprios alvos, não porque a fórmula seja injusta.
**Isso é assunto de molde por função, não de normalização.** Fica em aberto.

## C4. Habilidade nativa x adicional

`carta_habilidade_jogo` = nativa (de fábrica, não ocupa slot).
`build_otimizador.habilidades_adicionais` = as que o motor escolheu (ocupam
slot). O valor interno já embute o efeito das duas. Confundir isso leva a
concluir que o motor "não usa" uma habilidade que na verdade o card já tem.

---

# D. A DECISÃO — MOLDE v6

## D1. O problema que originou tudo

A habilidade **Curva descendente (Blitz Curler, skill_id 914, Curva +5%)** só
rende no jogo com Finalização e Curva **≥ 89/90 na tela**. Medição nos cards
que a têm:

| Função | Cards | Ativam os dois | Só falta Finalização | Só falta Curva | Faltam os dois |
|---|---|---|---|---|---|
| Falso Nove (3) | 48 | 14 | 1 | 31 | 2 |
| Meia Ofensivo (8) | 51 | 2 | 2 | 15 | 32 |
| Atacante Infiltrador (9) | 51 | 0 | 2 | 2 | 47 |

**Causa medida:** no Meia Ofensivo, James, Neymar e Ronaldinho estavam com
Finalização interna 94–95 contra alvo 86 — exatamente **8 a 9 pontos acima**,
colados no teto do C1. O motor parava porque o próximo ponto valia zero.

## D2. O que ENTRA no v6

### Meia Ofensivo (funcao_id 8)

| Atributo | codigo_atributo | Alvo v5 → v6 | Peso v5 → v6 |
|---|---|---|---|
| Finalização | `PB:530:6` | **86 → 89** | **3 → 7** |
| Aceleração | `PB:486:6` | 89 (não muda) | **7 → 3** |

O peso muda sozinho pela regra do C2: com alvo 89 a Finalização assume a 9ª
posição da fila (desempate com a Aceleração por índice, 6 < 11) e a Aceleração
cai para a 10ª.

**Efeito medido** (6.117 linhas publicadas, barras congeladas):
a nota média **SOBE +6,4**, porque a Finalização interna média é 91,9 e 4.236
das 6.117 linhas já estão acima de 89. Subir o peso premia a maioria.

### Meia Armador (funcao_id 10)

| Atributo | codigo_atributo | Alvo v5 → v6 | Peso v5 → v6 |
|---|---|---|---|
| Velocidade | `PB:434:6` | **81 → 85** | **3 → 7** |
| Aceleração | `PB:486:6` | **82 → 85** | 3 (não muda) |
| Curva | `PB:428:6` | 83 (não muda) | **7 → 3** |
| Equilíbrio | `PB:504:6` | 86 (não muda) | **7 — preservado** |

**Motivo:** eram os únicos atributos com alvo ABAIXO do que a posição entrega
(médias 84,8 e 84,5) — davam ponto de graça. Comparando alvo com o p90 da
função, o molde todo fica de −3 a −7; esses estavam a −10 e −9.

**Por que 85 e não 86:** em 86 a Aceleração também sobe para 7 e **empurra o
Equilíbrio para 3**. O Luis definiu que Equilíbrio importa no Meia Armador e
Curva não. Em 85 a Velocidade sobe, a Curva desce e o Equilíbrio fica.

**Efeito medido** (1.756 cards): p99 de 405,3 → **388,3**; topo 434,4 → **426,5**;
média **−12,3**; pior caso −113,9 (meia armador muito lento, comportamento
correto); 689 cards não perdem nada.

## D3. O que FICA DE FORA, e por quê

- **Falso Nove — Curva 84,5 → 92 ou 90: NÃO.** A Curva interna média da função
  é 81,4 e **4.670 das 5.668 linhas estão abaixo** do alvo novo. Subir o peso
  de 3 para 7 mais que dobra a punição de quem já vai mal: a queda salta de
  −10,6 (só alvo) para **−43,8** (alvo + peso), mediana −55,7. Puniria 4.670
  linhas para destravar 34 cards, dos quais 14 já ativam hoje. O Falso Nove,
  como população, não é uma função de curva.
- **Atacante Infiltrador: NÃO.** Decisão de jogo do Luis — ele finaliza de
  dentro da área, onde a Blitz Curler não é efetiva; Finalização e Aceleração
  importam mais que Curva, e o molde já reflete isso. Além disso, subir a Curva
  para 92 ali **rebaixaria a Finalização de 7 para 3**, o oposto do objetivo.
- **Drible do Meia Armador 89 → 94: NÃO.** Custaria −55,0 de média (3× mais)
  para ganhar 1,7 ponto no p99, e o promoveria a peso 12 — passaria a exigir
  drible de todo meia armador, o que o Pirlo não é.
- **Curva do Meia Ofensivo: NÃO.** Alvo 94 peso 12 já funciona: 92 dos 110
  cards com a habilidade passam do alvo (interna média 97,4) e **nenhum chega
  ao teto de 103**. Não há ponto de graça nem travamento.
- **Atributos defensivos no Meia Armador: NÃO.** Desarme, Dedicação defensiva
  e Agressividade têm peso 0 e assim deve continuar — o Luis definiu que o meia
  armador não marca. (Para referência: o Meia De Arranque, mesma posição MLG,
  é cobrado nos três, e é ali que ele perde pontos.)
- **Obrigar Precisão à distância (23) e Efeito de longe (17): NÃO agora.**
  Dos 93 cards com a Blitz Curler, **83 já têm as duas de fábrica**; depois da
  otimização o motor completa o pacote sozinho em 89 dos 93. Sobram 19 linhas
  de 519, em 4 cards (Gareth Bale falta o 17; Chiesa, Rafa Silva e Zico falta
  o 23). Renderia quase nada.
- **Normalização entre famílias: NÃO agora.** Ver C3 — não é a fórmula.

## D4. Ranking geral simulado depois do v6 (melhor função de cada card)

| # | Card | OVR | Função | Antes | Depois | Era |
|---|---|---|---|---|---|---|
| 1 | Neymar Jr | 89 | Atacante Criador | 113,25 | 113,25 | 3º |
| 2 | Lionel Messi | 90 | Atacante Infiltrador | 113,21 | 113,21 | 4º |
| 3 | Cristiano Ronaldo | 87 | Centroavante Fixo | 113,21 | 113,21 | 5º |
| 4 | Lionel Messi | 90 | **Meia Ofensivo** | 113,12 | **113,16** | 7º |
| 5 | Philipp Lahm | 88 | Lateral Avançado | 113,09 | 113,09 | 9º |
| 6 | Neymar Jr | 87 | Atacante Criador | 113,08 | 113,08 | 10º |
| 7 | Eden Hazard | 88 | Atacante Infiltrador | 113,06 | 113,06 | 11º |
| 8 | Andrea Pirlo | 87 | **Volante De Construção** | 113,06 | 113,06 | 2º (era Meia Armador) |
| 9 | Paolo Maldini | 88 | Zagueiro De Saída | 113,05 | 113,05 | 12º |
| 10 | **Andrea Pirlo** | 87 | **Meia Armador** | **113,39** | **112,95** | **1º** |
| 11 | Andrés Iniesta | 87 | Meia Armador | 113,14 | 112,94 | 6º |
| 16 | Pedri | 86 | **Meia De Arranque** | 112,77 | 112,77 | 13º (era Meia Armador) |

Pirlo sai de 1º para 10º. Nenhum Meia Armador no top 5. Pirlo e Pedri trocam de
vocação — o molde corrigido os reclassifica.

> Toda simulação acima usa **as barras atuais congeladas**. O motor vai
> redistribuir no recálculo e recuperar parte. A direção se mantém.

## D5. Registro obrigatório

Estes alvos **não vieram do método do molde** (que parte da elite da função).
Vieram de medição de frouxidão e de necessidade de jogo. **É uma exceção
autorizada pelo Luis** e precisa ficar registrada como tal, junto com as três
exceções que já existem (goleiro e cobrança de falta).

---

# E. PLANO DE IMPLEMENTAÇÃO

## E0. Antes de tudo — conferir o ponto de partida

```sql
select max(versao) from clube_novo.otimizador_molde;                  -- esperado: 5
select count(*) from clube_novo.otimizador_molde where versao=5;      -- esperado: 494 (19 x 26)
select estado, preparo_concluido, preparo_total
from clube_novo.otimizador_lote_producao_v3
where id='12090000-0000-4000-8000-000000001209';                      -- pausado, 20602/20602
```

## E1. Criar o molde v6

```sql
insert into clube_novo.otimizador_molde (versao, funcao_id, codigo_atributo, alvo, peso)
select 6, funcao_id, codigo_atributo, alvo, peso
from clube_novo.otimizador_molde where versao = 5;

-- Meia Ofensivo (8)
update clube_novo.otimizador_molde set alvo = 89, peso = 7
 where versao=6 and funcao_id=8 and codigo_atributo='PB:530:6';   -- Finalização
update clube_novo.otimizador_molde set peso = 3
 where versao=6 and funcao_id=8 and codigo_atributo='PB:486:6';   -- Aceleração

-- Meia Armador (10)
update clube_novo.otimizador_molde set alvo = 85, peso = 7
 where versao=6 and funcao_id=10 and codigo_atributo='PB:434:6';  -- Velocidade
update clube_novo.otimizador_molde set alvo = 85, peso = 3
 where versao=6 and funcao_id=10 and codigo_atributo='PB:486:6';  -- Aceleração
update clube_novo.otimizador_molde set peso = 3
 where versao=6 and funcao_id=10 and codigo_atributo='PB:428:6';  -- Curva
```

**Conferência — tem que dar exatamente 5 linhas diferentes entre v5 e v6:**

```sql
select a.funcao_id, a.codigo_atributo, a.alvo alvo5, b.alvo alvo6, a.peso peso5, b.peso peso6
from clube_novo.otimizador_molde a
join clube_novo.otimizador_molde b using (funcao_id, codigo_atributo)
where a.versao=5 and b.versao=6 and (a.alvo <> b.alvo or a.peso <> b.peso)
order by 1,2;
```

**Conferência da regra do peso** (a fila das duas funções tem que bater com
5/4/4/resto, respeitando a Cobrança de bola parada em 1):

```sql
with m as (
  select m.funcao_id, a.indice_otimizador idx, at.nome_pt, m.alvo, m.peso,
    row_number() over (partition by m.funcao_id order by ceil(m.alvo) desc, a.indice_otimizador) pos
  from clube_novo.otimizador_molde m
  join clube_novo.atributo_ordem_otimizador a on a.codigo_atributo=m.codigo_atributo
  join clube_novo.atributo_jogo at on at.codigo=m.codigo_atributo
  where m.versao=6 and m.funcao_id in (8,10) and ceil(m.alvo) >= 80
)
select funcao_id, pos, nome_pt, alvo, peso,
  case when pos<=5 then 12 when pos<=9 then 7 when pos<=13 then 3 else 1 end peso_esperado
from m order by funcao_id, pos;
```

## E2. Consertar `complemento_contexto_v14()`

⚠️ Ela tem **`where m.versao = 5` escrito fixo no corpo**, enquanto a régua usa
`max(versao)`. Sem isso, o complemento fica com os pesos velhos.

```sql
do $$
declare d text; n int;
begin
  d := pg_get_functiondef('public.complemento_contexto_v14()'::regprocedure);
  n := (length(d) - length(replace(d, 'where m.versao=5', ''))) / length('where m.versao=5');
  if n <> 1 then
    raise exception 'ancora encontrada % vezes, esperado 1 — parar e revisar', n;
  end if;
  execute replace(d, 'where m.versao=5',
                     'where m.versao=(select max(versao) from clube_novo.otimizador_molde)');
end $$;
```

Se a âncora não bater exatamente assim (espaços), ajustar o literal — mas
**nunca** aplicar sem a contagem dar 1.

## E3. Conferir que a régua adotou o v6

```sql
select (public.otimizador_regua_v2() -> 'versao_molde')                as versao_molde,   -- 6
       (public.otimizador_regua_v2() #> '{gate,pode_rodar}')           as pode_rodar,     -- true
       clube_novo.otimizador_producao_contrato_fingerprint_v3(
         public.otimizador_regua_v2())                                  as contrato_novo;
```

Se `pode_rodar` vier false, **PARAR** e ler `gate.motivos`.

## E4. Atualizar a régua vigente (o selo da tela)

`clube_novo.regua_vigente_v1` guarda o fingerprint vigente; é o que faz a
etiqueta "Régua antiga" aparecer no Ranking, na Busca, nas Boxes e na Ficha.

```sql
update clube_novo.regua_vigente_v1
set contrato_fingerprint = clube_novo.otimizador_producao_contrato_fingerprint_v3(
      public.otimizador_regua_v2());

select count(*) filter (where regua_vigente) vigentes,
       count(*) filter (where not regua_vigente) antigas
from clube_novo.build_publicacao_exibivel_v3;   -- esperado: 0 vigentes
```

## E5. Aposentar a fila 1209

Ela está selada com a régua velha; se rodasse, produziria resultado velho.

```sql
insert into clube_novo.otimizador_lote_aposentado_v1 (lote_id, motivo)
values ('12090000-0000-4000-8000-000000001209', 'molde v6: regua nova');

update clube_novo.build_linha_card
set estado_otimizador='interrompido',
    erro_otimizador='retirada: molde v6, fila refeita',
    otimizador_finalizado_em=clock_timestamp(), atualizado_em=clock_timestamp()
where lote_producao_id='12090000-0000-4000-8000-000000001209'
  and estado_otimizador='pendente';
```

(Conferir antes as colunas de `otimizador_lote_aposentado_v1`.)

## E6. Criar e preparar a fila nova

```sql
select public.otimizador_producao_criar_lote_integral_v6(
  '<NOVO-UUID>'::uuid,
  'a1cc830af3366e2d0c9ac12138d892058b3e57ed216e43d68242d105b33cb9d2',
  'otimizador-fila-producao-v3-local-20260909-habilidades-v12');
```

### ⚠️ E6.1 — o aditivo das cartas de ímpeto condicional (obrigatório)

O criador exclui as condicionais (ver B2). Depois de criar o lote e ANTES de
preparar:

```sql
do $$
declare v_lote constant uuid := '<NOVO-UUID>'; v_base bigint; v_ins int;
begin
  select coalesce(max(ordem_candidata),0) into v_base
  from clube_novo.otimizador_lote_producao_candidata_v5 where lote_id=v_lote;

  insert into clube_novo.otimizador_lote_producao_candidata_v5
    (lote_id, card_id, ordem_candidata, overall_snapshot, carta_versao_snapshot)
  select v_lote, c.card_id,
    v_base + row_number() over(order by
      case when coalesce(c.orcamento,0) > 0 then 0 else 1 end,
      c.overall desc nulls last, c.card_id collate "C")::bigint,
    c.overall::integer, coalesce(c.extraido_em::text,'')
  from clube_novo.carta_jogo c
  where coalesce(c.roda_motor,false) and coalesce(c.pode_rodar_vinculos,false)
    and exists (select 1 from clube_novo.carta_impeto_jogo ci
                where ci.card_id=c.card_id and coalesce(ci.condicional,false))
    and exists (select 1 from clube_novo.otimizador_prioridade_orcamento_v1 p
                where p.card_id=c.card_id)
    and not exists (select 1 from clube_novo.otimizador_lote_producao_candidata_v5 k
                    where k.lote_id=v_lote and k.card_id=c.card_id);
  get diagnostics v_ins = row_count;

  update clube_novo.otimizador_lote_producao_v3
  set preparo_total = preparo_total + v_ins, excluidas_impeto_condicional = 0,
      atualizado_em = clock_timestamp()
  where id = v_lote;
end $$;
```

### E6.2 — rodar o preparo em fatias

O preparo completo não cabe numa chamada (timeout de 2 min por statement).
Padrão que funciona: PROCEDURE com `COMMIT` dentro do laço, agendada no
`pg_cron` de minuto a minuto. **`COMMIT` é ilegal dentro de bloco PL/pgSQL que
tenha `EXCEPTION` — a procedure não pode ter handler.**

```sql
create or replace procedure clube_novo.preparo_v6_tick()
language plpgsql as $proc$
declare
  v_lote constant uuid := '<NOVO-UUID>';
  ini timestamptz := clock_timestamp();
  v_estado text; v_antes int; v_depois int;
begin
  loop
    select estado, preparo_concluido into v_estado, v_antes
    from clube_novo.otimizador_lote_producao_v3 where id=v_lote;
    exit when v_estado is distinct from 'preparando';
    exit when clock_timestamp() - ini > interval '75 seconds';
    perform public.otimizador_producao_preparar_fatia_v5(v_lote, 5);
    select preparo_concluido into v_depois
    from clube_novo.otimizador_lote_producao_v3 where id=v_lote;
    commit;
    exit when v_depois = v_antes;
  end loop;
end $proc$;

select cron.schedule('preparo-v6','* * * * *','call clube_novo.preparo_v6_tick()');
-- ao terminar (estado vira 'parado'):
select cron.unschedule('preparo-v6');
```

> Usar a **fatia v5**, não a v6: `otimizador_producao_preparar_fatia_v6` está
> pareada com a fórmula `7aaa3ccc…` e recusa lote criado pela via vigente
> (`a1cc830a…`). Pendência conhecida.

Leva cerca de 1 hora. Acompanhar com:

```sql
select estado, preparo_concluido, preparo_total, cards, linhas, falha
from clube_novo.otimizador_lote_producao_v3 where id='<NOVO-UUID>';
```

### E6.3 — retirar as linhas sem evidência física

Mesmo caso de B2; senão viram pendentes eternas:

```sql
update clube_novo.build_linha_card l
set estado_otimizador='interrompido',
    erro_otimizador='retirada: carta sem evidencia fisica em carta_nivel_evidencia_v1',
    otimizador_finalizado_em=clock_timestamp(), atualizado_em=clock_timestamp()
from (
  select q.linha_id from clube_novo.otimizador_lote_producao_linha_v3 q
  left join clube_novo.otimizador_prioridade_orcamento_v1 p on p.card_id=q.card_id
  where q.lote_id='<NOVO-UUID>' and p.card_id is null
) f
where l.id=f.linha_id and l.estado_otimizador='pendente';
```

### E6.4 — renumerar a ordem_fila pela regra canônica

O aditivo entra depois das linhas já numeradas e jogaria as condicionais para o
fim. Offset temporário por causa do `UNIQUE (lote_id, ordem_fila)`:

```sql
do $$
declare v_lote constant uuid := '<NOVO-UUID>'; v_off constant bigint := 100000000; v_n int;
begin
  update clube_novo.otimizador_lote_producao_linha_v3
  set ordem_fila = ordem_fila + v_off where lote_id = v_lote;

  with nova as (
    select q.linha_id,
      row_number() over(order by
        case when coalesce(c.orcamento,0) > 0 then 0 else 1 end,
        c.overall desc nulls last, q.card_id collate "C",
        l.funcao_id, l.posicao_id, l.impeto_condicional_nivel nulls first, q.linha_id)::bigint ordem
    from clube_novo.otimizador_lote_producao_linha_v3 q
    join clube_novo.build_linha_card l on l.id=q.linha_id
    join clube_novo.carta_jogo c on c.card_id=q.card_id
    where q.lote_id=v_lote
  )
  update clube_novo.otimizador_lote_producao_linha_v3 q
  set ordem_fila=n.ordem from nova n
  where q.lote_id=v_lote and q.linha_id=n.linha_id;

  select count(*) into v_n from clube_novo.otimizador_lote_producao_linha_v3
  where lote_id=v_lote and ordem_fila > v_off;
  if v_n > 0 then raise exception 'renumeracao incompleta: % linhas', v_n; end if;
end $$;
```

### E6.5 — refazer o fingerprint e deixar o lote em `pausado`

```sql
do $$
declare v_lote constant uuid := '<NOVO-UUID>';
        v clube_novo.otimizador_lote_producao_v3%rowtype; v_fp text;
begin
  select * into v from clube_novo.otimizador_lote_producao_v3 where id=v_lote;
  select encode(extensions.digest(convert_to(
    v_lote::text||':'||v.formula_fingerprint||':'||v.contrato_fingerprint||':'||v.motor_versao||':'||
    string_agg(q.card_id||':'||l.funcao_id::text||':'||l.posicao_id::text||':'||q.ordem_fila::text,
               ',' order by q.ordem_fila), 'UTF8'),'sha256'),'hex')
  into v_fp
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id=q.linha_id
  where q.lote_id=v_lote;

  update clube_novo.otimizador_lote_producao_v3
  set fingerprint=v_fp, atualizado_em=clock_timestamp() where id=v_lote;

  perform public.otimizador_producao_controlar_lote_v3(v_lote,'iniciar');
  perform public.otimizador_producao_controlar_lote_v3(v_lote,'pausar');
end $$;
```

### E6.6 — conferência final da fila

```sql
-- a fotografia passa? (tem que responder em segundos)
with m as (select public.otimizador_producao_pacote_local_manifesto_v2('<NOVO-UUID>') j)
select j->>'cartas_total', j->>'linhas_total', j->>'linhas_condicionais',
       j->>'impetos_condicionais', j->>'contrato_fingerprint' from m;

-- sobrou pendente fora da fila?
select coalesce(lote_producao_id::text,'sem lote'), count(*)
from clube_novo.build_linha_card
where estado_otimizador='pendente' and estado <> 'invalida' group by 1;
-- esperado: só o lote novo

-- primeiras linhas da fila
select p.ordem_fila, c.nome, c.overall, c.orcamento, p.prioridade_grupo
from clube_novo.otimizador_fila_prioridade_v1 p
join clube_novo.carta_jogo c on c.card_id=p.card_id
where p.lote_id='<NOVO-UUID>' order by p.ordem_fila limit 5;
-- esperado: grupo 1, overall alto (Lionel Messi 94, orcamento 16)
```

## E7. Máquina 1 — documentação (obrigatório)

- `4-DOCUMENTOS/MANUAL-DO-OTIMIZADOR.md` — seção nova do molde v6: o que mudou,
  as medições, e as regras do C1 e C2 (teto de 9 e peso vindo da fila).
- `Site Novo/CADERNO-DE-PENDENCIAS.md` — abrir a pendência da mediana por
  família (C3) e a do `criar_lote_integral_v6` que exclui condicionais.
- Registrar a exceção de método do D5 junto com as três já existentes.
- Documento de decisão no Projeto do Claude.

## E8. Máquina 2 — o que o Luis faz (só no fim)

1. Rodar o `.bat` de baixar a fila com o **UUID novo** dentro:
   `"bin\OperacaoLocalJson.exe" renovar --lotes <NOVO-UUID>`
   (pasta `2-MOTORES\OTIMIZADOR\OPERACAO-LOCAL-JSON`)
2. `PROCESSAR-FILA-PRINCIPAL.bat`
3. `ENVIAR-FILA-PRINCIPAL.bat` (pode enviar em tandas, sem esperar terminar)

**Conferir na primeira tela do processar:** o total de cartas e linhas tem que
bater com o manifesto do E6.6. Se aparecer número velho, o pacote não trocou.

> O motor local **não tem cópia do molde**. `fonte_unica.py` lê tudo da régua do
> banco e sela no pacote. **Nenhum arquivo .py precisa ser alterado.**

---

# F. PENDÊNCIAS QUE FICAM ABERTAS

| # | O quê | Gravidade |
|---|---|---|
| 1 | `criar_lote_integral_v6` exclui cartas de ímpeto condicional — exige aditivo manual em toda fila nova | alta |
| 2 | Aposentar lote não retira as linhas pendentes dele — vira lixo invisível | alta |
| 3 | `preparar_fatia_v6` pareada com a fórmula `7aaa3ccc…`, incompatível com a criação (`a1cc830a…`) | média |
| 4 | Extrator lê o estilo Sobreposição no bit 135, fora da faixa 199–238 dos outros cinco — vai reintroduzir o erro na próxima extração | alta |
| 5 | 1.414 técnicos ainda com 5 estilos e ímpeto não conferido (não têm boost, não afetam nota hoje) | baixa |
| 6 | `tests/ranking.test.cjs` e `tests/search.test.cjs` quebrados por fixture velha (de 06/09) — não é regressão do selo | baixa |
| 7 | Mediana por família muito desigual (MEIO −25, DEFESA −58, GOLEIRO −80): defesa tem 13 no top 100 e goleiro zero | média |
| 8 | 1.571 cartas sem evidência física em `carta_nivel_evidencia_v1`, 10 delas cartas comuns | média |
