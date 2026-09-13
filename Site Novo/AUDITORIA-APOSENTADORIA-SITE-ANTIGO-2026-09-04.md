# Auditoria da aposentadoria dos read-models do site antigo

Data: 04/09/2026  
Projeto Supabase: `trqqpsnafpbudtvvicch`  
Banco operacional preservado: `clube_novo`

## 1. Resultado

Foram removidas seis views públicas da família do site antigo, em duas migrações explícitas e sem `CASCADE`:

1. `public.frontend_boxes_v1`;
2. `public.frontend_home_v1`;
3. `public.frontend_busca_v1`;
4. `public.frontend_ficha_builds_v1`;
5. `public.frontend_ficha_build_v1`;
6. `public.frontend_ficha_v1`.

As cinco views com nome no adaptador antigo foram provadas por leitura do código. A sexta, `frontend_ficha_builds_v1`, era uma view auxiliar da mesma família, sem consumidor executável no repositório e sem dependente no catálogo; ela precisava sair primeiro para permitir a remoção segura das duas views da Ficha.

Nenhuma tabela, função/RPC, schema ou role foi removido. Nenhum `CASCADE` foi usado.

## 2. Serviço verificado antes da cadeia de views

Foram lidos integralmente os nove arquivos atuais de `6-AVALIADOR-NO-RAILWAY`:

| Arquivo | Bytes | Última gravação local |
|---|---:|---|
| `app.py` | 13.862 | 30/08/2026 15:37:50 -03:00 |
| `avaliador.py` | 7.213 | 30/08/2026 15:37:35 -03:00 |
| `banco.py` | 3.952 | 31/08/2026 05:37:07 -03:00 |
| `monta_regua.py` | 3.436 | 30/08/2026 15:37:35 -03:00 |
| `otimizador.py` | 9.343 | 29/08/2026 03:58:36 -03:00 |
| `Procfile` | 68 | 29/08/2026 03:58:36 -03:00 |
| `regua_do_banco.py` | 3.257 | 30/08/2026 15:37:35 -03:00 |
| `requirements.txt` | 43 | 29/08/2026 03:58:36 -03:00 |
| `servidor.py` | 10.631 | 29/08/2026 03:58:36 -03:00 |

O `Procfile` inicia `app:app`. `banco.py` chama as RPCs `otimizador_regua_v2`, `otimizador_carta_v3` e `otimizador_pool_habilidades_v3`; nenhuma das seis views aposentadas é consumida pelo serviço.

## 3. Cadeia real do `index.html` antigo

O arquivo auditado foi `1-SISTEMA/index.html`, com 26.386 bytes, 372 linhas e SHA-256 `2CA0A42E75FF035ADA4479438A989FA50ECEB6B9D3C83A90D55DEB3F6E4B62EC`.

Ele carrega três CSS e onze JavaScripts executáveis:

