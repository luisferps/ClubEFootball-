# Snapshot — antes da organização operacional do Bonificador

- Movimento autorizado: somente
  `2-MOTORES/motor_bonus.py` → `2-MOTORES/BONIFICADOR/motor_bonus.py`.
- SHA-256 do executável antes do movimento:
  `a0909796e8932426a3b72d677ef77fcf50d820eaced95253449828f4d2bfe7cb`.
- O motor importa somente módulos da biblioteca padrão Python; não há módulo local a
  copiar para a pasta nova.
- `2-MOTORES/config.txt` é compartilhado pelos motores e permanece no local comum.
  Seu SHA-256 neste snapshot é
  `507c3202cc69944461d3272062f60fe4734673d8796106edec6e47780237bcd9`.
- A cópia `config.txt` na raiz já existia, possui o mesmo hash e não é alterada por
  esta organização.
- Recuperação: executar
  `ROLLBACK-ORGANIZACAO-OPERACIONAL.ps1` a partir da raiz do projeto. O script só
  move o arquivo de volta quando o destino existe e o caminho antigo está ausente.
