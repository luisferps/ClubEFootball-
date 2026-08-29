# Manual do Extrator eFootball

**Versão:** 4.6 · 29 de agosto de 2026  
**Estado da entrega:** leitura física cumulativa, comparação automática, escrita manual reabilitada e aplicação segura de dimensões/vínculos antes dos cards  
**Pasta operacional:** `Clubefootball V4\7-VARREDURA-DO-JOGO`

## 1. Finalidade

O Extrator eFootball é a primeira etapa do pipeline produtivo do ClubEFootball V4. Ele lê diretamente os arquivos físicos instalados pela Konami, transforma os registros no contrato interno do sistema e compara o estado físico atual com `clube_novo`.

A ordem do sistema é obrigatória:

```text
EXTRATOR -> OTIMIZADOR -> BONIFICADOR
```

Dentro do Extrator, a ordem produtiva também é obrigatória:

```text
METADADOS / CATÁLOGOS
        ↓
VÍNCULOS FÍSICOS DOS CARDS
        ↓
CARDS NOVOS / ALTERADOS
        ↓
READBACK
```

Nenhum motor deve receber card com insumo obrigatório faltando por falha de coleta. Ausência legítima no próprio jogo é diferente de ausência causada por coleta incompleta.

## 2. Escopo atual e regra de versão

A pasta `7-VARREDURA-DO-JOGO` do ClubEFootball V4 é a implementação atual do Extrator. Fluxos anteriores existentes no repositório são legado e servem apenas como consulta histórica ou recuperação.

A V4.6 estende a V4.5 sem reaproveitar o extrator legado. O mapa físico comprovado continua em `app\mapeamento-fisico.js`; a leitura operacional fica em `app\extrator-core.js`; o acesso ao banco continua concentrado no executor Python local.

A escrita nunca é feita pelo navegador diretamente. O navegador não recebe senha, connection string nem credencial privilegiada.

## 3. Fontes físicas

O Extrator trabalha por família de dados. Um CPK não substitui genericamente outro.

| Fonte | Papel atual |
|---|---|
| DT870 da atualização | cartas atuais, relações, dimensões, técnicos, nacionalidades, ímpetos atuais, habilidades e overlay de playstyles |
| DT200 base | semântica de playstyles e ímpetos legados ainda válidos |
| DT870 original | ímpetos legados exclusivos e conferência histórica |
| `dt261_bra` | `all.str` e textos oficiais em português |

Arquivos físicos já integrados ao contrato incluem `Player.bin`, `PlayerVariationDetail.bin`, `PlayerAppearance.bin`, `PlayerSkill.bin`, `PlayerBooster.bin`, `Playstyle.bin`, `Coach.bin`, `Country.bin`, `Team.bin`, `CompetitionUnit.bin`, `CompetitionEntry.bin`, `PlayerDeleteList.bin` e `all.str`.

A regra permanece: endereço, tamanho, fingerprint ou estrutura incompatível bloqueia a família. O Extrator não completa lacunas com dado antigo e não inventa significado para bytes sem prova.

## 4. Como iniciar a V4.6

Enquanto o executável ainda não tiver sido reconstruído localmente, use:

`INICIAR-EXTRATOR-V46.cmd`

O fonte do lançador Windows já foi atualizado para a versão 4.6 e aponta para `executor\servidor_v46.py`. Para reconstruir o executável no próprio Windows existe:

`COMPILAR-EXTRATOR-V46.cmd`

Esse comando usa `windows-app\COMPILAR-APLICATIVO.ps1` e o compilador .NET Framework do Windows. O `Extrator eFootball.exe` só passa a representar a V4.6 depois dessa compilação terminar com sucesso. Até lá, o EXE anterior deve ser tratado como binário preservado da V4.5.

Ao iniciar a V4.6:

1. o servidor local abre somente em `127.0.0.1`;
2. as fontes conhecidas são localizadas;
3. a comparação de cards começa quando a fonte atual e o banco estão disponíveis;
4. a comparação de metadados relê as famílias físicas;
5. o painel adicional **Etapa 1 · Metadados antes dos cards** fica aguardando a fotografia de dimensões;
6. nenhuma gravação ocorre sem ação manual.

## 5. Metadados e dimensões — regra V4.6

A V4.6 fecha a lacuna que existia entre **ler/validar** e **gravar** nacionalidade, clube, liga, tipo de carta e os vínculos físicos desses dados com cada card.

O contrato físico utilizado é `clubef-card-dimensions-physical-v2`.

### 5.1 Dados lidos por card

A fotografia física contém, entre outros:

- código bruto e código resolvido de nacionalidade;
- código de clube;
- código de liga/competição;
- tipo físico da carta;
- subtipo físico;
- estado de jogador indisponível;
- chave/tipo canônico da carta;
- prova da fonte, arquivo e hash do `Player.bin`;
- estado `pode_rodar_vinculos` e motivo de bloqueio quando a prova física é insuficiente.