| Arquivo | Bytes | Linhas | SHA-256 |
|---|---:|---:|---|
| `clubefut.css` | 272.653 | 4.285 | `63F4F9B465DB925BFAAE3A3A0D80C2FA87C581F06E64B7E5C589E38FD58E4175` |
| `ficha-aprovada.css` | 32.538 | 567 | `47A0F98C313D57E1FA80F126BF36C450A5CD1B17B4A7DA61DDDB9D5F9811553C` |
| `como-funciona.css` | 9.448 | 93 | `7B32C1F6A698661F8C5E1FE09976D40744B6F5B8CCA4F3065AA0BA92035D2C6E` |
| `dados-e-catalogos.js` | 1.578.981 | 232 | `18609D275DD0D47CBBE018B98197180EBFE2D57D5767BC8AFDF9DB1CF70CE1A2` |
| `clube-novo-read-model.js` | 56.057 | 1.331 | `2CBF62EE1F41DC20065A447296A9F55071E9C9520D867A581764915BEB40495E` |
| `user-state-repository.js` | 19.015 | 364 | `37267813A19DD2B64DF301BBFFB9676B1C8B3618C266CE0F771C7BE551268605` |
| `motor-e-ficha-base.js` | 758.639 | 4.354 | `500D665EFEEC206EA86D2D348FF3F04880C93C5FE9EE19686787F453C086EC83` |
| `elenco.js` | 245.056 | 4.915 | `6E2D8F58AB4A4B88DCBB25C5B1840271B9B4951B879B57990DABF56D623CADCD` |
| `ficha-ajustes.js` | 175.161 | 3.499 | `DC20BE4772ECB0475580DFE59BD6FA21BF89F93E64552344B8CD82DEA669C807` |
| `ficha-cadastral-view.js` | 11.104 | 118 | `C9697278C946A072E9D65C7753126BA324DD913A71EB1EF45293351C2FFA2A6B` |
| `modulos-elenco-paginas.js` | 89.020 | 746 | `53981AADB78AD1EEDCABDCCF1CF295EBFE9A3FFC61446E505B3E45EB6F6B9E3B` |
| `como-funciona.js` | 7.966 | 147 | `EE2429124B3A6991B86497D32F4DD9B01473919984A0E6B02A0E0E95F6248D60` |
| `paginas-e-navegacao.js` | 42.696 | 749 | `84ADB497954DC083C7B72F5C87E1CFB4F23FB5C353BBB6947F79A457CC17BCAA` |
| `arows-sob-demanda.js` | 6.419 | 162 | `6FEFC8F374F71BCE3C17DACC37E49FBAE4910E28D054AC510A0A5182E5DD1123` |

Não foi encontrada carga dinâmica de outro JavaScript, worker ou HTML. O único recurso externo adicional dos CSS é a fonte Carlito do Google Fonts; os demais `url(...)` identificados são dados embutidos.

## 4. Prova de consumo

`1-SISTEMA/clube-novo-read-model.js` define a base `https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/` e estes recursos:

| Método exposto | Recurso HTTP | Chamador executável provado |
|---|---|---|
| `boxes()` | view `frontend_boxes_v1` | `ficha-ajustes.js:313` |
| `home()` | view `frontend_home_v1` | `paginas-e-navegacao.js:555` |
| `busca()` | view `frontend_busca_v1` | `paginas-e-navegacao.js:670` |
| `ficha()` / `carta()` | view `frontend_ficha_v1` | `ficha-cadastral-view.js:111` e `ficha-ajustes.js:1409` |
| `fichaBuild()` | view `frontend_ficha_build_v1` | `ficha-ajustes.js:1415` |
| `listar()` / `card()` | RPC `frontend_build_publicada_v2` | `motor-e-ficha-base.js:101,181`, `ficha-ajustes.js:1410` e `arows-sob-demanda.js:51` |

O catálogo vivo confirmou que os cinco primeiros nomes eram views em `public` e que `public.frontend_build_publicada_v2(...)` era função, não view. Por isso a RPC ficou fora do escopo destrutivo.

## 5. Dependências que determinaram a ordem

- `frontend_boxes_v1`, `frontend_home_v1` e `frontend_busca_v1` não tinham views dependentes.
- `frontend_ficha_build_v1` dependia de `frontend_ficha_v1`.
- `frontend_ficha_builds_v1` dependia de `frontend_ficha_v1`, `frontend_ficha_build_v1` e `clube_novo.funcao_sistema`.
- `frontend_ficha_builds_v1` não tinha dependentes.
- Busca repo-wide: nenhum código executável do Site Novo ou do serviço atual consumia `frontend_ficha_builds_v1`; os únicos registros estavam em inventário/documentação.

A segunda ordem de remoção foi, portanto: `frontend_ficha_builds_v1`, `frontend_ficha_build_v1`, `frontend_ficha_v1`.

## 6. Recuperação capturada antes das remoções

