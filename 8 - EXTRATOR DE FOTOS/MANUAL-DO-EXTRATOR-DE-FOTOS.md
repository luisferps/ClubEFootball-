# Manual do Extrator de Fotos

O aplicativo procura imagens para cartas sem `foto_url_cloudinary`, aproveita a foto
já existente no Cloudinary ou obtém a imagem da fonte eFHUB. Não sobrescreve uma URL
já preenchida. Não gera imagem fictícia quando a fonte ainda não tem foto.

## Operação

Abra `INICIAR-EXTRATOR-DE-FOTOS.cmd` nesta pasta:

| Opção | Ação |
|---|---|
| 1 | Iniciar ou retomar |
| 2 | Consultar estado |
| 3 | Pausar |
| 4 | Continuar |
| 5 | Parar |
| 6 | Configurar |
| 7 | Verificar |
| 0 | Sair do menu |

`VIGIA-EXTRATOR-DE-FOTOS.cmd` acompanha/reinicia o processo a cada 60 segundos.
Fechar a janela não equivale a parar o worker; use a opção 5. Pausa e parada são
cooperativas. Evite duas instâncias para a mesma pasta.

Configure Cloudinary e conexão administrativa do banco somente no fluxo local.
A proteção DPAPI depende do usuário e computador Windows: uma configuração copiada
de outra máquina pode precisar ser refeita. Use a conexão de sessão indicada pelo
aplicativo (porta 5432), não o pool de transações 6543. Não publicar segredos no Git.

## Funcionamento e resultados

Prioridade: cartas do motor primeiro, depois overall decrescente e identidade.
Lotes de 100, quatro tarefas concorrentes e intervalo mínimo de 500 ms. Antes de
baixar novamente, verifica o Cloudinary. O manifesto registra identidades e hashes;
a aplicação preenche somente URL nula da carta correspondente e confirma por releitura.

Uma carta é tentada uma vez por execução. Ao terminar o conjunto, a descoberta procura
novas cartas ainda não tentadas. Se restarem apenas fontes sem imagem, o estado é
`waiting_sources`, não conclusão integral. Outra execução poderá consultá-las novamente.
HTTP 404 da imagem é `fonte_sem_imagem`; não inventar URL para eliminar essa espera.

Estado: `output/operador/estado.json`. Logs: `output/operador/runs`.
Manifestos: `output/runs`. Preserve esses arquivos para retomada/diagnóstico;
eles não são versões extras do aplicativo.

## Limitação conhecida

Foi observado encerramento nativo do Node com código `0xC0000409`. A causa não foi
comprovada; o vigia permite retomada. Se persistir, conserve log e estado antes de
investigar. Não considerar reinício automático prova de correção da causa.

Node, bootstrap, dependências e scripts desta pasta fazem parte do aplicativo.
Não executar uma cópia antiga arquivada. [Índice dos sistemas](../LEIA-ME-PRIMEIRO.md).
