# Carregamento da Ficha — evidência de recursos

Inspeção somente leitura do Dashboard do projeto `trqqpsnafpbudtvvicch`, em 06/09/2026, após o teste de timeout já revertido.

- Instância selecionada: **Nano**, até 0,5 GB de memória, CPU compartilhada.
- Painel de infraestrutura mostrava CPU **97%**, memória **72%** e Disk IO **100%**, com alerta de esgotamento de múltiplos recursos. São os valores exibidos no painel no momento da inspeção, não uma série histórica exportada.
- Disco ocupado: **2,33 de 8 GB**; não é falta de espaço de armazenamento.
- Consulta ativa vista no banco: carregamento PostgREST de `pg_timezone_names`; os logs anteriores também mostravam timeout na consulta de metadados do catálogo. A hipótese de saturação é coerente com o painel; não foi atribuída a carga a um motor específico.
- Alternativa apresentada pelo próprio Dashboard: **Micro**, 1 GB de memória, CPU de dois núcleos, marcado **Free Upgrade**, pelo mesmo preço por hora do Nano: **US$ 0,01344/h**.

Foi solicitada autorização específica para Nano → Micro por envolver interrupção do banco compartilhado. Até receber aprovação, nenhum seletor foi alterado, nenhuma mudança de infraestrutura foi aplicada e nenhum worker/sessão foi encerrado.

Essa autorização não cobre Small ou planos mais caros, aumento do disco, retirada do limite de gastos, réplicas, reprocessamento de filas ou qualquer outra alteração operacional.

## Mudança autorizada em 06/09/2026

O usuário respondeu `autorizo` à proposta Nano → Micro. No Dashboard foi selecionado somente Micro. A revisão confirmou **Nano → Micro**, **US$ 9,68/mês antes e depois**, diferença **US$ 0,00/mês**, antes de impostos. Disco, limite de gastos e demais opções não foram alterados.

Após `Confirm changes`, o Dashboard mostrou `Resizing project`, e a API de gerenciamento confirmou `RESIZING`. A reinicialização faz parte da mudança autorizada; não foram encerradas sessões ou reiniciados workers manualmente. A conclusão e a consulta pública ainda precisam de confirmação posterior.

### Conclusão verificada

- API de gerenciamento passou para **ACTIVE_HEALTHY**.
- Dashboard confirmou **t3a.micro**, Micro selecionado, **US$ 0,01344/h**, **1 GB** de memória; disco de **8 GB** e limite de gastos preservados.
- Postgres reiniciou em **2026-09-06 06:14:40 UTC** (03:14:40 de Brasília).
- Consulta pública real `site_novo_ficha_v2`, carta `88045755964138`, linha `379897`: **HTTP 200**, `status=pronto`, às **06:14:49 UTC**, em **987 ms**; nova resposta válida às **06:15:08 UTC**, em **275 ms**.
- Dados confirmados: Shevchenko, nota **110,8290229441381** (110,83 na tela), **0/64** pontos restantes, **5** sugestões de habilidades e **12** builds publicadas.
- Houve uma resposta intermediária não JSON (HTML), logo após o reinício; o primeiro teste não registrou seu status HTTP. A consulta seguinte foi válida. Esses testes confirmam recuperação naquele momento, não estabilidade prolongada.
- Timeouts conferidos depois do reinício: `anon=3s`, `authenticated=8s`, `authenticator=8s` (lock timeout 8s), `service_role=60s`. A alteração temporária anterior permanece revertida.
- Testes locais de JavaScript, consulta, falha HTTP e falha de foto passaram. Não representam validação visual do layout em zoom 100%.