### 5.2 Catálogos envolvidos

Antes de tocar nos vínculos dos cards, o executor aplica/atualiza:

- nacionalidades;
- clubes;
- ligas;
- tipos de carta já conhecidos pelo contrato canônico.

Tipos de carta fisicamente novos não são inseridos automaticamente sem prova nominal/canônica suficiente. Mudança na chave canônica de um tipo já existente também é bloqueada e exige migração própria, porque há cards protegidos por FK apontando para essa chave.

### 5.3 Ordem de escrita

A aplicação de dimensões usa uma única transação e segue esta ordem:

1. validar a fotografia física;
2. travar a execução concorrente;
3. atualizar/inserir nacionalidades;
4. atualizar/inserir clubes;
5. atualizar/inserir ligas;
6. atualizar tipos de carta já canônicos, sem alterar chave canônica referenciada;
7. somente depois atualizar os vínculos dos cards existentes;
8. commit;
9. abrir nova conexão somente leitura;
10. executar readback integral contra a mesma fotografia física.

Nenhum catálogo ou vínculo ausente da fonte é apagado automaticamente.

### 5.4 Cards novos ainda inexistentes no banco

Metadados vêm primeiro. Portanto uma carta completamente nova pode aparecer na fotografia física antes de existir na tabela de cards.

Nesse caso:

- os catálogos são aplicados normalmente;
- o vínculo dessa carta é marcado como `pending_card_insert` na execução;
- a carta é inserida na etapa de cards;
- uma nova reconciliação de dimensões deve ocorrer depois da inserção para preencher o vínculo físico daquela carta.

Isso não autoriza o Otimizador a rodar um card pendente. O gate continua fechado até a reconciliação terminar.

## 6. Estado físico validado em 28/08/2026

A fotografia cumulativa validada encontrou:

- 43.072 cards únicos;
- 214 nacionalidades;
- 1.072 clubes;
- 75 ligas;
- 11 tipos de carta.

No estado auditado, todas as cartas possuem nacionalidade e tipo físicos resolvidos. Clube e liga só são preenchidos quando a relação existe/prova no jogo. A ausência não deve ser preenchida artificialmente.

Existiam 354 bloqueios factuais ligados a código de clube sem definição física/nominal comprovada. Esses casos permanecem identificados e bloqueados; a V4.6 não os transforma em valor inventado.

## 7. Ímpetos

Ímpetos são lidos dentro do Extrator atual a partir dos arquivos do próprio jogo. Eles não dependem do fluxo antigo de site externo.

A união física validada contém 440 IDs. O Extrator preserva registros que aparecem apenas em fontes físicas legadas quando a prova por fingerprint é válida.

O contrato físico também relê:

- os dois slots do card;
- estado de vaga;
- efeitos;
- tipo/condição raw;
- alvos por nacionalidade, liga e clube;
- faixas e classes condicionais;
- vínculos de competição necessários às condições.

A leitura/validação de ímpetos está no V4. A existência de um bloqueio posterior chamado "consumidor de ímpetos" pertence ao Otimizador, não ao Extrator.

## 8. Boxes/coleções

A relação física de card com box/coleção vem do `PlayerVariationDetail.bin` e faz parte do contrato de leitura do card. O fluxo atual não usa o coletor antigo de site como fonte oficial.

## 9. Técnicos

O `Coach.bin` atual fornece técnicos, cinco proficiências históricas, Sobreposição quando fisicamente presente, até dois boosts, idade, nacionalidade e afinidade.

A referência validada possui 1.478 técnicos. Link-up permanece fora do contrato quando a semântica/cardinalidade não estiver integralmente comprovada; isso não autoriza inferência.

## 10. Textos oficiais

Textos vêm exclusivamente de `all.str` no `dt261_bra`. A chave canônica é composta por seção + ID de texto.

O adaptador de textos continua separado, com preflight, confirmação manual, transação e readback. Não substituir textos por correspondência nominal aproximada.

## 11. Cards — atualização por diff

Depois dos metadados, o fluxo normal de cards compara a fonte física atual com a base do banco pelo `card_id` original Konami.

As categorias são:

- **nova:** ID não existe no banco;
- **alterada:** ID existe e um ou mais campos mudaram;
- **possível inativa:** existia no banco e não aparece na fonte atual.

Novas e alteradas podem ser aplicadas manualmente pelo pacote selado atual. Possível inativação continua bloqueada quando não houver contrato canônico seguro para inativar.

A aplicação de cards usa preflight somente leitura, confirmação final, transação `SERIALIZABLE`, trava consultiva, verificação das precondições e readback pós-commit.

## 12. Escrita produtiva reabilitada na V4.6

A V4.5 possuía um bloqueio global deliberado (`PRODUCTIVE_WRITES_LOCKED`) durante o conserto do Extrator.

