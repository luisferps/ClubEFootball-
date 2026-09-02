# Snapshot antes do batch operacional do Bonificador

Criado em 02/09/2026, antes de acrescentar a camada persistente de lote, as rotas
locais e os controles da janela. Esta pasta é somente recuperação; não é runtime nem
entrega portátil.

| arquivo salvo | SHA-256 |
|---|---|
| `arquivos/ClubEfootballBonificadorLauncher.cs` | `A3EE115E35CF0DC6404980AE6235E11AD7AEC56265C775C8C1A29708C222958E` |
| `arquivos/motor_bonus.py` | `E8541B8F08558D7E4DB67BF72C1C437627D402F8A76ABFBFAB2DD3CAF52BFD41` |
| `arquivos/servidor.py` | `CA9125B96E4AFD4E0F4DA73A35E067BE6E1F08744AEEA69CFB45EA30E1326FE2` |

O rollback do código consiste em restaurar esses três arquivos e recompilar o único
EXE canônico pelo script `2-MOTORES/BONIFICADOR/windows-app/COMPILAR-APLICATIVO.ps1`.
O banco recebeu a migração documentada em
`4-DOCUMENTOS/BONIFICADOR/SQL/APLICAR-LOTE-OPERACIONAL-BONIFICADOR-V1.sql`; nenhuma
linha de jogo, cálculo, bônus ou publicação foi alterada na preparação.
