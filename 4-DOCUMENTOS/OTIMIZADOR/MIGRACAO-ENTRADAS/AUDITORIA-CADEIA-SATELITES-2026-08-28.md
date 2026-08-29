# Auditoria factual da cadeia satélite do Otimizador

Data: 28/08/2026. Escopo: somente leitura. Nenhuma fórmula, peso, regra de
negócio, dado do jogo, banco ou arquivo executável foi modificado por esta auditoria.

## Critério

Um elo está **verde** somente quando recebe e relaciona os insumos de cálculo por
`card_id`, `funcao_id`, `skill_id`, `tecnico_id`, ID de posição ou código/bit físico
do atributo. Nome e rótulo podem atravessar o elo apenas como apresentação. A
compatibilidade para a saída histórica é anotada separadamente: não a confundi com
uma entrada nova do Otimizador.

## Grafo efetivamente alcançável

```text
RODAR-O-MOTOR.bat / RODAR-TUDO.bat
  -> 2-MOTORES/OTIMIZADOR/roda_lote_v6.py
     -> fonte_unica.py -> public.otimizador_{carta,cartas,regua,pool_habilidades,
                             proxima_fila,peso_ordem}_v1
     -> equacao.py + regua.py + motor.py + travas.py
     -> fonte_unica.gravar() -> public.gravar_build [saída histórica]
     -> grava_direto.py [importado; sem payload nesta rota]

Procfile: gunicorn app:app
  -> 6-AVALIADOR-NO-RAILWAY/app.py
     -> banco.py -> mesmas RPCs v1
     -> monta_regua.py -> regua_do_banco.py
     -> avaliador.py + otimizador.py

1-SISTEMA/index.html
  -> dados-e-catalogos.js -> motor-e-ficha-base.js -> elenco.js -> ficha-ajustes.js
     -> modulos-elenco-paginas.js -> ... -> arows-sob-demanda.js
     -> public.casa_lista/casa_arows/bonus_posicao [projeções públicas históricas]
```

`SITE-ATUALIZADO-2026-08-24/ClubEfootball-DATA-BOXES-CORRIGIDA-CARDS-LARGOS.html`
carrega a mesma família de scripts da tela. `TELA-CLUBEFOOTBALL-UNICA.html` contém
uma cópia embutida. São réplicas a auditar, não portas autorizadas para `clube_novo`.

## Matriz de elos

