# Relatório — Extrator eFootball 4.4

## Resultado

A versão operacional agora abre diretamente com **Resumo desta abertura**. Ela localiza as fontes, compara cartas com `clube_novo.carta_jogo` em leitura e confere as famílias de metadados sem clique inicial e sem seletor JSON.

Na instalação validada, o indicador final ficou verde em **Tudo atualizado**:

- cartas: 43.072 conferidas, zero diferenças pendentes;
- metadados: zero novas, zero alteradas e zero ausentes nas famílias suportadas;
- famílias sem cobertura integral: identificadas como **Não suportada nesta atualização**, sem promoção ou aplicação.

Quando houver novidades, o mesmo indicador fica vermelho em **Atualização disponível** e o conjunto revisável permanece disponível até a decisão do usuário. Fontes e opções técnicas foram movidas para baixo do resultado.

## Preparação e aplicação

O pré-voo mostra **Preparando** imediatamente, bloqueia o botão e termina obrigatoriamente em concluído, sem mudanças ou bloqueado. A aplicação final foi alterada para mostrar **Aplicando carga**, bloquear todos os controles e terminar em sucesso com readback ou erro recuperável.

O executor usa `execution_id` + SHA-256 da seleção. Pré-voos repetidos reutilizam o token vigente; chamadas simultâneas recebem o estado `applying`; uma execução concluída reutiliza o manifesto persistido. A consulta somente leitura da aplicação anterior confirmou o estado `completed`, sem repetir qualquer gravação.

## Estado factual do banco

A aplicação autorizada anterior foi integral: 269 inserções, 34 atualizações, zero inativações e readback de 303 registros. A auditoria final por todos os 29 campos confirmou:

- `clube_novo.carta_jogo`: 43.072 IDs únicos, correspondência exata à referência atual;
- `clube.carta_jogo`: 42.803 IDs únicos, correspondência exata à carga legada.

Nenhuma nova escrita foi feita durante a implementação, instalação ou validação da versão 4.4.

## Instalação

- Abrir: `C:\Users\Luis Fernando\Downloads\Clubefootball V4\7-VARREDURA-DO-JOGO\Extrator eFootball.exe`
- Versão: 4.4.0.0
- SHA-256: `ec8473443b8163268131f2b3b4a64166f5d29ec2bfc7465d275458aa38d858be`
- Recuperação preservada: `RECUPERACAO\2026-08-27-ANTES-ABERTURA-AUTOMATICA-V44`
- Manual: `DOCUMENTACAO\MANUAL-DO-EXTRATOR.md`
