# Sobreposição: endereço corrigido em 12/09/2026

Fonte atual: DT870 atualizado, Coach.bin SHA-256
`cb2484b8d29d4d966a22202cf463719c51c968a75f83fad05667263f4955eced`.
Registros de 176 bytes, identidade u64 little-endian no início do registro.

O campo correto é **bit 192, largura 7, unsigned little-endian**, antes da
proficiência longBall no bit 199. O endereço antigo 135 foi rejeitado.

Foram comparados todos os 65 IDs da referência `tecnico_efhub_20260912` com
o arquivo atual. Os 65 existem na fonte. Bit 192: 65/65 iguais; bit 135:
0/65. O próximo candidato, bit 199, coincide em apenas 36/65. Conte
`17609097478250` tem Sobreposição 69. Amostras completas, posições dos
registros e hashes em `SOBREPOSICAO-192-1209.json`.

Banco: campo 13 do contrato atualizado transacionalmente, exigindo o hash
observado e o endereço anterior. A view do catálogo herda o endereço novo.
Código: leitor do núcleo usa 192; leitores por contrato recebem o campo
atualizado. Teste físico permanente passa nos 65 técnicos pela rotina real
do núcleo, com 1.495 técnicos lidos.

Os 65 valores já corrigidos manualmente foram registrados em `valor_do_dono`,
incluindo sua confirmação. São 130 proteções por campo; os números não mudaram.
A evidência física não foi fabricada no histórico: a próxima varredura gerará
pacote com bit/hash/registro atuais. A rodada 224315 usa o contrato anterior
e deve ser substituída por nova rodada pelo aplicativo.

Tela: a conclusão da varredura passa a informar comparação e revisão dos
dados, sem mandar conferir boxes que não foram atualizadas. Relatórios de
níveis explicam a prioridade manual. Executável previsto: 5.4.0.3.

O mapeamento foi corrigido e testado; recarga integral de técnicos, confirmação
dos boosts, nova extração aplicada e fila v6 continuam etapas do plano principal.

## Validação do leitor tipado

O teste inicial do núcleo não cobria o catálogo estilo_jogo_tecnico, ainda em bit 135. Esse catálogo foi corrigido para 192 e relido. metadata-v46-runtime agora exige igualdade de endereço entre catálogo e contrato para todos os seis estilos. O teste teste-tecnicos-leitor-tipado.js executa o caminho completo com contrato atual: 65 proficiências e 106 boosts conferidos; uma divergência reintroduzida deve ser recusada. Pacotes das rodadas 224315 e 225832 não foram aplicados e precisam ser substituídos por nova varredura.