| elo e acionamento | recebe | entrega/consome | origem/linguagem | estado factual |
|---|---|---|---|---|
| `RODAR-O-MOTOR.bat`, `RODAR-TUDO.bat` | `PARAR_EM`, `config.txt` | inicia `roda_lote_v6.py` | lançador local | **verde** para entradas: não escolhe carta/função nem lê catálogo; o lote produtivo não foi acionado nesta auditoria |
| `OTIMIZADOR/roda_lote_v6.py` | fila `{card_id, funcao_id, prioridade, overall}` | carta, molde, pool e resultado com IDs; chama `gravar` | Python; `otimizador_*_v1` via `fonte_unica` | **verde na entrada**. `funcao_codigo_compat` e nomes são apenas log/saída. Fila continua sendo estado operacional histórico, mas sua fronteira devolve `funcao_id` |
| `OTIMIZADOR/fonte_unica.py` | JSON das RPCs v1 | estrutura interna indexada por posição/`skill_id`/`tecnico_id` | Python + RPC privada por `service_role` | **verde na entrada**: sem arquivo/HTML/RPC antiga como fallback. Os blocos `apresentacao` e `compatibilidade_legado` não são lidos pelo cálculo. Exceção de saída: `gravar()` traduz `funcao_id` para `funcao_codigo` e chama `gravar_build` |
| `OTIMIZADOR/equacao.py` | índices 0–25, `skill_id`, multiplicador e boosts já normalizados | valores calculados | Python | **verde para identidade externa**. `ATTRS_EF`, grupos de barras e degraus são constantes matemáticas internas, não busca por rótulo recebido; não foram alterados |
| `regua.py` | vetor de índices e linhas `(índice, alvo, peso)` | nota | Python | **verde**: não abre banco/arquivo nem resolve textos |
| `OTIMIZADOR/motor.py` | `skill_id`, `tecnico_id`, índices e matriz de molde por `funcao_id` | build e textos de apresentação | Python | **verde na entrada**. Nome de técnico/ímpeto aparece apenas no resultado. Catálogo de ímpetos fabricáveis recebido é vazio por gate; nenhuma regra condicional foi ligada |
| `travas.py` | `gate.pode_rodar`, cardinalidades e motivos | recusa explícita | Python | **verde**: carta incompleta ou com ímpeto equipado não entra; não há fallback |
| `grava_direto.py` | linhas históricas, se outro chamador invocar `junta()` e o interruptor local existir | REST direto em `builds`, chave `(card_id, funcao)` textual | Python; satélite importado pelo lote | **amarelo/inativo nesta rota**. `roda_lote_v6.py` só chama `descarrega()` no fim e não chama `junta()`. Não é fonte de entrada, mas conserva um escritor legado alternativo que deve permanecer fora de qualquer caminho novo |
| `public.gravar_build` pela `fonte_unica.gravar()` | resultado com `card_id`, convertido para `funcao_codigo` | `clube.build` e remoção da fila | RPC de **saída histórica** | **amarelo deliberado**: não influencia o cálculo nem alimenta o lote migrado. Não há substituto de saída autorizado em `clube_novo`; trocar isto exige decisão própria, não inferência |
| `CONFERIR-UMA-LINHA.bat` -> `OTIMIZADOR/conferir_uma.py` | `card_id`, `funcao_id` | conferência local | Python/manual | **verde**: lê `fonte_unica`, `equacao`, `motor` e `regua`; não usa fonte antiga |
| `app.py` (único entrypoint do `Procfile`) | HTTP `{card_id, funcao_id, barras, skill_ids, tecnico_id}` | `/avaliar`, `/otimizar` | Flask | **verde na cópia local**: recusa IDs inválidos, ímpetos e carta sem gate; usa somente `banco.py`/v1. A implantação efetivamente publicada ainda precisa ser identificada antes de qualquer alegação sobre a internet |
| `banco.py` | IDs canônicos | `otimizador_regua_v1`, `otimizador_carta_v1`, `otimizador_pool_habilidades_v1` | Python + RPC privada | **verde**: não consulta tabela, view ou RPC antiga |
| `monta_regua.py`, `regua_do_banco.py` | JSON v1: `funcao_id`, `skill_id`, `tecnico_id`, índice físico | estruturas de régua por ID | Python | **verde**. Textos são guardados apenas para resposta/diagnóstico |
| `avaliador.py`, `otimizador.py` | vetores, barras e molde já indexados | nota/valores/barras | Python | **verde para fontes**: não têm I/O. Fórmula e pesos foram preservados e estão sob teste de trava |
| `servidor.py` | quando importado, `{card_id, funcao_id, skill_ids, tecnico_id}` | rotas `/nota` e `/otimizar` | Flask auxiliar | **cinza/órfão**: o `Procfile` sobe `app:app`; `app.py` não importa `servidor.py`. Não é rota ativa da cópia operacional. Não deve ser usado como prova da implantação |
| `1-SISTEMA/index.html` e oito scripts carregados | dados públicos e estado local | tela, ficha, build local | JavaScript | **vermelho para migração de entradas**: a cadeia ativa inclui `motor-e-ficha-base.js`, `ficha-ajustes.js` e `arows-sob-demanda.js`, que consultam `casa_lista`, `casa_arows`, `bonus_posicao` e/ou catálogos embutidos; não recebem contrato v1 por IDs |
| `1-SISTEMA/motor-e-ficha-base.js` | linhas da projeção pública e `CAT`/funções embutidos por texto | calcula build no navegador | JavaScript | **vermelho**: usa `casa_lista`, rótulos e catálogo hard-coded de ímpetos. É cálculo replicado, não simples apresentação. Não foi modificado devido à trava de fórmula |
| `ficha-ajustes.js`, `dados-e-catalogos.js`, `elenco.js`, `modulos-elenco-paginas.js` | projeções públicas, estado e rótulos | ficha/ranking/elenco | JavaScript | **vermelho/amarelo**: componentes ativos da mesma tela; mantêm formato histórico de build/função. Alguns só apresentam, mas a cadeia não carrega IDs suficientes para provar identidade sem tradução nova |
| `arows-sob-demanda.js` | `public.casa_arows` por REST público | `arows`/pool da ficha | JavaScript | **vermelho**: satélite de entrada tardia da UI, ainda em contrato público legado |
| cópias `SITE-ATUALIZADO-2026-08-24/motor-e-ficha-base.js` e HTML único | mesmas estruturas embutidas | tela publicada/fotografia | JavaScript/HTML | **vermelho**: são réplicas independentes, não derivadas em tempo de execução da cópia de `1-SISTEMA`; exigem teste de paridade individual |
| `motor-no-servidor.js` | `funcao` por código textual, nomes de técnico/ímpeto e habilidades da tela | chama `/nota` e `/otimizar` Railway | JavaScript | **cinza/incompatível**: não é referenciado pelo `index.html` nem pelo HTML publicado. Mesmo se fosse carregado, o payload não satisfaz o `app.py` ativo (`funcao_id`, `skill_ids`, `tecnico_id`) e o `Procfile` não registra `/nota` |
| `funcao_nativa.py`, `regras_do_card.py` | posição/estilo e catálogos próprios | mapeamentos auxiliares | Python | **cinza/órfão**: nenhuma importação/chamada alcançável a partir dos lançadores do lote ou do `Procfile`; não foram tratados como fallback ativo |
| `BONIFICADOR/motor_bonus.py` | própria cadeia de bônus e saída `gravar_bonus` | bônus publicado | Python | **fora da cadeia do Otimizador**: não é importado por lote, serviço nem lançadores. Seu contrato foi auditado separadamente; nada aqui autoriza misturá-lo ao Otimizador |

