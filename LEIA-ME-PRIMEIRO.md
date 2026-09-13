# Pasta de trabalho — 12/09/2026

Raiz operacional: `C:\Users\Luis Fernando\Downloads\ClubEFootball--main\ClubEFootball--main`.

## Aplicativos mantidos

| Componente | Entrada operacional |
|---|---|
| Site e editor de builds | `Site Novo\ABRIR-SITE-NOVO.cmd` / `Site Novo\index.html` |
| Otimizador e enviador | `2-MOTORES\OTIMIZADOR\OPERACAO-LOCAL-JSON\bin\OperacaoLocalJson.exe`, pelos BATs de baixar, processar e enviar |
| Bonificador | `2-MOTORES\BONIFICADOR\Bonificador ClubEfootball.exe` e `RODAR-LOTE-BONIFICADOR.bat` |
| Complemento local V14 | `2-MOTORES\OTIMIZADOR\COMPLEMENTO-LOCAL-V14\ComplementoLocalV14.exe` |
| Extrator físico | `7-VARREDURA-DO-JOGO\ABRIR-EXTRATOR.cmd` / `Extrator eFootball.exe` |
| Extrator de níveis eFHUB | `7-VARREDURA-DO-JOGO\ABRIR-EXTRATOR-NIVEIS-EFHUB.cmd` / `Extrator Niveis eFHUB.exe` |
| Extrator de fotos | `8 - EXTRATOR DE FOTOS\INICIAR-EXTRATOR-DE-FOTOS.cmd` |
| Serviço Railway — uso atual a confirmar | `6-AVALIADOR-NO-RAILWAY\Procfile`; fontes preservados por ter papel próprio e não haver prova de aposentadoria |

Os BATs são entradas para os aplicativos, não versões extras. Fontes, dependências, compiladores, testes, configurações e manuais continuam necessários. Resultados, pacotes de fila e recibos atuais não são lixo.

## Rodada atual v6 — 13/09/2026

Molde v6 aplicado com as cinco mudanças aprovadas. O lote 1209 foi aposentado.
A fila atual é `39da8ff4-7a4a-4ec7-8641-e81b5677ad4c`: 193.543 linhas
elegíveis, seladas e pausadas. Ordem: novas cartas, demais com orçamento,
demais sem orçamento; overall decrescente em cada grupo.

Use `2-MOTORES/OTIMIZADOR/OPERACAO-LOCAL-JSON/BAIXAR-FILA-PRINCIPAL.bat`.
O processamento usa quatro processos na Máquina 2 e grava JSONs em ordem.
O Bonificador confere/reaproveita componentes vigentes e calcula somente
exceções. Consulte `4-DOCUMENTOS/OTIMIZADOR/FILA-V6-MAQUINA-2.md` para
etapas concluídas e pendências; fila preparada não significa recálculo concluído.

## Recuperação

Material retirado: `C:\Users\Luis Fernando\Downloads\ClubEFootball-BACKUP-LIMPEZA-20260912`.

O backup preserva os caminhos relativos originais. O manifesto `MANIFESTO.csv` contém caminhos, tamanhos e hashes dos arquivos arquivados. Não executar aplicativos pelo backup. A restituição deve ser pontual, conferindo antes se o destino já existe.

Documentos históricos podem mencionar caminhos arquivados. Isso não os torna aplicativos operacionais atuais.
