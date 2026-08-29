# Investigação das frações internas da proficiência

**Data:** 27/08/2026  
**Estado:** não comprovado — aguardando evidência direta do cálculo interno  
**Escopo:** somente leitura; sem alteração do jogo, sem rede, sem automação de gameplay e sem nova mudança no Otimizador.

> **Atualização de 28/08/2026:** este documento registra uma investigação histórica
> sobre frações; não autoriza ordem de cálculo. A hipótese que colocava ímpetos antes
> da proficiência sem teto foi reprovada pelo experimento discriminante do Messi e está
> revogada. A regra vigente está no `MANUAL-DO-OTIMIZADOR.md`.

## Pergunta

Depois de aplicar a proficiência do técnico, o jogo:

1. converte imediatamente o resultado para inteiro; ou
2. preserva uma parte fracionária internamente e só converte em uma etapa posterior?

A interface não responde a essa pergunta. Quando duas cadeias acabam no mesmo inteiro visível, esse inteiro não revela se existiu uma fração antes da apresentação.

## Hipóteses que precisam ser distinguidas

Usando o multiplicador medido atualmente para proficiência 89 (`m = 1,036`):

- **H1 — truncamento precoce:** `interno = x + trunc(x × 0,036)`;
- **H2 — fração preservada:** `interno = x × 1,036`, mantendo a fração até uma conversão posterior.

Essas fórmulas eram hipóteses da investigação de 27/08. H1 foi usada na tentativa
posteriormente revogada; não descreve a regra vigente do Otimizador nem prova o código
interno do jogo.

### Valores-âncora para inspeção interna

| Estado antes da proficiência | H1: logo após proficiência | H2: logo após proficiência | após boost +1 em H1 | após boost +1 em H2 |
|---:|---:|---:|---:|---:|
| 96 | 99 | 99,456 | 100 | 100,456 |
| 98 | 101 | 101,528 | 102 | 102,528 |
| 99 | 102 | 102,564 | 103 | 103,564 |

Os casos reais já documentados fornecem dois bons estados para localizar a cadeia na memória:

- Marcel Desailly: `96 -> proficiência 89 -> boost +1`;
- Alessandro Nesta: `98 após ímpetos -> proficiência 89 -> boost +1`.

O número visível 100 ou 102 não decide entre H1 e H2 se a apresentação corta a fração no fim. A prova precisa observar a rotina ou o valor antes dessa conversão.

## Inventário factual dos artefatos locais

### Executável instalado

- arquivo: `C:\Program Files (x86)\Steam\steamapps\common\eFootball\eFootball\Binaries\Win64\eFootball.exe`;
- versão: `6.0.0.0`;
- tamanho: `352.409.088` bytes;
- modificação: `12/08/2026 21:59:44`;
- SHA-256: `A6911E9613750DF33D10598D6493DB629B03195C3EC1D011704CD1E853D8C6E4`;
- não há `.pdb`, `.map`, `.sym` ou `.dbg` ao lado do executável.

O executável contém nomes que confirmam a existência de estruturas pertinentes, entre eles `GetPlayerAbilityParamStr`, `TeamPlayStyle`, `CoachData@OnlineMatch`, `coachParam`, `adaptabilityRate` e `playerParameter`. Também contém nomes genéricos de funções matemáticas como `floor`, `round` e `trunc`. A presença desses nomes **não prova** que uma delas seja usada na proficiência.

A estrutura PE possui grandes seções não convencionais, incluindo `.xcode`, `.tls$` e `.impdata`. Sem símbolos e sem desmontagem confiável da rotina, uma constante isolada ou um nome de importação não permite atribuir uma operação à proficiência.

### Arquivos físicos de dados

`GameDefine.bin` foi localizado tanto em `dt200_console_all.cpk` quanto em `dt870_console_win.cpk`:

- conteúdo compactado idêntico: 1.865 bytes, SHA-256 `1ab5a0a4aee9061d46d3789f19cfa693cf9acded3f5c9224e376a9840d5bc4ed`;
- conteúdo descompactado idêntico: 4.136 bytes, SHA-256 `7771556f9f306c3e82e316b8fe432914befdb4e3a1162c10118a3766ac984307`;
- não contém, como `float32` ou `float64`, os valores medidos `1,036`, `1,0365`, `1,0355`, `1,034091`, `1,03275`, `0,036` ou `0,0365`.

