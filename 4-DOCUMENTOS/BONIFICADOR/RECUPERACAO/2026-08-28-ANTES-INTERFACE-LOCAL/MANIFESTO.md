# Snapshot — antes da interface local do Bonificador

- Estado existente: `2-MOTORES/BONIFICADOR/` contém somente
  `motor_bonus.py`, SHA-256
  `a0909796e8932426a3b72d677ef77fcf50d820eaced95253449828f4d2bfe7cb`.
- A interface acrescenta apenas arquivos novos em `2-MOTORES/BONIFICADOR/interface/`,
  `2-MOTORES/BONIFICADOR/windows-app/`, o ícone, o EXE e o lançador local. Não altera
  motor, fórmulas, banco, UI principal, Extrator ou Otimizador.
- O rollback é exclusivamente de arquivos novos e está em
  `ROLLBACK-INTERFACE-LOCAL.ps1`. Ele verifica os caminhos exatos antes de removê-los.
