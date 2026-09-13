# Avaliador privado de uma build — contrato vigente

Implementado em 06/09/2026. Motor `editor-independente-v1`.

## Escopo e caminho único

O navegador envia as escolhas para `public.site_novo_editor_avaliar_v1`.
A porta de cálculo, agora disponível também sem login, chama somente `build_editor.avaliar_v1`. Essa função resolve
os dados de `clube_novo`, valida a entrada e avalia **uma** build. Não otimiza,
não procura combinações e não chama Railway, Otimizador ou Bonificador aposentados.

O servidor aplica, nesta ordem:

1. Base + distribuição, limitada a 99.
2. Maior proficiência confirmada do técnico, tabela medida; incremento truncado,
   piso 40/teto 99 quando o multiplicador atua.
3. Boosts do técnico e ímpetos físicos. Passam de 99.
4. Valoração das habilidades, separada dos atributos exibidos: referência do
   passo 1; vencedora comum inteira, demais comuns pela metade, raras inteiras;
   teto matemático sobre o ganho total, sem arredondar as metades antes.
5. Normalização: soma ponderada do vetor do sistema / soma ponderada dos alvos
   do molde aprovado versão 5 × 100.
6. Bônus de pé, físico V10, dois estilos e IA, conforme catálogos vigentes.

Não há chamadas às antigas funções de cálculo/normalização. A interpretação foi
conferida com os manuais e com contraexemplos manuais, não apenas comparada ao
resultado de um motor antigo. As migrações são histórico de instalação; o banco
mantém uma definição ativa por assinatura. Não usar trechos de migrações antigas
como especificação de regra. Qualquer mudança futura exige atualizar este contrato,
os casos esperados e a função ativa, sem uma segunda rota de cálculo.

## Privacidade e autorização

- Código do servidor está nesta pasta, **fora de `Site Novo`**.
- `build_editor` não é um schema exposto pela Data API.
- Fórmulas auxiliares e tabelas não concedem execução/leitura direta ao usuário.
- As portas públicas são invoker. Avaliar, consultar catálogo e conferir gêmeas
  aceitam `anon`, por decisão expressa posterior do usuário. Salvar, listar e
  excluir na nuvem continuam exclusivos de contas autenticadas, com verificação
  de `auth.uid()` e existência de conta não anônima. Nenhuma decisão usa `user_metadata`.
- Catálogo público do editor contém nomes, escolhas e efeitos visíveis no jogo,
  não pesos, moldes, fórmulas de bônus ou valoração das habilidades.
- Não publicar esta pasta nem as migrações. O frontend usa somente HTML, CSS e JS
  de interface/transporte; não contém o motor nem credenciais de serviço.

## Entrada e validações

`card_id`, `funcao_id`, `posicao_id`, `tecnico_id` opcional, objeto com as dez
`barras`, até cinco `habilidades`, `impetos` por vaga e níveis `condicoes`.
Nota, proprietário e resultado não são aceitos na entrada.

Valida orçamento, custo progressivo, limites das barras, aptidão física da posição,
função compatível, habilidades sem duplicatas/nativas, slots livres e efeitos
confirmados. Ímpeto nativo não pode ser trocado. Condicional aceita apenas nível
entre zero e o máximo físico. Sem nível explícito, avalia a condição no máximo;
o modal mostra o nível escolhido. Dados sem confirmação interrompem a avaliação.

O treino pessoal não usa `vetada`, bloqueios por função, dominância ou incidência
estratégica do Otimizador. Oferece habilidades comuns, exceto as já nativas ou
adicionadas. Reposição baixa/alta do GO, Arremesso longo do GO e Pegador de pênaltis
(44,45,47,49) não entram em jogador de linha. As antigas flags de utilidade tinham
inclusive Arremesso lateral longo marcado simultaneamente nos dois grupos;
não foram usadas como proibição de treino. A lista adicional de ímpetos exige
não condicional, de um a quatro efeitos físicos +1; Pacote total não é liberado.

Conferência de 08/09/2026: Volta para marcar (56) continua disponível ao usuário
mesmo nas especialidades em que o Otimizador foi proibido de adicioná-la.
O editor também aceita zero habilidades adicionais. O catálogo e o avaliador
foram restaurados exatamente após uma aplicação indevida do veto estratégico.
Readback real de Shevchenko como Centroavante móvel, com barras zero:
com 56, nota 97,71466187964516902400; sem adicionais, 97,57081148405658115600.
Ambos retornaram 26 atributos. Nenhuma build pessoal foi salva nesse teste.

## Gêmeas