## Contrato v1 e gates que a cadeia verde respeita

As RPCs `otimizador_carta_v1`, `otimizador_cartas_v1`, `otimizador_regua_v1`,
`otimizador_pool_habilidades_v1`, `otimizador_proxima_fila_v1` e
`otimizador_peso_ordem_v1` usam `SECURITY DEFINER`, `search_path=''` e são de
`service_role`. As entradas trazem IDs/FKs e os gates de 26 atributos, 12 corpo,
12 posições, pé, playstyles, habilidades, dimensões e tipos. Ímpetos retornam
desligados; uma carta com ímpeto equipado fica recusada. A tabela `clube.molde`
permanece regra operacional: a ponte usa `codigo_legado` único somente para chegar
a `funcao_id`; o consumidor recebe o ID e os 494 pares de alvo/peso intactos.

## Plano de paridade por elo — obrigatório antes de qualquer hunk

1. **Congelar a fotografia atual.** Criar snapshot/patch e hashes dos arquivos que
   forem efetivamente tocados. O teste de trava deve continuar comparando AST das
   fórmulas e bytes das três réplicas; um diff fora dos adaptadores de dados reprova.
2. **Contrato de sombra da UI.** Sem expor `clube_novo`, criar/identificar um único
   endpoint de serviço implantado que aceite e devolva IDs: `card_id`, `funcao_id`,
   `tecnico_id`, `skill_ids`, barras e gate. O payload não pode aceitar rótulo de
   função, nome de técnico ou nome de ímpeto como chave. Antes do corte, registrar
   por carta/função a origem antiga, origem v1, cardinalidade, fingerprint e valor.
3. **Traduzir somente na borda histórica.** Para builds e linhas públicas antigas,
   o adaptador de comparação deve obter `funcao_id` pela ponte canônica já provada;
   não deduzir por texto. Habilidade e técnico precisam chegar em IDs persistidos;
   se a projeção histórica não os contém, o caso fica bloqueado em vez de adivinhado.
4. **Migrar cada réplica separadamente.** `1-SISTEMA`, a cópia em
   `SITE-ATUALIZADO-2026-08-24` e o HTML único só podem mudar depois de cada uma
   produzir a mesma entrada lógica e a mesma saída para amostras gate-abertas.
   Cobrir Messi, Capello, Conte, uma carta sem ímpeto e uma carta recusada.
5. **Manter ímpetos e saída histórica fechados.** Nenhuma rota de UI ativa ímpetos,
   condições ou faixas antes dos gates próprios. `gravar_build`/`clube.build` não
   muda nesta frente sem uma autorização explícita para migração de saída; ele não
   pode virar entrada do contrato v1. `grava_direto.py` deve continuar fora do fluxo.
6. **Readback e rollback.** Para cada troca: negar fallback, salvar o payload
   auditado, comparar fingerprints/cardinalidades, testar renomeação de rótulos e
   restaurar apenas o hunk de adaptador se houver diferença. Não executar lote nem
   publicar enquanto algum elo vermelho permanecer.

## Veredito

O objetivo estrito “todos os arquivos ativos da cadeia usam o mesmo contrato novo”
está atendido para **lote local + cópia local do serviço**, mas **não** para a UI.
O bloqueio é factual e específico: a tela ativa lê projeções públicas/embutidas e o
endpoint Railway efetivamente implantado não foi provado. Não é seguro trocar esses
elos apenas pelo nome, nem permitir acesso direto da UI ao schema privado.
