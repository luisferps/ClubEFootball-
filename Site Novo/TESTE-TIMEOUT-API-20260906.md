# Teste temporário do limite de carregamento da API

Autorização: usuário aprovou aumentar de 8 para 60 segundos e restaurar se não resolvesse. Escopo limitado a `authenticator.statement_timeout`, sem mudanças de filas, fórmulas, resultados, permissões ou recursos contratados.

## Aplicação e evidências

- Migração local `20260906055738_ficha_api_cache_timeout_temporario_v1.sql`, aplicada com sucesso em 06/09/2026.
- Readback confirmou `authenticator=60s`. Foram preservados `anon=3s`, `authenticated=8s`, `service_role=60s`, `authenticator.lock_timeout=8s` e as bibliotecas da sessão.
- Após o reload, duas chamadas HTTP públicas de `site_novo_ficha_v2`, card `88045755964138`, linha `379897`, continuaram em 503/PGRST002; durações de 3477ms e 1413ms. Isso não mede a duração da carga do catálogo: são os tempos das respostas de erro aos clientes.
- Snapshot de atividade às 05:59:43 UTC encontrou uma consulta PostgREST `SELECT name FROM pg_timezone_names` ativa havia 94 segundos. A observação confirma lentidão no carregamento interno, mas não identifica a causa do esgotamento de recursos nem prova que o novo limite foi adotado por toda conexão já existente.
- A consulta aos advisors expirou (`Query read timeout`); não foi declarada aprovada.

## Reversão

- A primeira tentativa falhou na inicialização da tabela de histórico por timeout de conexão. Uma leitura posterior confirmou que continuava em 60s; não foi presumida restauração.
- A segunda aplicação de `ficha_api_cache_timeout_restaurar_v1` retornou sucesso, restaurando 8s e notificando reload de configuração/schema.
- Readback final confirmou `authenticator=8s`, `anon=3s`, `authenticated=8s` e `service_role=60s`, com as demais configurações originais preservadas.
- Arquivo local da reversão: `20260906060001_ficha_api_cache_timeout_restaurar_v1.sql`. SQL de recuperação separado preservado em `RECUPERAR-TIMEOUT-API-8S-20260906.sql`.

Resultado: o aumento não recuperou a API durante o teste. Nenhum restart do projeto, encerramento de sessão, pausa de worker, upgrade ou mudança de timeout dos usuários foi executado. O erro de carregamento exige investigação de desempenho/recursos; não foi mascarado por fallback de dados no site.
