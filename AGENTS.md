# Regras atuais do projeto

Pasta oficial: `C:\Users\Luis Fernando\Downloads\ClubEfootball-Maquina-2`.
GitHub: `https://github.com/luisferps/ClubEFootball-.git`, branch `main`.
Entrada documental: [LEIA-ME-PRIMEIRO.md](LEIA-ME-PRIMEIRO.md).
Pendências: [ESTADO-ATUAL.md](4-DOCUMENTOS/ESTADO-ATUAL.md).

## Trabalho e autoridade

- Respeitar o escopo atual de Luis. “Somente leitura” e “segurar” são limites reais;
  pausas históricas não anulam autorização posterior explícita.
- Conferir as quatro frentes afetadas: banco, código dos aplicativos, manuais e tela.
  Soluções devem servir à operação diária, sem IDs pontuais onde cabe uma regra geral.
- Somente `clube_novo` é operacional; `clube` é legado, sem fallback.
- Usar aplicativos existentes no fluxo do operador; não exigir SQL/terminal diariamente.
- Preservar processos em execução, configurações, filas, JSONs e recibos. Não publicar
  credenciais. Não iniciar ou reabrir lotes a partir de instruções históricas.

## Dados e extração

Correção manual deve ser registrada em `valor_do_dono` com destino, chave completa,
coluna, valor JSON e motivo. UPDATE direto não registra decisão. O Extrator não pode
remover a proteção; conferir prova e valor efetivo separadamente.
[Contrato](4-DOCUMENTOS/EXTRATOR/PRIORIDADE-CORRECOES-MANUAIS.md).

Cartas excluídas não são defeitos ou pendências. Usar `carta_operacional_v1` ou filtro
equivalente antes de contar. Orçamento aguardando divulgação é estado normal;
`carta_orcamento_pendente_automatico_v1` governa o aviso sem IDs fixos. Não inventar
orçamento zero. Reconsulta diária depende da execução do Extrator. Prova válida
devolve elegibilidade, sem alterar pacotes selados já em uso.
[Regra](4-DOCUMENTOS/ORCAMENTO-REGRA-DIARIA.md).

## Motores e apresentação

Frontend: não manter código morto nem implementações concorrentes da mesma
responsabilidade. Centralizar utilidades comuns e invalidar respostas antigas após
nova escolha ou fechamento. A busca deve funcionar sem exigir acentos.
Textos de todas as telas: inicial maiúscula nas palavras, preservando siglas e
mantendo artigos/preposições/conjunção “e” em minúsculas no meio da expressão.
Exemplo: Estilo de Jogo. Nas boxes, mostrar apenas a sigla da posição (VOL, MAT).

Molde vigente v6: mudanças em Meia ofensivo e Meia armador, descritas no
[manual](4-DOCUMENTOS/MANUAL-DO-OTIMIZADOR.md). Técnicos pertencem ao Otimizador.
Bonificador reaproveita entradas/regras compatíveis, independentemente do nome da
versão, e calcula somente exceções. Cartas novas sem bônus precisam de cálculo.

Habilidades: [política](4-DOCUMENTOS/OTIMIZADOR/HABILIDADES-0909/REGRA-APROVADA.md).
Complemento V14 é posterior à busca e substitui a proibição absoluta de preencher
vagas sem ganho; gêmeas não excluem candidatas. Consultar
[regra](4-DOCUMENTOS/OTIMIZADOR/COMPLEMENTO-1009/REGRA-APROVADA.md).
O seletor pessoal permanece livre dos vetos estratégicos automáticos.

Estilos: principal pela função, ativação pela posição; 1,0/0,5, com somente as duas
exceções aprovadas. Não restaurar promoção genérica do secundário.
[Regra](4-DOCUMENTOS/BONIFICADOR/REGRA-ESTILOS-APROVADA-0909.md).
Altura independente e IA V13 permanecem vigentes.
Normalização atual é por amplitude, não a curva antiga molde 100/teto 110:
[contrato](4-DOCUMENTOS/NORMALIZACAO-0909/AMPLITUDE-VIGENTE.md).

Editor e motor devem produzir os mesmos atributos, parcelas e nota para entradas e
versão iguais. Conferir criar, editar, avaliar, salvar, reabrir e apresentação pública,
incluindo barras, habilidades, técnico, ímpetos/degraus, estilos, corpo/altura, pé,
IA e arredondamento. Um exemplo isolado não encerra divergência geral.

Preservar a publicação anterior válida até substituição confirmada, identificando a
régua antiga. Resultado local, envio confirmado, publicação e exposição são estados
distintos. Só declarar conclusão com readback apropriado ao escopo.
Boxes usam fotografias de avaliação; não revisar essas fotografias sem escopo próprio.

## Manutenção dos manuais

Atualizar a seção vigente, sem empilhar diários contraditórios. Histórico completo
fica no Git; manter provas/mapeamentos/SQLs necessários nas pastas técnicas.
O estado de produção fica em ESTADO-ATUAL, com data e limites, sem contagem antiga
apresentada como atual. Não declarar rodada encerrada porque a documentação terminou.

Regra visual: blocos equivalentes em cada visualização devem ter as mesmas dimensões. Ausência de nota, análise ou foto não reduz o bloco; reservar o espaço correspondente. Nas boxes, alturas uniformes na grade, avaliação e botão alinhados, inclusive entre fileiras.
