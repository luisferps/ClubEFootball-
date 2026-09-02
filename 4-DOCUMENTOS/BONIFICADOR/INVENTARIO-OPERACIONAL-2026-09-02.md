# Inventário físico do Bonificador — 02/09/2026

Inventário de leitura feito antes de qualquer reorganização física adicional. Nenhum
arquivo foi movido ou removido por este inventário.

| Item | Classificação | Papel | Observação |
|---|---|---|---|
| `2-MOTORES/BONIFICADOR/Bonificador ClubEfootball.exe` | operacional | único aplicativo do operador | V2.0.25.0; contém o componente local como recurso interno |
| `2-MOTORES/BONIFICADOR/motor_bonus.py` | operacional/manutenção | cálculo e writer do Bonificador | lê somente contratos canônicos; fila V5 |
| `2-MOTORES/BONIFICADOR/interface/servidor.py` | operacional/manutenção | componente loopback para a janela | não é interface web e não expõe banco ao navegador |
| `2-MOTORES/BONIFICADOR/windows-app/ClubEfootballBonificadorLauncher.cs` | compilação/manutenção | fonte da janela WinForms | gera o único EXE |
| `2-MOTORES/BONIFICADOR/windows-app/COMPILAR-APLICATIVO.ps1` | compilação/manutenção | recompila o EXE | não é entrada normal do operador |
| `2-MOTORES/BONIFICADOR/windows-app/assets/BonificadorComponente.bin` | compilação | componente incorporado no EXE | não é segundo aplicativo |
| `2-MOTORES/BONIFICADOR/windows-app/assets/icone-bonificador-clubefootball.*` | compilação | ícone do EXE | ativos do pacote |
| `2-MOTORES/config.txt` | compartilhado/local | conexão da máquina | fora do Bonificador porque também serve a outros motores; não copiar nem embutir |
| `__pycache__/` e `interface/__pycache__/` | gerado | cache local do Python | não são entrada do operador, fonte ou componente incorporado; preservados nesta etapa porque a diretriz de organização proíbe exclusão sem ação própria autorizada |

## Cadeia verificada

`Bonificador ClubEfootball.exe` → recurso `BonificadorComponente.bin` →
`interface/servidor.py` → `motor_bonus.py` → RPCs canônicas V2/V5/V4 do
Bonificador. A janela usa o loopback em `127.0.0.1`; a configuração fica somente
na máquina e não é entregue à janela como conteúdo de interface.

## Conclusão do inventário

Não existe segundo aplicativo operacional na raiz. O único arquivo abrível pelo
operador é `Bonificador ClubEfootball.exe`; os demais itens são fonte, compilação,
ativo interno ou configuração compartilhada. Qualquer movimentação futura deve manter
essa cadeia e recompilar o único EXE, com snapshot e validação de recurso incorporado.
