# Manual do Otimizador

O Otimizador busca a distribuição de evolução e as escolhas permitidas de técnico,
ímpetos e habilidades para cada carta/posição/especialidade. Usa o contrato selado da
fila; produz o resultado de atributos e a nota do motor. O Bonificador fornece suas
parcelas separadamente; a publicação depende da composição válida dos dois.

## Operação na Máquina 2

Na pasta `2-MOTORES/OTIMIZADOR/OPERACAO-LOCAL-JSON`:

1. `BAIXAR-FILA-PRINCIPAL.bat`: obter e validar a fotografia. Se a entrega já contém
   a fotografia validada em uso, não substituir o pacote durante o processamento.
2. `PROCESSAR-FILA-PRINCIPAL.bat`: calcular e salvar os JSONs locais.
3. `ENVIAR-FILA-PRINCIPAL.bat`: enviar e aguardar confirmação do banco por linha.

Uma janela de processamento utiliza quatro processos. Uma janela de envio pode rodar
ao mesmo tempo. Não abrir dois processadores ou dois enviadores para a mesma pasta.
Há um escritor local e barreira entre grupos: cartas novas, demais com orçamento,
demais sem orçamento, sempre por overall decrescente dentro do grupo.

Ctrl+C solicita parada segura. Resultados já gravados e recibos devem ser preservados.
Retome pelos mesmos BATs. Não apagar JSONs para reiniciar nem editar selos. Erros de
contrato exigem conferir pacote/versão; não forçar envio. Cálculo salvo, envio confirmado
e publicação são estados diferentes. [Instalação](../COMO-USAR-MAQUINA-2.md).

## Entradas e regras

- Autoridade operacional: `clube_novo`; contratos `otimizador_carta_v3`,
  `otimizador_cartas_v3`, `otimizador_regua_v2` e `otimizador_pool_habilidades_v3`.
- A carta precisa de evidência válida ou decisão manual efetiva de nível/orçamento.
  Nível 1 comprovado permite orçamento zero. Orçamento não divulgado não é zero.
- Técnicos pertencem a este motor. Proficiência atua nos 26 atributos antes dos
  boosts; depois entram ímpetos e a valorização de habilidades na ordem oficial.
- A referência base + evolução é limitada a 99; a proficiência usa tabela e
  truncamento oficiais. Não inverter a ordem para acrescentar boosts antes dela.
- A implementação exata e o arredondamento estão em `2-MOTORES/equacao.py` e no
  contrato; os bytes do núcleo compõem o selo. Não reformatar fontes sem avaliar o hash.
- Habilidades nativas são preservadas. A busca respeita bloqueios por função;
  o editor pessoal não herda os vetos estratégicos do preenchimento automático.
- Após a busca, o complemento V14 preenche vagas permitidas por incidência nativa
  de pelo menos 10%, com exceções condicionais 69/48. Uma habilidade gêmea não exclui
  automaticamente a candidata; o mesmo ID já presente exclui.

## Molde vigente: v6

| Função | Atributo | Alvo | Peso |
|---|---|---:|---:|
| Meia ofensivo (8) | Finalização `PB:530:6` | 89 | 7 |
| Meia ofensivo (8) | Aceleração `PB:486:6` | 89 | 3 |
| Meia armador (10) | Velocidade `PB:434:6` | 85 | 7 |
| Meia armador (10) | Aceleração `PB:486:6` | 85 | 3 |
| Meia armador (10) | Curva `PB:428:6` | 83 | 3 |

Equilíbrio do Meia armador permanece alvo 86/peso 7. São duas funções alteradas.
Os pesos decorrem da classificação 5/4/4/resto; não há exceções cravadas manualmente.
As propostas para Falso nove e Atacante infiltrador não foram aplicadas.

Mourinho ASTROS está incluído: ID `17608560707469`, proficiência máxima 90,
contra-ataque com bola longa, +1 Finalização e +1 Contato físico. Outras cartas de
Mourinho têm identidades próprias. Sobreposição lê `Coach.bin` bit 192/largura 7;
Conte tem 69 nesse campo, não 96. [Prova física](EXTRATOR/SOBREPOSICAO-192-1209.md).

## Publicação e manutenção

Resultados entram em `build_otimizador`, associados a `build_linha_card`. Contrato,
fórmula, complemento e identidade precisam ser compatíveis. A composição oficial
valida também o Bonificador antes de ativar a publicação. Não copiar uma nota antiga
para uma linha nova nem confundir resultado recebido com nota pública.

A nota publicada usa `100 + 50 × motor / (máximo teórico − mínimo teórico) + bônus`.
O frontend não refaz essa conta. [Normalização](NORMALIZACAO-0909/AMPLITUDE-VIGENTE.md).

[Habilidades](OTIMIZADOR/HABILIDADES-0909/REGRA-APROVADA.md) ·
[Complemento](OTIMIZADOR/COMPLEMENTO-1009/REGRA-APROVADA.md) ·
[Estado da rodada](ESTADO-ATUAL.md). Registros de instalação antigos não são passos
para repetir na pasta atual. O executor separado de complemento atende rodadas
corretivas próprias, não o processamento normal já configurado.
