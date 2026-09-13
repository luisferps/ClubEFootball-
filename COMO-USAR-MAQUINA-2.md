# Instalação da Máquina 2 pelo GitHub

Este repositório contém os aplicativos atuais, fontes, dependências e manuais,
com cinco executáveis operacionais, um por componente.
Credenciais, fotografias da fila e resultados locais não são versionados.

1. Baixe o repositório e extraia em uma pasta nova.
2. Configure as credenciais locais quando o aplicativo solicitar.
3. Em `2-MOTORES/OTIMIZADOR/OPERACAO-LOCAL-JSON`, abra
   `BAIXAR-FILA-PRINCIPAL.bat` e aguarde a conclusão.
4. Abra `PROCESSAR-FILA-PRINCIPAL.bat`.
5. Abra `ENVIAR-FILA-PRINCIPAL.bat` para enviar os resultados.

Use apenas uma instância do processador: ela utiliza quatro processos.
A fila segue cartas novas → demais com orçamento → demais sem orçamento,
sempre por overall decrescente dentro de cada grupo.

O Bonificador e o Otimizador podem trabalhar em paralelo; a finalização e
publicação de cada linha dependem dos dois resultados.

A entrega física `ClubEfootball-Maquina-2` preparada em 13/09/2026 já continha
uma fotografia conferida de 193.543 linhas. Quem usa essa entrega pode iniciar
o processamento diretamente. O download do GitHub exige o passo 3 acima.
Preserve os resultados e recibos locais de qualquer processamento já iniciado.
