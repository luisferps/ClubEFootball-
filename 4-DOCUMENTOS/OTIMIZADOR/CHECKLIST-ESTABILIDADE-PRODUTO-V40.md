# Checklist oficial — produto Otimizador V40

Data: 31/08/2026. Escopo: abertura portátil, leitura rápida e ordem visual da
fila. Não autoriza iniciar worker, preparar lote, publicar resultado, alterar
fórmula, pesos, moldes, regras de negócio, estados de fila ou dados do banco.

## Ordem de acompanhamento

- [x] a aba **Fila integral** recebe primeiro a linha em processamento e as
  pendentes em `ordem_fila` crescente;
- [x] linhas finais ficam depois das abertas, sem alterar a ordem real de
  execução;
- [x] a aba **Resultados** recebe somente linhas finais, mais recentes primeiro;
- [x] a primeira página do lote real confirmou pendentes `246,247,248,249,250`;
- [x] Resultados confirmou finais `245,244,243,242,241`;
- [x] a UI informa a ordem recebida, sem depender de reordenação textual.

## Produto e segurança

- [x] o ponto único de abertura continua
  `2-MOTORES/OTIMIZADOR/Otimizador ClubEfootball.exe`;
- [x] o serviço portátil V40 inclui `psycopg` e as bibliotecas necessárias no
  diretório `runtime/_internal/`;
- [x] navegador fala exclusivamente em `127.0.0.1`; a conexão privada fica no
  servidor local e não é enviada para JavaScript;
- [x] `otimizador_portal_local_v3` é uma ponte de allowlist de leitura; não dá
  acesso de navegador a tabela, legado ou SQL arbitrário;
- [x] a Fila usa rótulos canônicos mínimos por ID e não aguarda o catálogo pesado
  de teste individual;
- [x] indisponibilidade do contrato continua fail-closed: controles não são
  habilitados por cache ou fallback legado.

## Provas executadas

- [x] sintaxe: `py_compile` de `interface/servidor.py` e `node --check` de
  `interface/app.js`;
- [x] `teste_interface_local_otimizador.py`: 20/20 testes verdes;
- [x] `teste_formula_aprovada.py`: Messi/Capello/Precisão retorna 104;
- [x] serviço empacotado em porta isolada: saúde V40, banco conectado, Fila e
  Resultados responderam;
- [x] lançador oficial testado em porta oficial livre: abriu o serviço V40, sem
  worker, e devolveu as cinco próximas pendentes;
- [x] nenhum worker, preparador, reserva, linha ou resultado foi criado ou
  modificado durante estas provas;
- [x] os processos iniciados exclusivamente para teste foram encerrados depois
  de identificar o executável e a porta.

## Recuperação

- [x] snapshot anterior:
  `4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260831-v40-ponte-privada-antes/`;
- [x] migrações aplicadas: V13 e V16, com arquivos de rollback no mesmo diretório
  `FILA-PRODUCAO-V3/`;
- [x] V15 não foi aplicada; é histórico e foi substituída pela V16.

## Travas preservadas

- [x] fórmula aprovada: barras teto 99 -> proficiência piso/teto 40/99 -> boost
  técnico -> ímpetos;
- [x] Ímpetos condicionais continuam sujeitos aos gates já existentes;
- [x] Bonificador e publicação não são acionados pela interface;
- [x] nenhuma leitura retorna a tabelas legadas como fallback.
