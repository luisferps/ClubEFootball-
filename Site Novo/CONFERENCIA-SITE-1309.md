# Conferência do Site — 13/09/2026

Registro das verificações desta rodada, sem promessa de latência ou estado futuro.
Regras de operação: [Manual do Site](MANUAL-DO-SITE-NOVO.md).

## Correções verificadas

- Busca sem acentos: formas acentuadas e não acentuadas retornaram os mesmos IDs.
- Ciclo de interface: respostas atrasadas descartadas, seções independentes,
  transporte compartilhado e remoção dos trechos mortos identificados.
- Grau global: seis transições entre 1, 2 e 3, resposta atrasada, link divergente,
  grau sem publicação e consulta pessoal sem sobrescrever o registro salvo.
- Ficha: consulta explícita por grau e estados sem publicação; editor preserva sua
  exceção de escolha local. Nove comparações de referência de estrelas passaram.
- Boxes: 51 verificações de ordenação e correspondência entre prévia e detalhe,
  cobrindo os três graus. Antecipação somente da próxima página, reutilização,
  isolamento de grau e cancelamento na saída verificados.
- Banco: leitura pronta por grau, invalidação e atualização concorrente verificadas;
  job automático executado com sucesso. A consulta não reconstrói todas as boxes.
- Site publicado: pacote de 20 arquivos públicos; leitura dos arquivos servidos
  conferida durante as publicações. Manuais, credenciais e SQL ficam fora do pacote.

Medições da leitura pronta: primeira conexão de Boxes em 721 ms; demais consultas
em 117–137 ms no ensaio. São observações dessa execução, não garantia de desempenho.

## Alcance e pendências

O Bonificador terminou para a população auditada e as primeiras publicações ativas
foram confirmadas no banco. Totais e limites dessa prova ficam somente no
[Estado Atual](../4-DOCUMENTOS/ESTADO-ATUAL.md), que substitui a antiga pendência de
aguardar os primeiros resultados. A rodada integral do Otimizador não foi declarada
concluída. A divergência de boost do técnico em atributos de peso zero permanece
registrada em [Paridade do Editor](PARIDADE-EDITOR-MOLDE-V6.md).
