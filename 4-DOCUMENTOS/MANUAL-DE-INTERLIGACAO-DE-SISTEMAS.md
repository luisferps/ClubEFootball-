# Integração dos sistemas

O banco operacional é `clube_novo`. Dados físicos entram pelo Extrator; os motores
consomem contratos canônicos; o site lê a publicação validada por portas públicas.

| Etapa | Responsabilidade | O que comprova conclusão |
|---|---|---|
| Extrator | Ler, comparar e aplicar dados/provas respeitando correções manuais | Releitura do persistido |
| Preparação | Selecionar elegíveis, ordenar e selar contrato/fotografia | Pacote validado |
| Otimizador | Evolução, técnico, ímpetos, habilidades, atributos e nota do motor | Resultado aceito no banco |
| Bonificador | Reaproveitar bônus conformes e calcular exceções | Bônus compatível persistido |
| Composição | Validar identidade/selos e combinar os dois resultados | Publicação ativa confirmada |
| Leitura de Boxes | Preparar classificação por grau e atualizar após mudanças | Revisão aplicada após atualização bem-sucedida |
| Site | Exibir dados públicos e estados | Leitura pública e tela coerentes |

Otimizador e Bonificador são independentes durante o cálculo. O enviador pode
acompanhar o Otimizador. A publicação depende de ambos e de seus contratos compatíveis.
`finalizar_publicar_linha_v1` e a ponte ativa realizam a composição; não publicar
somente porque um JSON chegou. A substituição preserva a publicação anterior válida
até a nova estar pronta, com sua régua identificada.

Resultado local, envio, resultado no banco, publicação ativa e exposição pública
são estados diferentes. A fonte exibível pode aplicar critérios próprios; não tratar
todo resultado oculto como falha. Cartas excluídas ficam fora do universo operacional.

Novas extrações não modificam o pacote selado já em execução. Nova prova de orçamento
retira a espera e devolve elegibilidade; preparação/revisão da fila é etapa própria.
Correção manual registrada prevalece sobre a fonte automática.

As Boxes usam leitura pronta, paginada e separada por grau. Mudanças nas fontes
invalidam a revisão; um job verifica a cada minuto e atualiza quando necessário.
Uma nova nota máxima pode alterar as estrelas de outras cartas. A visita não
recalcula todo o universo. Até o próximo ciclo, permanece a versão anterior
coerente. Ver o [Manual do Site](../Site%20Novo/MANUAL-DO-SITE-NOVO.md).

A rotina é operada pelos aplicativos. O Coordenador automático descrito em planos
antigos não foi implementado por esta rodada; não há promessa de iniciar os aplicativos
sozinho. A regra de reconsulta diária funciona quando o Extrator é executado.

[Aplicativos](../LEIA-ME-PRIMEIRO.md) · [Estado da implantação](ESTADO-ATUAL.md) ·
[Contratos](MANUAL-DAS-TABELAS.md).
