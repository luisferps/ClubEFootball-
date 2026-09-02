# Checklist V61 — runtime portátil completo

- [x] `runtime/_internal/base_library.zip` deixou de ser ignorado pelo Git.
- [x] O arquivo tem 1.333.490 bytes, abaixo do limite de publicação.
- [x] O ícone valida a biblioteca antes de iniciar o serviço local.
- [x] URL formatada como link/Markdown é recusada antes de iniciar o serviço.
- [x] Teste real do ícone para serviço local em `127.0.0.1:8769` passou sem
  iniciar worker, reserva, cálculo ou publicação.
- [x] Testes: 32 do painel e 11 da fila local.
- [x] Fórmula, pesos, moldes, Ímpetos condicionais, fila e publicação não
  foram alterados.

## Entrega entre computadores

1. Publicar a revisão que inclui `base_library.zip`.
2. Baixar/substituir a pasta completa no outro Windows.
3. Criar `config.txt` local com URL HTTPS literal e Secret key literal.
4. Abrir somente `Otimizador ClubEfootball.exe`.

O rollback físico desta revisão está em
`RECUPERACAO/20260901-v61-runtime-zip-portatil-antes/`.
