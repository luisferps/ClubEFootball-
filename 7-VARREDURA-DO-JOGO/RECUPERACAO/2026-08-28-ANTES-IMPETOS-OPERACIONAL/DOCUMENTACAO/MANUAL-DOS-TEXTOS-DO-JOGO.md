# Manual dos Textos do Jogo

## Finalidade

`clube_novo.texto_do_jogo` é o dicionário canônico dos textos oficiais exibidos pelo jogo. Catálogos devem guardar a chave oficial do texto e obter nome, sigla ou rótulo por junção com esse dicionário. Não se deve copiar uma string para outro catálogo como se ela fosse identidade.

## Fonte e chave

A fonte portuguesa é `all.str`, armazenada em `dt261_bra_console_win.cpk`. A chave oficial é o par `(secao,id_texto)`. `idioma='pt-BR'` descreve o conteúdo, mas não substitui nem amplia a chave.

Fonte provada em 27 de agosto de 2026:

| Objeto | Tamanho | SHA-256 |
|---|---:|---|
| `dt261_bra_console_win.cpk` | 258.498 bytes | `2419045a081a151f8a0cdcc70a9ca0c4ca1ca265b8467b9c182623baa05338db` |
| `all.str` descompactado | 783.360 bytes | `306741adab8376ed64620b618ae9721d316ae548b126419730b9bd5ff5f525a9` |

## Estrutura física comprovada

- byte 0: quantidade de seções (`u32`);
- byte 4: início da tabela de seções (`u32`);
- cada cabeçalho de seção tem 12 bytes, na ordem `secao_offset`, `secao_tamanho`, `nome_offset`;
- cada seção começa com cabeçalho de 8 bytes;
- cada entrada tem 12 bytes: `id_texto` (`u32`), tamanho armazenado (`u16`), tamanho visível (`u16`) e offset relativo do texto (`u32`);
- `texto_offset = secao_offset + offset_relativo`.

O parser valida todos os limites antes de aceitar uma entrada. A prova atual contém 188 seções, 11.679 chaves únicas, zero duplicidade, 509 valores vazios e 11.170 valores não vazios.

Esses números descrevem a fonte selada de 27 de agosto; não são uma trava de versão. Em uma atualização futura, o Extrator aceita outra contagem quando o parser comprovar limites, chaves únicas, proveniência, offsets e um único par de fingerprints do CPK/`all.str`. Contagem diferente, sozinha, é mudança a comparar — não erro estrutural.

## Contrato de `clube_novo.texto_do_jogo`

A tabela já existe. A migração preparada preserva a PK `(secao,id_texto)` e acrescenta apenas proveniência fisicamente comprovada:

| Campo | Papel |
|---|---|
| `secao`, `id_texto` | chave oficial |
| `texto`, `idioma` | conteúdo localizado |
| `arquivo`, `cpk`, `origem` | procedência lógica |
| `secao_idx`, `secao_offset` | posição da seção |
| `entrada_idx`, `entrada_offset` | posição da entrada |
| `texto_offset` | posição do conteúdo |
| `tamanho_armazenado`, `tamanho_visivel` | larguras gravadas na entrada |
| `fonte_cpk_sha256`, `fonte_arquivo_sha256` | identidade da fonte |
| `presente_na_fonte`, `extraido_em` | estado e instante da extração |

Não foram inventados bits, largura ou endereço quando o arquivo não os fornece. O conteúdo vazio é preservado porque uma chave oficial vazia continua sendo uma entrada real.

## Seções atuais e rótulos históricos

O arquivo físico atual é autoridade. Entre as seções relevantes comprovadas estão:

| Seção física atual | Linhas | Índice | Rótulo histórico correspondente |
|---|---:|---:|---|
| `E15W` | 110 | 33 | `E13W` |
| `E5W` | 35 | 43 | `E5T` |
| `E6W` | 19 | 45 | `E6T` |
| `Any3W` | 951 | 15 | `Any3T` |
| `Any2W` | 639 | 13 | `Any2T` |
| `Po1C` | 30 | 157 | `PlayC` |

Há ainda relocações comprovadas `Amg1T→Amg1W`, `Any1T→Any1W`, `Lcm2W→Lcm4W` e `T2T→T2W`. Rótulos antigos servem apenas para reconciliar a fotografia anterior; nunca são usados para inferir uma chave nova.

Quando a chave histórica exata existe na fonte física atual, ela tem prioridade. A relocação conhecida só é usada se a chave exata estiver ausente e o destino mapeado existir. Se uma única coluna de seção de catálogo exigisse simultaneamente dois destinos diferentes, o lote é bloqueado como cardinalidade incompatível.

## Catálogos ligados ao dicionário

