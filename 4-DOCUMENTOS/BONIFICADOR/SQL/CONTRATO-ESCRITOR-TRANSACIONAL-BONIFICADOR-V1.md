# Escritor transacional do Bonificador V1

Status: **preparado e não aplicado ao banco vivo**.

O pacote instala `public.gravar_build_bonificador_v1(jsonb)` e o leitor
privado `public.bonificador_contexto_escrita_v2(integer,integer)`. A
função grava um resultado imutável em `clube_novo.build_bonificador` e o liga a
uma linha já existente em `clube_novo.build_linha_card`, na mesma transação.
Não lê nem escreve `clube.build` ou `clube.fila` e não interfere na publicação,
Home, boxes ou fotos.

## Pré-requisito obrigatório

`4-DOCUMENTOS/EXTRATOR/SQL/APLICAR-COMPLETUDE-MOTORES-CARTA-V1.sql` precisa
estar aplicado e validado. A função confere novamente, no instante da gravação:

- carta fisicamente conferida, vigente e apta;
- `carta_versao` e `carta_fingerprint` iguais aos selos atuais;
- contrato `public.bonificador_carta_v1` ainda liberado;
- linha card/função/posição exata e ainda pendente;
- total exatamente igual às parcelas declaradas.

Um bloqueio de motor não bloqueia a publicação da carta.

## Envelope aceito

O JSON exige somente estes campos, sem extras:

```json
{
  "build_linha_card_id": 123,
  "card_id": "176844",
  "funcao_id": 10,
  "posicao_id": 3,
  "carta_versao": "regra-versionada",
  "carta_fingerprint": "sha256-vigente",
  "contrato_versao": "bonificador-carta-v1",
  "contrato_fingerprint": "fingerprint-do-contrato",
  "formula_fingerprint": "fingerprint-da-formula",
  "motor_versao": "versao-do-motor",
  "bonus_pe": 0,
  "bonus_fisico_total": 0,
  "bonus_fisico_detalhe": {"altura": 0},
  "bonus_posicao": 0,
  "bonus_playstyle_1": 0,
  "bonus_playstyle_2": 0,
  "bonus_ia": 0,
  "bonus_outros": {},
  "bonus_total": 0
}
```

O `resultado_fingerprint` não vem do cliente. O banco o calcula sobre o JSON
normalizado, incluindo identidade, selos e parcelas. Repetir exatamente o mesmo
pedido devolve o mesmo ID sem criar uma segunda linha. Resultado diferente não
substitui silenciosamente o anterior.

O cliente também não inventa `build_linha_card_id`, posição ou selos. Antes de
calcular, lê `bonificador_contexto_escrita_v2`, que devolve somente linhas
pendentes com Otimizador ligado, completude vigente/apta e os seguintes selos:

- `carta_versao` e `carta_fingerprint`;
- `contrato_versao`;
- `contrato_fingerprint`, derivado das definições atuais dos contratos de régua
  e carta;
- `formula_fingerprint`, derivado do JSON canônico atual da régua.

O writer recalcula todos eles sob a mesma transação e rejeita qualquer mudança.

`bonus_outros` precisa permanecer `{}` nesta versão. A tabela possui essa coluna,
mas não existe no contrato atual uma regra física que diga como itens livres
entram em `bonus_total`; aceitá-los seria inventar uma soma. O total V1 é a soma
exata das seis parcelas numéricas explícitas.

`bonus_fisico_detalhe` não aceita as antigas notas intermediárias de 0 a 1. Cada
chave deve guardar a contribuição efetiva daquela medida para a fórmula final;
todos os valores precisam ser numéricos e sua soma exata precisa reproduzir
`bonus_fisico_total`. O cliente deve compensar o arredondamento na última
parcela, sem mudar o total da fórmula. Objeto vazio ou soma divergente bloqueiam
a transação.

## Ordem futura de ativação

1. aplicar e validar o gate de completude;
2. aplicar este pacote;
3. adaptar um cliente novo para enviar o envelope acima;
4. testar uma transação controlada e fazer o readback em outra conexão;
5. só então liberar lotes reais.

O `2-MOTORES/BONIFICADOR/motor_bonus.py` atual é legado e não foi alterado. Ele
envia quatro parcelas agregadas, não envia o ID da linha nem os selos exigidos e
continua chamando a porta bloqueada `public.gravar_bonus(jsonb)`. Portanto, não
é compatível com este writer sem uma migração separada do cliente.

## Privilégios e ordem de instalação

A leitura somente de 31/08/2026 confirmou que `service_role` não possui hoje:

- `SELECT/INSERT` em `clube_novo.build_bonificador`;
- `SELECT/UPDATE` em `clube_novo.build_linha_card`;
- `USAGE` na sequência identity de `build_bonificador`;
- `SELECT` na completude, que ainda não existe no banco vivo.

Por esse motivo o writer segue o mesmo limite dos RPCs privados existentes:
`SECURITY DEFINER`, owner explícito `postgres`, `search_path=''`, nomes de objetos
qualificados e validação integral dentro da função. Ele não concede nenhuma ACL
direta nas tabelas. `PUBLIC`, `anon` e `authenticated` ficam sem `EXECUTE`; apenas
`service_role` recebe execução.

As duas portas RPC ficam em `public`, porque o Data API vivo não expõe
`clube_novo` (`PGRST106` já comprovado). O cliente REST usa normalmente
`/rest/v1/rpc/bonificador_contexto_escrita_v2` e
`/rest/v1/rpc/gravar_build_bonificador_v1`, sem `Content-Profile` ou
`Accept-Profile` customizado. Isso não muda a autoridade: todo dado lido ou
gravado pelas funções continua exclusivamente em `clube_novo`; não existe
fallback para `clube.build`, `clube.fila` ou `public.gravar_bonus(jsonb)`.

O banco ainda está sem materialização da completude: as tabelas de execução e
aplicação do Extrator estão vazias. Isso define a ordem de instalação, não exige
uma coluna nova neste writer. Não há dependência de `aplicacao_id` aqui; a
dependência é apenas da versão vigente/apta que o gate deverá criar.

O rollback remove somente a função. Ele nunca apaga resultados que já tenham
sido gravados, porque isso destruiria evidência operacional.

## Uso pelo instalador atômico

Os arquivos normais `APLICAR-...V1.sql` e `ROLLBACK-...V1.sql` têm
`BEGIN/COMMIT` próprios e devem ser executados isoladamente. Para a instalação
única junto com completude e seed, usar exclusivamente:

- `APLICAR-ESCRITOR-TRANSACIONAL-BONIFICADOR-V1-COMPOSAVEL.sql`;
- `ROLLBACK-ESCRITOR-TRANSACIONAL-BONIFICADOR-V1-COMPOSAVEL.sql`.

As variantes composáveis não possuem `BEGIN`, `COMMIT` ou `ROLLBACK`; o
instalador é responsável pela transação externa. O teste offline exige que o
corpo delas seja exatamente igual ao standalone, exceto pelo controle
transacional e pelo cabeçalho explicativo.
