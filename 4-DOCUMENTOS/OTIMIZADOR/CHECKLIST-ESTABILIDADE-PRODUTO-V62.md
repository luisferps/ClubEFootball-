# Checklist V62 — recarga segura da configuração local

- [x] O ícone compara a data de `config.txt` com o serviço local ocioso.
- [x] Uma mudança válida de configuração reinicia apenas o serviço ocioso no
  próximo clique; não exige Gerenciador de Tarefas.
- [x] Com worker ativo, o ícone não encerra nem reinicia o cálculo.
- [x] Configuração inválida abre novamente o formulário local, em vez de usar
  silenciosamente um valor antigo.
- [x] Fórmula, motor, fila, publicação e arquivos do front-end permanecem
  inalterados.

Rollback físico: `RECUPERACAO/20260901-v62-reinicio-config-antes/`.