Os catálogos `atributo_jogo`, `estilo_ia`, `habilidade_jogo`, `impeto_jogo`, `pe` e `playstyle` possuem uma referência `(secao_texto,id_texto)`. `posicao_jogo` possui duas referências explícitas: uma para a sigla e outra para o nome. A migração prepara FKs compostas diretas para `texto_do_jogo(secao,id_texto)`; não cria tabela auxiliar.

As FKs foram instaladas primeiro de forma protegida e, depois da carga integral e do
readback com zero referência ausente, as oito foram validadas. Cada uma possui um
índice composto parcial correspondente no próprio schema `clube_novo`.

## Fluxo automático no Extrator

Ao abrir o Extrator eFootball:

1. o aplicativo localiza `dt261_bra_console_win.cpk` no caminho conhecido;
2. extrai e valida `all.str`;
3. lê `clube_novo.texto_do_jogo` em transação somente leitura;
4. compara por `(secao,id_texto)` e mostra o resumo junto aos metadados;
5. conserva o pacote integral selado e revisável;
6. não escreve nada automaticamente.

Na primeira carga, o resumo foi 11.468 chaves novas, 211 atualizadas e zero remoções
sem substituição. Depois da aplicação confirmada em 28/08/2026, a mesma fonte deve
aparecer como **Tudo atualizado**, com as 11.679 chaves conferidas. A interface mostra
no máximo 250 linhas para permanecer responsiva, mas o manifesto preserva o conjunto integral.

## Aplicação manual e proteções

O botão de preparação aceita somente o pacote integral que o próprio Extrator acabou de gerar. Não existe seletor de CSV ou JSON. O executor:

- fixa o alvo em `clube_novo.texto_do_jogo`;
- rejeita pacote parcial, adulterado, obsoleto ou com chave duplicada;
- verifica o contrato estrutural antes do pré-voo;
- exige que a linha anterior ainda exista e conserve o texto usado para gerar o diff; desaparecimento ou alteração concorrente bloqueia tanto atualizações na mesma chave quanto relocações de seção;
- prova que todas as referências de catálogos continuarão resolvidas;
- bloqueia ausência, seção ambígua ou troca não comprovada;
- mostra imediatamente `Preparando`, `Pronto`, `Bloqueado` ou `Sem mudanças`;
- exige confirmação final e identificador idempotente;
- usa transação e readback;
- envia os registros em upserts idempotentes de até 500 linhas, dentro da mesma transação;
- não reenvia ao `UPSERT` uma chave que o pré-voo já classificou como integralmente aplicada;
- grava manifesto de aplicação e dados de recuperação.

Um duplo clique reutiliza ou rejeita o mesmo `request_id`; não reaplica o lote. `clube` nunca é destino.

## Recuperação

Antes do commit, qualquer divergência encerra a transação sem alteração. Depois de um commit, o manifesto conserva o estado anterior das linhas substituídas, as seções antigas reconciliadas e os hashes do pacote. O rollback preparado remove as constraints e colunas desta migração sem tocar no schema legado; a reversão de dados só deve ser executada com o manifesto específico da aplicação.

## Estado desta entrega

- extração física: concluída e validada;
- integração automática no aplicativo: instalada e validada;
- migração estrutural: aplicada exclusivamente em `clube_novo`;
- carga no banco: 11.679 textos oficiais aplicados manualmente;
- readback: 11.679 chaves únicas, zero duplicidade e 11.679 procedências confirmadas;
- referências: 166 resolvidas, zero sem texto e oito FKs validadas;
- fingerprint do readback: `56a205221af16addfe96f8452baffa8a`;
- `clube` e `public`: intocados por esta frente.

Em 28 de agosto de 2026, a validação local foi tornada autocontida: o teste físico passou a usar o manifesto selado guardado nesta própria frente, sem depender de outra pasta de tarefa. Foram acrescentados 17 testes do executor e das migrações, incluindo contrato estrutural ausente, chave histórica alterada, linha original desaparecida, mudança legítima de contagem, prioridade da chave física exata, conflito de seção compartilhada, identidade adulterada, pacote com duas versões físicas, referência de catálogo não resolvida, idempotência sem `UPSERT` redundante, readback/rollback simulados e restrição integral dos SQLs ao schema `clube_novo`. Todos passaram sem escrita no banco.

O executor operacional lê `clube_novo.texto_do_jogo` em transação somente leitura e
confirmou 11.679 registros, 11.679 chaves únicas e zero duplicidade após a instalação.

## Lacunas explícitas

- A semântica completa de todas as 188 seções não foi inferida. Isso não impede a carga do dicionário, mas impede atribuir função a uma seção sem prova.
- Catálogos futuros de técnicos e Link-up não foram modelados nesta frente.
- Consumidores de tela ainda precisam migrar suas consultas para as FKs centrais; nenhum nome embutido foi removido fora do Extrator nesta tarefa.