A V4.6 reabilita a escrita manual no servidor `executor\servidor_v46.py`. Isso não significa escrita automática:

- o destino continua restrito a `clube_novo`;
- o painel de dimensões exige confirmação explícita;
- cards/textos continuam usando os mecanismos de confirmação já existentes;
- nenhuma operação toca o schema legado `clube`;
- falha reverte a transação;
- readback continua obrigatório.

A configuração distribuída contém `allow_manual_dimensions_apply=true`. Instalações locais antigas que ainda não possuam essa chave herdam a autorização de `allow_manual_card_apply` somente dentro do servidor V4.6.

O painel de status de dimensões não fica consultando o contrato do banco continuamente; o contrato completo é relido nas operações que realmente dependem dele, reduzindo carga desnecessária.

## 13. Fluxo operacional completo do Extrator

Para uma atualização real do jogo:

1. iniciar a V4.6;
2. deixar a comparação automática de metadados terminar;
3. aplicar **metadados e vínculos** primeiro;
4. comparar novamente os metadados e exigir readback sem divergência para os registros já existentes;
5. revisar o diff de cards;
6. aplicar cards novos/alterados;
7. executar nova reconciliação de dimensões caso existam cards que estavam pendentes de inserção;
8. exigir que nenhum card destinado aos motores permaneça bloqueado por falta de insumo coletável;
9. só então encerrar a etapa Extrator e liberar o Otimizador.

## 14. Relação com Otimizador e Bonificador

O Extrator é produtor de insumos. Ele não decide a fórmula do Otimizador nem aplica o resultado do Bonificador.

O pipeline só avança quando:

- o card existe;
- os dados físicos necessários existem ou a ausência legítima está registrada;
- os catálogos necessários estão disponíveis;
- os vínculos de nacionalidade/clube/liga necessários a condicionais estão reconciliados;
- os slots/ímpetos foram lidos e validados;
- o gate do card não está fechado por coleta incompleta.

Depois disso:

```text
Extrator aprovado
    ↓
Otimizador — validação contra builds legadas
    ↓
Bonificador — validação dos efeitos/condicionais
```

## 15. Credenciais e segurança

- nenhuma senha vai para HTML ou JavaScript;
- o servidor escuta somente `127.0.0.1`;
- o banco alvo é `clube_novo`;
- o schema `clube` é legado/referência e não é alterado por esse fluxo;
- connection string e senha permanecem no ambiente seguro já usado pelo projeto;
- nenhuma exclusão automática é feita por ausência na fonte;
- operação concorrente de dimensões é bloqueada;
- qualquer conflito estrutural falha fechado.

## 16. Recuperação

Antes desta etapa foi feito backup local integral da pasta V4. O histórico do GitHub fornece a segunda camada de recuperação.

Em caso de falha antes do commit, a transação é revertida. Em caso de falha depois de commit confirmado, não repetir cegamente a operação: usar o readback e o manifesto/estado da execução para produzir uma correção explícita.

As pastas `RECUPERACAO` e `RESULTADOS-E-VALIDACOES` continuam preservadas como evidência histórica. Não usar código antigo como implementação atual sem autorização explícita.

## 17. Arquivos novos/alterados da V4.6

- `executor\card_dimensions_apply.py` — aplicação segura de catálogos e vínculos;
- `executor\servidor_v46.py` — servidor operacional com escrita manual reabilitada e rota de dimensões;
- `app\metadados-v46.js` — painel visual da etapa de metadados;
- `INICIAR-EXTRATOR-V46.cmd` — iniciador direto da V4.6;
- `COMPILAR-EXTRATOR-V46.cmd` — reconstrução de um clique do EXE no Windows;
- `windows-app\ClubEfootballExtractorLauncher.cs` — versão 4.6 e backend `servidor_v46.py`;
- `configuracao.exemplo.json` — inclui `allow_manual_dimensions_apply`.

## 18. Limites atuais conhecidos

- o EXE existente só representa a V4.6 depois de ser recompilado no Windows; o fonte do lançador já está atualizado;
- tipos de carta completamente novos são bloqueados até existir registro canônico/prova suficiente;
- mudança da chave canônica de tipo já usado por cards é bloqueada e exige migração própria;
- Link-up de técnicos continua adiado sem prova completa;
- possíveis inativações de cards continuam sem exclusão automática;
- famílias de catálogo sem adaptador específico continuam comparação/diagnóstico, não escrita genérica;
- o navegador precisa oferecer APIs modernas de descompressão usadas pelo núcleo.

## 19. Regra de documentação

Toda implementação, alteração, remoção ou mudança de comportamento no V4 deve atualizar este manual e, quando aplicável, o manual do Otimizador, do Bonificador e a documentação do banco no mesmo conjunto de trabalho.

Código e documentação divergentes são tratados como pendência do projeto, não como estado concluído.