Os CPKs e `Coach.bin` comprovam os dados de entrada — identidade do técnico, proficiências e boosts —, mas não expõem por si mesmos a operação executada sobre os atributos.

## Nível 1 — prova estática no executável

Este é o caminho preferencial porque não toca no processo em execução.

1. Trabalhar sobre uma cópia somente leitura do executável com o SHA-256 acima.
2. Usar um desmontador local autorizado que reconheça o código protegido/empacotado sem modificar o arquivo.
3. Localizar a cadeia de dados que parte de:
   - `CoachData@OnlineMatch` e seus campos de proficiência;
   - `TeamData@OnlineMatch.adaptabilityRate`;
   - a construção do vetor `playerParameter` usado antes da apresentação.
4. Identificar a instrução que aplica o fator da proficiência e a primeira conversão do resultado:
   - conversão imediata de ponto flutuante/fixo para inteiro, ou divisão inteira com descarte, favorece H1;
   - armazenamento/propagação como `float`, `double` ou ponto fixo com parte fracionária favorece H2 até aquele ponto.
5. Registrar, para auditoria:
   - RVA/endereço da função;
   - bytes das instruções relevantes;
   - pseudocódigo mínimo;
   - origem do multiplicador ou escala inteira;
   - ponto exato da conversão;
   - hash do executável analisado.

### Critério de aceitação estática

Só aceitar uma conclusão se houver fluxo completo entre a proficiência do técnico, o atributo de entrada e o parâmetro calculado. Encontrar `trunc`, `floor`, `round`, `0,036` ou um número semelhante fora desse fluxo não é evidência suficiente.

## Nível 2 — observação passiva da memória

Usar apenas se o Nível 1 não conseguir revelar a rotina e se o Windows e a proteção do jogo permitirem uma captura passiva sem contorno.

1. O usuário abre o jogo normalmente e monta manualmente um estado conhecido; não há automação de gameplay.
2. Usar somente um mecanismo de leitura/snapshot permitido pelo sistema, sem:
   - `WriteProcessMemory`;
   - injeção de DLL;
   - patch, hook ou modificação de código;
   - desativação ou contorno de proteção/anticheat;
   - rede.
3. Capturar dois snapshots locais do mesmo cartão e mesma montagem, mudando apenas o técnico/proficiência, quando isso puder ser feito de forma permitida.
4. Localizar o objeto pelo encadeamento comprovado de estruturas (`CoachData`, cartão/ID e `playerParameter`), e não por busca cega de um número.
5. Observar o campo imediatamente após a aplicação da proficiência e antes da conversão de apresentação.

### Conjunto mínimo de estados internos

| Caso | Entrada conhecida | valor esperado se H1 | valor esperado se H2 |
|---|---:|---:|---:|
| Desailly / proficiência 89 | 96 | inteiro 99 | 99,456 ou representação fixa equivalente |
| Nesta / proficiência 89 | 98 | inteiro 101 | 101,528 ou representação fixa equivalente |

O boost deve ser conferido separadamente, depois do ponto observado: H1 produz 100/102; H2 preservada produz 100,456/102,528 antes da conversão final.

### Critério de aceitação em memória

- Encontrar uma fração ligada pelo fluxo de dados ao atributo correto prova que a fração sobrevive **até aquele ponto**.
- Encontrar apenas o inteiro final prova somente que naquele ponto o valor já é inteiro; não revela onde ocorreu a conversão.
- Um número solto (`101,528`, `101` etc.) sem vínculo com cartão, técnico, atributo e rotina é falso positivo possível e não deve ser aceito.
- Se a proteção do jogo impedir a captura ou exigir qualquer contorno, a investigação deve parar.

## Resultado desta auditoria

Com os artefatos e ferramentas locais disponíveis nesta data, **não foi possível provar H1 nem H2 diretamente**. Foi possível provar apenas:

- as entradas físicas do técnico existem nos arquivos do jogo;
- o executável contém estruturas relacionadas a técnico e parâmetros do jogador;
- `GameDefine.bin` não contém a fórmula nem os multiplicadores medidos como constantes de ponto flutuante;
- a interface inteira não decide a existência de fração escondida.

Portanto, nenhuma mudança adicional na fórmula do Otimizador é justificada por esta investigação. O próximo passo válido é uma desmontagem estática autorizada do executável exato; memória passiva é contingência e deve ser abandonada se a proteção do jogo não a permitir com segurança.
