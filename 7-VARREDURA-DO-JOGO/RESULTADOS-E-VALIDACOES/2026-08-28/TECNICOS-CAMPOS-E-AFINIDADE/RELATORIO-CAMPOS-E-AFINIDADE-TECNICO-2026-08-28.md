# Relatório — idade, nacionalidade e afinidade de técnico

**Data:** 28/08/2026  
**Escopo:** bibliotecas DT200/DT870 e textos oficiais do jogo; nenhuma alteração no Otimizador.  
**Estado do banco nesta investigação:** somente leitura; nenhuma escrita executada.

## Resultado objetivo

Os três campos pedidos foram extraídos do `Coach.bin` atual para as **1.478 versões de técnico** presentes no DT870 atualizado, sem duplicidade de ID físico `u64`:

| campo | fonte física | endereço | regra comprovada nesta fonte |
|---|---|---:|---|
| idade | `Coach.bin` do DT870 atualizado | bit 231, largura 7 | `idade = valor físico + 14` |
| nacionalidade | `Coach.bin` do DT870 atualizado | bit 170, largura 8 | código oficial que resolve em `Country.bin` |
| afinidade | `Coach.bin` do DT870 atualizado | bit 187, largura 3 | enum físico `0..7`; `0` é ausência legítima |

### Validações

- idade: faixa extraída `28..80`; o cruzamento por ID completo com a fotografia anterior coincidiu exatamente em 1.241 de 1.319 registros. Em 75 registros a fotografia externa estava um ano à frente, coerente com idade corrente versus idade fixada na versão; os valores físicos não foram substituídos pela referência.
- nacionalidade: `Country.bin` tem 214 registros de 1.488 bytes e é byte-idêntico nas três fontes auditadas. Seu código está no bit 10, largura 9; o nome português do Brasil fica no campo fixo de offset 788. As 1.478 versões de técnico resolveram sem órfãos, usando 100 nacionalidades distintas.
- afinidade: 1.456 versões têm código `0`; 22 têm código não zero. As 20 versões não zero presentes na fotografia de conferência coincidiram com o valor físico. As duas versões mais novas também têm código físico, embora ainda não existam nessa fotografia.
- amostra dirigida: Fabio Capello (`17601312850052`) tem idade física 44, nacionalidade `215 / Itália / ITA` e afinidade código `5`. A captura fornecida pelo usuário identifica esse código, nessa versão, como **Jogadores de AT / Atacantes**.

Os outros rótulos não foram ligados artificialmente aos códigos: o arquivo conserva o código bruto e só marca como confirmado o vínculo `5 -> Jogadores de AT` já observado. Isso evita transformar a ordem visual dos textos em uma relação inexistente.

## Semântica comprovada da afinidade

O `all.str` português do `dt261_bra_console_win.cpk` responde diretamente à pergunta central:

- `Any8T / 605`: a afinidade aumenta a quantidade de experiência recebida em partidas; o tipo de afinidade define quais jogadores recebem o benefício.
- `Any1W / 492..497`: as categorias exibidas são jogadores veteranos, jogadores jovens, astros, jogadores de AT, jogadores do MC e jogadores da DEF.
- `Any1W / 498..503`: as descrições das seis categorias especificam **pontos de experiência de partida**, respectivamente para idade `>=30`, idade `<=23`, valor de jogador `5 estrelas`, posições de ataque, posições de meio-campo e ZG/GO.
- `Any7T / 485`: itens que aumentam experiência são aplicados junto com a afinidade do técnico.

Portanto, a evidência positiva da biblioteca é: **afinidade condiciona bônus de experiência por categoria de jogador**.

## Relação com atributos, ímpetos, boosts e proficiência

Não foi encontrada relação física ou textual que faça uma afinidade conceder aumento direto a atributos determinados ou escolher ímpetos:

- nenhuma das seis descrições oficiais fala em atributo, overall, ímpeto ou proficiência; todas falam em pontos de experiência de partida;
- a afinidade ocupa seu próprio enum de 3 bits no `Coach.bin`;
- os boosts ocupam dois campos físicos independentes, nos bits 160 e 148;
- cada um dos sete códigos não zero observados aparece com pares de boosts diferentes. Por exemplo, o código 5 aparece com três pares distintos entre Capello, Beckenbauer e Cruyff. Logo, o código de afinidade não determina a receita de boost;
- nenhuma entrada específica de afinidade/ímpeto existe no inventário físico do DT200/DT870 auditado.

Conclusão factual: **não há evidência de que afinidade aumente ou condicione atributos/ímpetos**. O efeito comprovado é experiência de partida, separado de boost, posição, proficiência e Link-up.

## Artefatos

- `tecnico-apresentacao-fisico.csv`: 1.478 versões com valores e proveniência por registro.
- `manifesto-tecnico-apresentacao.json`: contagens, hashes e regras físicas.
- `evidencia-textos-afinidade.json`: 11.679 textos lidos e recorte das entradas relevantes com offsets.
- `mapeamento-campos-apresentacao-tecnico.json`: cruzamento de bits contra fotografia anterior.
- `auditoria-campos-apresentacao-tecnico-db.json`: pré-voo do banco em transação somente leitura.

Pasta permanente: `7-VARREDURA-DO-JOGO/RESULTADOS-E-VALIDACOES/2026-08-28/TECNICOS-CAMPOS-E-AFINIDADE`.

## Limite preservado

Esta etapa não promoveu colunas nem dados no banco e não alterou o Otimizador. O CSV é uma extração física revisável. A ligação dos demais códigos de afinidade aos rótulos será promovida somente quando uma relação física/documentada código-rótulo for encontrada; os textos isolados não foram usados para presumir essa ordem.