`site_novo_editor_gemea_v1` recebe a entrada e os IDs de uma saída e uma entrada.
Exige origem presente, destino ausente, relação de gêmeas e efeitos iguais.
Avalia antes/depois pelo mesmo motor e recusa diferença na nota ou nos atributos.
Não é possível aplicar o atalho de gêmea a outra habilidade nem trocar duas de uma vez.
Trocas manuais gerais são permitidas, mas podem alterar a nota.

## Persistência

`site_novo_editor_salvar_v1` recalcula no servidor na transação de salvamento.
Sem UUID de build pessoal, cria uma nova linha. Com UUID, verifica dono, mesma
carta e revisão esperada sob trava. Revisão obsoleta retorna conflito, sem sobrescrever.
Cada envio possui UUID de recibo durável: repetir uma chamada perdida retorna a
mesma confirmação, sem duplicar. A cópia recebe novo UUID. Nunca escreve nas
tabelas de builds do sistema, filas ou resultados dos motores operacionais.

`site_novo_editor_listar_v1` devolve somente builds não excluídas do usuário para a carta.
Entrada, resultado validado, nome, versão do motor, revisão e datas ficam salvos.

Cada build recebe função-base e número permanente por usuário/card/função. A
numeração usa UPSERT transacional em contador separado; exclusão lógica não
libera números. Atualização mantém identidade; mudar função exige salvar cópia.
`site_novo_editor_excluir_v1` exige propriedade e revisão. A projeção `build`
é montada no servidor para a mesma vitrine, sem recalcular nota na leitura.

Sem login, `ficha-editor-api.js` salva a avaliação em `localStorage`, com recibo,
revisão e contador próprios; Web Locks serializa gravações nas abas que suportam
essa API. Login é opcional e recolhido. Limpar dados do navegador remove as cópias
locais. O cálculo continua exigindo internet; nenhuma fórmula foi enviada ao JS.

## Provas executadas

- Messi: Finalização 80 + barra 19 → 99; técnico 89/+1 e ímpeto +4 → **104**.
- Truncamento negativo: 74 com multiplicador 0,987 continua **74**; piso **40**.
- Físico Messi 89136409091415, função 14: soma **13**, máximo **20**, bônus **0,9750**.
- Shevchenko 88045755964138, função 2/CA: **9038/8342 × 100 + 2,4857 = 110,8290229441381**;
  os 26 atributos e o gasto 64/64 foram conferidos.
- Testes transacionais cobrem entradas inválidas, gêmeas incompatíveis, salvar,
  listar, atualizar, repetição idempotente, revisão obsoleta, outro usuário e anônimo.
- Teste pela role `authenticated` confirmou acesso às portas e catálogo. Após
  autorização do modo sem login, HTTP anônimo de avaliação/catálogo passou; salvar
  na nuvem continua **401/42501**. Persistência local foi testada com recarga.
- Readback de permissões: usuário não executa a fórmula
  auxiliar, não lê o molde e não insere diretamente na tabela pessoal.
- Os usuários e builds temporários dos testes foram desfeitos por ROLLBACK;
  readback confirmou zero registros restantes. Nenhum e-mail de teste foi enviado.
- Advisor de segurança: nenhum alerta nos objetos novos após as políticas.
  Alertas anteriores de outros schemas permanecem fora desta mudança.

### Atributos no jogo e no sistema

O avaliador devolve `atributos[].jogo` e `atributos[].sistema` separadamente. `final` permanece como alias de `jogo` para compatibilidade, nunca como alternativa para um valor `sistema` ausente. A nota já utilizava o vetor `sistema`; esta mudança só expõe o valor que era omitido, sem trocar fórmulas ou limites.

`apresentar_v1` conserva os dois valores no contrato pessoal como `valor_jogo` e `valor_sistema`. Registros antigos sem o segundo valor não são recalculados silenciosamente: mostram ausência na vitrine, e passam a conter os dois após avaliação e salvamento explícitos pelo editor. O mesmo vale para cópias locais do navegador.

Prova HTTP/DOM de 06/09: Shevchenko 379897 tem Finalização 90 no jogo / 111 no sistema e nota inalterada 110,8290229441381. Remover a habilidade testada mantém o vetor de jogo, muda Drible no sistema de 94 para 92 e atualiza a nota. Não há cálculo no navegador.

Teste reproduzível: `tests/editor-servidor.sql` (transação com rollback).
Não usar contas reais para testes destrutivos. Validação visual a 100% e envio de
e-mail de autenticação não foram automatizados nesta execução; testes DOM não
substituem renderização real nem alegam que um usuário real entrou na conta.
