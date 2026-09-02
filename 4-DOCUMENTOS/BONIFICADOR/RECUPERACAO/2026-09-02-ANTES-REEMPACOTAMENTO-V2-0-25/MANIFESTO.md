# Snapshot antes do reempacotamento V2.0.25

Escopo: unificação da leitura de fila do pipeline com a interface e recompilação
versionada do único aplicativo local. Não abrange banco, filas, fórmulas, moldes,
pesos, Otimizador, Extrator ou resultados.

Arquivos preservados sem alteração em `arquivos/`:

- `motor_bonus.py`;
- `servidor.py`;
- `ClubEfootballBonificadorLauncher.cs`;
- `BonificadorComponente.bin`;
- `Bonificador ClubEfootball.exe`.

Recuperação: fechar o Bonificador, restaurar esses cinco arquivos nos respectivos
caminhos operacionais e abrir novamente o único `Bonificador ClubEfootball.exe`.
O novo número de versão impede reutilização de componente local de versão anterior.

## Hashes SHA-256 antes da alteração

```text
14C58747EC3DE3382D0CE12DF9537074F6D09373BD3DF3F4C9A5D0717E2CF826  Bonificador ClubEfootball.exe
3586D4CD135EC71EA5DE04EA7F69908D288BF27F4FA72EDF253575758877B587  BonificadorComponente.bin
4C7DF482FD696509FB0A1C0829A9333E9C5C80223F8629EE23FD3D93CBE9CF8D  ClubEfootballBonificadorLauncher.cs
463085998BC1E5D5494FA88C758E134809347D129C201F52F39E1709C5CDBEC9  motor_bonus.py
CA9125B96E4AFD4E0F4DA73A35E067BE6E1F08744AEEA69CFB45EA30E1326FE2  servidor.py
```
