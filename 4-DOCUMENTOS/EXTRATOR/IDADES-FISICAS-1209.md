# Idades físicas: cartas acima de 47 anos

O leitor descartava silenciosamente cartas acima de 47 anos. O contrato ativo
carta.idade declara Player.bin, bit 536, largura 6, transformação raw+10.
Portanto a faixa representável é 10–73. O limite anterior não vinha do contrato.

Na fonte SHA256 051491deb87eacc3772cc254b66ec8649860dda5351e80c28524b3aad3de8f5d:

- 87961467093288: Miura Kazuyoshi, 50.
- 105568953959383: Gianluigi Buffon, 48.
- 105592576279511: Gianluigi Buffon, 48.

Corrigidos extrator-core.js, contrato-v46-runtime.js e card_completeness.py.
O banco já declara corretamente os seis bits; não foi necessário mudar o mapa.
Nenhuma elegibilidade foi forçada: lista de indisponíveis, vínculos, níveis e
orçamento continuam com suas próprias verificações. O leitor básico retorna
43.635 cartas. Teste físico dos três IDs e testes de limite 10/73 (9/74
recusados) passaram. A tela de prontidão usa o avaliador corrigido.

A rodada 232232 foi cancelada antes da importação para refazer o pacote com
as três cartas. Nenhum dos pacotes anteriores foi aplicado. Sua leitura de
técnicos serve como evidência de 65/65 Sobreposição e 106/106 boosts corretos.
