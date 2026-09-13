> Atualização 10/09/2026: normalização vigente por amplitude: 100 + 50 × motor / (máximo teórico − mínimo teórico) + bônus. Consulte 4-DOCUMENTOS/NORMALIZACAO-0909/AMPLITUDE-VIGENTE.md; curvas anteriores são históricas.

# Normalização oficial e estrelas de contratação — 09/09/2026

Versão: `normalizacao-bonus-integral-20260909-v1`.
Parâmetros: `80bc2ab246b9a56dd10dd3a613056ff4d74d7b9171d4e100cc1f4caf21b36efe`.

## Decisão e alcance

Luis aprovou a proposta **bonus-integral-0909** como oficial. Esta decisão posterior substitui as restrições históricas de “normalização inalterada” das frentes de habilidades e estilos. O Otimizador, Bonificador, moldes, alvos, pesos, habilidades, distribuição de barras, atributos e filas não mudam nesta entrega. Não há motivo para refazer os cálculos dos motores nem instalar um executável novo na Máquina 2 por causa desta normalização.

## Conta

1. Ler a pontuação bruta já gravada pelo Otimizador.
2. Dividir pelo teto teórico fixo da função, derivado de suas regras. O teto corresponde a 4,68 vezes a soma dos pesos, arredondado a uma casa decimal; não vem do melhor card.
3. Aplicar a tabela fixa da função em `parametros.json`, com interpolação linear entre os pontos. O molde é 100 e o teto é 110 antes dos bônus. Resultado bruto negativo segue `100 + 10 × bruto/teto`; acima do teto ou teto diferente do aprovado gera erro, sem inventar uma nota.
4. Somar o bônus integral, sem divisão, reescala ou teto adicional.

Exemplo aprovado: Ronaldinho, Meio ofensivo: bruto 444,10 / teto 472,70; motor normalizado 106,906428; bônus 1,6196; final 108,526028 (108,53 na tela). A interpolação da tabela é parte da regra; somente dividir pelo teto e multiplicar por dez não reproduz esta proposta.

Há 19 curvas e 820 pontos. São fixos e não mudam quando chegam cartas. **A calibração inicial usou a amostra e os exemplos de jogadores apresentados por Luis.** Portanto, não é uma validação independente nem uma lei física do jogo. A busca por uma curva única continuará como comparação separada, sem substituir esta decisão automaticamente.

## Banco e continuidade

Somente `clube_novo` é autoridade operacional. `normalizacao_regra_v3` guarda versão, parâmetros, hash e origem. `normalizar_motor_v3` converte a nota. `normalizar_publicacao_v3` atualiza ponte e delta do par de motores efetivamente publicado, registra os campos anteriores em `normalizacao_publicacao_historico_v3` e valida a soma.

A linha canônica só recebe a nota se ainda corresponde ao mesmo par e aos mesmos selos. É proibido misturar um bônus novo com um Otimizador diferente da publicação ativa. O histórico preserva os campos de pontuação anteriores; os resultados integrais dos motores continuam nas próprias tabelas. Não apagar resultados, recibos, filas ou antecessores.

O finalizador conserva seus critérios existentes, chama a normalização na mesma transação e desfaz toda a finalização se a conversão falhar. Atualizar apenas a nota não pode disparar substituição de orçamento ou reabrir fila. `normalizar_publicacoes_pendentes_v3` é a migração idempotente das publicações anteriores, com trava por linha e `SKIP LOCKED`.

A tela recebe a nota pronta. O editor pessoal avalia as escolhas do usuário no servidor e aplica a mesma conversão, sem otimizar nem limitar as habilidades por critérios estratégicos. Pessoais antigas são reavaliadas para apresentação, preservando o registro até um salvamento explícito. A implementação reutiliza a política de estilos V12; não cria outra política de bônus.

## Goleiros