Os arquivos abaixo contêm as definições obtidas com `pg_get_viewdef`, opções, comentários, owners e grants de restauração. Eles foram gravados antes de cada migração e não foram executados:

| Arquivo | Views | Bytes | SHA-256 |
|---|---:|---:|---|
| `RECUPERACAO-VIEWS-SITE-ANTIGO-2026-09-04.sql` | 3 | 12.148 | `BFCC49844961620306EAA711E29F937198A1D92105F2A6DF75E9EAA8E6FE555F` |
| `RECUPERACAO-VIEWS-FICHA-SITE-ANTIGO-2026-09-04.sql` | 3 | 15.439 | `FFD5E1D7D8EDDD98BAF46E13B098B0C5BC1AE134F069DBF2D980611F2E406957` |

## 7. Migrações aplicadas

| Versão | Migração | Resultado |
|---|---|---|
| `20260904210738` | `aposentar_views_site_antigo_20260904` | removeu Boxes, Home e Busca |
| `20260904211109` | `aposentar_views_ficha_site_antigo_20260904` | removeu lista da Ficha, Ficha-Build e Ficha |

As duas migrações:

- verificaram previamente que cada alvo ainda era uma view;
- abortariam diante de dependente fora do conjunto autorizado;
- usaram nomes qualificados;
- fizeram `DROP VIEW` explícito;
- não usaram `CASCADE`.

## 8. Readback final do banco

O catálogo retornou `ABSENT` para os seis nomes aposentados, em qualquer schema não sistêmico e tanto para view como para materialized view.

Tabelas e dados permaneceram presentes. Contagens lidas depois das migrações:

| Tabela | Linhas |
|---|---:|
| `clube_novo.carta_jogo` | 43.448 |
| `clube_novo.carta_playstyle_jogo` | 86.144 |
| `clube_novo.carta_posicao_principal_jogo` | 43.072 |
| `clube_novo.playstyle` | 36 |
| `clube_novo.posicao_jogo` | 13 |
| `clube_novo.tipo_carta_jogo` | 11 |
| `clube_novo.build_linha_card` | 224.602 |
| `clube_novo.build_otimizador` | 57.950 |
| `clube_novo.build_bonificador` | 57.950 |

Na primeira leitura, `carta_jogo` tinha 43.072 linhas e, no readback final, 43.448. O crescimento de 376 linhas ocorreu durante a janela de auditoria por atividade concorrente; não houve redução causada pelas migrações. As demais tabelas comparáveis mantiveram as contagens.

Os advisors de segurança e desempenho foram relidos após a segunda migração e não mencionaram nenhuma das views aposentadas. Avisos preexistentes e não relacionados ficaram fora deste escopo.

## 9. Funções preservadas e inventário de possível obsolescência

Nada desta lista foi removido:

| Função | Estado depois da aposentadoria | Decisão |
|---|---|---|
| `public.frontend_build_publicada_v2(text,bigint,integer,integer)` | RPC diretamente consumida pelo site antigo; continua existente, `SECURITY DEFINER`, owner `postgres`, sem consumidor do Site Novo/serviço provado nesta auditoria | candidata a aposentadoria separada; exige autorização específica |
| `clube_novo.frontend_normalizar_texto_v1(text)` | helper da view de Busca removida; catálogo atual não encontrou outra view ou rotina que a mencione | provavelmente órfã; exige autorização específica |
| `public.fn_pts_regua(numeric,integer,numeric)` | era chamada por Ficha-Build; ainda é mencionada por `public.fn_pts_regua_b(...)` | não classificada como órfã; preservada |

## 10. Limites

- Nenhum arquivo do site antigo foi alterado.
- Nenhuma implementação funcional ou alteração visual do Site Novo foi feita.
- Os arquivos de inventário/checkpoint datados foram preservados como evidência histórica.
- O Site Novo não herdará automaticamente nenhum dos contratos aposentados nem a RPC preservada; seu contrato público continua a ser definido e aprovado separadamente.
