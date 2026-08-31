# Recuperação — limpeza do pacote único

Data: 31/08/2026.

Esta pasta guarda os itens que foram retirados da raiz operacional do Bonificador:
runtime portátil experimental, caches Python (inclusive o cache da interface), log de abertura antigo e os dois
lançadores paralelos. Eles não participam do fluxo oficial do aplicativo e não devem
ser restaurados em `2-MOTORES/BONIFICADOR` sem uma nova decisão de arquitetura.

Também foram guardados aqui a interface web anterior e os artefatos temporários do
PyInstaller. O aplicativo oficial é nativo; o componente loopback expõe apenas API
local para a janela WinForms, sem página, JavaScript ou CSS.

O antigo `Bonificador Componente Local.exe` não foi preservado como segundo aplicativo:
foi movido, sem alteração de bytes, para
`2-MOTORES/BONIFICADOR/windows-app/assets/BonificadorComponente.bin`. Esse arquivo é
um payload de compilação incorporado no único EXE do operador.

Estado confirmado após a limpeza: `Bonificador ClubEfootball.exe` V2.0.14 abriu com
`Responding=True`, sem página web e com encerramento do componente interno ao fechar.
Fórmulas, banco, dados, fila produtiva e demais motores não foram
alterados.