A vitrine segue a separação aprovada no comparativo: Goleiro defensivo (estilo 337) na função 4, Goleiro ofensivo (336) na função 5. `build_publicacao_exibivel_v3` filtra somente a leitura. Os resultados e a ponte produtiva permanecem guardados; o editor pessoal continua livre. Estilos novos não são classificados por suposição. Os snapshots históricos de Boxes não são reescritos.

## Estrelas de contratação

A coluna `clube_novo.regua_contratacao_faixa_v1.estrelas` é a quantidade preenchida dentre cinco ícones. As seis etiquetas, códigos, limites e snapshots anteriores permanecem no banco.

| Estrelas | Etiqueta preservada | Mínimo existente (%) |
|---:|---|---:|
| 5 | PAGAR QUALQUER PREÇO | 99,995 |
| 4 | PAGAR CARO | 99 |
| 3 | PAGAR | 98 |
| 2 | PAGAR POUCO | 97 |
| 1 | PAGAR MUITO POUCO | 96 |
| 0 | NÃO PAGAR | 0 |

Aplicar a primeira faixa satisfeita, como antes. Exatamente 96% mantém uma estrela: a decisão final de preservar as faixas substitui a sugestão inicial de zerar em 96%. Estas porcentagens continuam apenas na regra do banco, não nas cartas da tela.

Nos cards das Boxes aparecem cinco ícones, preenchidos conforme o campo do banco, sob a indicação “Contratação”. A legenda no cabeçalho mostra os mesmos ícones acompanhados dos textos acima. São distintas das estrelas nativas desenhadas na arte da carta. O frontend nunca reconstrói a classificação a partir da nota, percentual ou código.

Boxes em andamento continuam dinâmicas; Boxes finalizadas continuam com a análise histórica gravada. Equivaler um código histórico a estrelas não autoriza recalcular sua classificação.

## Arquivos e implantação

SQLs 01 a 05 neste diretório registram a instalação da normalização, ativação, equivalência de estrelas, editor e leitores de goleiros. Os parâmetros e o consumidor de conferência acompanham a regra. Não reaplicar migrações de criação em um banco já atualizado; conferir o registro de migrações e o readback.

A publicação é o conteúdo público de `Site Novo` no projeto Netlify existente. SQLs, manuais, tokens e arquivos dos motores não integram o pacote web. Conferir `READBACK-IMPLANTACAO.json` e `IMPLANTACAO.md` para estado real e testes. Uma embalagem pronta não comprova deploy.


## Revisão das fotografias de Boxes — 09/09/2026

Autorização posterior: atualizar as avaliações congeladas para a normalização vigente, não apenas o desenho das estrelas. `clube_novo.box_avaliacao_revisao_0909` guarda nova fotografia por box/card/degrau, consumida por `site_novo_box_card_analise_snapshot_v1`; o leitor original e os 2.621 snapshots antigos permanecem preservados. Esta revisão substitui a orientação anterior de manter exclusivamente a avaliação antiga na tela.

Foram capturadas 20.094 fotografias (6.698 vínculos de cards, 1.022 boxes, três degraus), contendo 44.827 análises. Cards sem publicação elegível ficam sem avaliação; nenhuma nota foi inventada. As faixas de contratação e os motores permanecem iguais. Não há atualização contínua dessa fotografia: nova revisão exige decisão própria. Fontes: publicações exibíveis vigentes, melhor linha por função/degrau e topo global da função, como na régua de contratação existente.

Readback: zero divergências de identidade, nota, degrau ou estrelas inválidas. Cristiano Ronaldo `89138556572074`, Living Legends 2026, degrau 3: Centroavante fixo, linha 364310, nota 111,3542550014243, cinco estrelas. SQL de implantação: `4-DOCUMENTOS/NORMALIZACAO-0909/06-RENOVAR-AVALIACOES-BOXES.sql`. A correção é no banco e já é consumida pelo site publicado; não exige novo deploy nem pacote para a Máquina 2.
