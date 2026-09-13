# ClubEfootball — pasta oficial

Pasta de trabalho: `C:\Users\Luis Fernando\Downloads\ClubEfootball-Maquina-2`.
GitHub: https://github.com/luisferps/ClubEFootball- — branch `main`.
Atualização dos manuais: 13/09/2026.

## Onde começar

| Sistema | Entrada | Manual |
|---|---|---|
| Extrator físico e níveis eFHUB | `7-VARREDURA-DO-JOGO/ABRIR-EXTRATOR.cmd` e `ABRIR-EXTRATOR-NIVEIS-EFHUB.cmd` | [Extrator](7-VARREDURA-DO-JOGO/DOCUMENTACAO/MANUAL-DO-EXTRATOR.md) |
| Otimizador | BATs de baixar, processar e enviar em `2-MOTORES/OTIMIZADOR/OPERACAO-LOCAL-JSON` | [Otimizador](4-DOCUMENTOS/MANUAL-DO-OTIMIZADOR.md) |
| Bonificador | `2-MOTORES/BONIFICADOR/Bonificador ClubEfootball.exe` | [Bonificador](4-DOCUMENTOS/MANUAL-DO-BONIFICADOR.md) |
| Fotos | `8 - EXTRATOR DE FOTOS/INICIAR-EXTRATOR-DE-FOTOS.cmd` | [Fotos](8%20-%20EXTRATOR%20DE%20FOTOS/MANUAL-DO-EXTRATOR-DE-FOTOS.md) |
| Site e editor | https://imaginative-granita-ace1ca.netlify.app/ | [Site](Site%20Novo/MANUAL-DO-SITE-NOVO.md) |

[Instalação na Máquina 2](COMO-USAR-MAQUINA-2.md) ·
[Integração](4-DOCUMENTOS/MANUAL-DE-INTERLIGACAO-DE-SISTEMAS.md) ·
[Estado da implantação](4-DOCUMENTOS/ESTADO-ATUAL.md) ·
[Referência técnica](4-DOCUMENTOS/MANUAL-TECNICO.md).

Use uma instância de processamento e uma de envio. Os quatro processos de cálculo
são internos ao Otimizador. Preserve filas, JSONs e recibos ao atualizar a pasta.
O GitHub não contém credenciais nem os resultados locais da Máquina 2.

Fontes, dependências, testes e SQLs são necessários à manutenção, não versões extras
dos aplicativos. O complemento V14 separado atende correções de resultados prontos;
as buscas novas já incluem o complemento. Não iniciar outra rodada corretiva por rotina.
O serviço Railway permanece preservado; seu uso atual não foi comprovado nesta revisão.

Manuais descrevem o funcionamento atual. SQLs, mapeamentos e provas específicas ficam
nas pastas técnicas. Versões anteriores dos documentos são recuperáveis pelo histórico
do Git; não executar planos antigos como se fossem pendências atuais.
