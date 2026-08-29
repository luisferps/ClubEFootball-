# Matriz e plano — organização física dos motores

Data: 28/08/2026. Escopo: organizar arquivos por responsabilidade, sem alterar
fórmula, pesos, ordem de cálculo, dados, banco ou execução produtiva.

## Destino aprovado pelo inventário

```text
2-MOTORES/
  config.txt                         # comum e secreto; não mover
  OTIMIZADOR/                         # lote, cálculo e auditorias do Otimizador
  BONIFICADOR/                        # executável exclusivo do Bonificador
  funcao_nativa.py                    # outro fluxo histórico; manter comum
  regras_do_card.py                   # coleta/box; manter comum
```

`6-AVALIADOR-NO-RAILWAY/` já contém somente o serviço do Otimizador. Não será
renomeado ou deslocado: o `Procfile` externo sobe `gunicorn app:app`, portanto a
renomeação alteraria a implantação sem separar responsabilidade adicional.

`1-SISTEMA/`, `SITE-ATUALIZADO-2026-08-24/` e `7-VARREDURA-DO-JOGO/` não entram na
movimentação. São, respectivamente, UI geral/réplicas, publicação e Extrator; ficam
nos locais comuns e apontam para os motores apenas por documentação/contrato.

## Matriz de responsabilidade e dependência

| item atual | responsabilidade | chamados por / chama | destino | ação de caminho |
|---|---|---|---|---|
| `2-MOTORES/roda_lote_v6.py` | Otimizador — lote | `RODAR-O-MOTOR.bat`, `RODAR-TUDO.bat`; importa os auxiliares | `2-MOTORES/OTIMIZADOR/` | lançadores passam a entrar na pasta nova |
| `fonte_unica.py` | Otimizador — contrato de entrada | lote, equação, motor e conferência; RPCs v1 | `OTIMIZADOR/` | import relativo de diretório continua entre irmãos |
| `equacao.py`, `regua.py`, `motor.py`, `travas.py` | Otimizador — cálculo e gates | lote, conferência e testes | `OTIMIZADOR/` | nenhum conteúdo matemático muda |
| `grava_direto.py` | Otimizador — escritor histórico alternativo de saída | importado pelo lote, sem payload na rota atual | `OTIMIZADOR/` | permanece junto do único chamador |
| `conferir_uma.py` | Otimizador — conferência manual | `CONFERIR-UMA-LINHA.bat` | `OTIMIZADOR/` | lançador atualiza `cd` |
| `auditar_entradas_v1.py`, `auditar_moldes_v1.py`, `classificar_diferencas_fisicas_v1.py` | Otimizador — auditorias | testes e execução manual | `OTIMIZADOR/` | testes recebem o novo caminho |
| `motor_bonus.py` | Bonificador — bônus físico/estilo | sem `.bat` ativo; RPCs `bonificador_*_v1` e `gravar_bonus` | `2-MOTORES/BONIFICADOR/` | testes/documentação apontam ao novo caminho; nenhuma fórmula muda |
| `config.txt` | configuração comum | Otimizador e Bonificador localizam ao subir diretórios | `2-MOTORES/config.txt` | não mover, não ler/imprimir e não versionar |
| `funcao_nativa.py` | regra histórica de classificação | nenhum lançador/import alcançável do Otimizador/Bonificador | raiz comum | não mover: outros fluxos/documentos antigos podem referenciá-lo |
| `regras_do_card.py` | coleta/box | declaradamente usado por coletores externos | raiz comum | não mover: não pertence a nenhum dos dois motores |
| `6-AVALIADOR-NO-RAILWAY/*.py`, `Procfile` | serviço do Otimizador | `Procfile -> app.py -> banco/regra/avaliador/otimizador` | mantém pasta exclusiva existente | somente referências documentais, nenhuma mudança de deploy |
| `4-DOCUMENTOS/OTIMIZADOR/**` | documentação, testes e recuperação do Otimizador | testes leem fontes e snapshots | mantém pasta exclusiva existente | atualizar somente caminhos ativos nos testes/manuais |
| `4-DOCUMENTOS/BONIFICADOR/**` | documentação, testes e recuperação do Bonificador | testes comparam o executável e snapshot | mantém pasta exclusiva existente | atualizar caminho atual; snapshots continuam apontando ao caminho histórico |
| `1-SISTEMA/**`, réplicas e UI | interface geral | lê builds/projeções; não importa Python | mantém local comum | não mover nem reescrever fórmula/contrato nesta organização |
| `7-VARREDURA-DO-JOGO/**` | Extrator | fonte física e referências | mantém local comum | não mover |

## Arquivos que precisam ter caminho atualizado

- lançadores: `RODAR-O-MOTOR.bat`, `RODAR-TUDO.bat`,
  `CONFERIR-UMA-LINHA.bat`, `1-LIMPAR-ANTES-DE-SUBIR.bat`, `APAGAR-O-LIXO.bat`;
- testes: cinco em `4-DOCUMENTOS/OTIMIZADOR/TESTES` e dois em
  `4-DOCUMENTOS/BONIFICADOR/TESTES`;
- manuais/checklists/auditorias que apresentam caminho executável atual;
- a referência histórica do snapshot **não** será reescrita: ela registra o local
  original e o teste de trava comparará o arquivo novo contra a cópia antiga.

## Execução atômica e recuperação

1. Criar ZIP, manifesto SHA-256 e patch do estado imediatamente anterior para os
   lançadores, fontes, testes, manuais e documentos afetados.
2. Criar as duas pastas de destino e mover somente os 11 arquivos classificados.
   Não mover `config.txt`, UI, Extrator, serviço Railway, `funcao_nativa.py` ou
   `regras_do_card.py`.
3. Atualizar caminhos de lançadores, testes e documentação por hunks explícitos;
   imports entre arquivos do Otimizador permanecem irmãos e não mudam de nome.
4. Provar a estrutura: nenhum arquivo executável do Otimizador/Bonificador fica na
   raiz de `2-MOTORES`; nenhuma referência ativa aponta para o caminho antigo.
5. Executar testes de fórmula/auditoria, testes do Bonificador, `py_compile` e
   validação estática de cada lançador. Os dois lançadores produtivos não serão
   executados: o teste confirma alvo e comando sem consumir fila ou gravar build.
6. Rollback: restaurar somente os arquivos e caminhos do ZIP/patch desta etapa,
   sem checkout/reset e sem tocar nos snapshots anteriores.

## Critério de aprovação

- Otimizador: 11 fontes/auditorias reunidas em `2-MOTORES/OTIMIZADOR/`;
- Bonificador: 1 executável reunido em `2-MOTORES/BONIFICADOR/`;
- comuns preservados: `config.txt`, `funcao_nativa.py`, `regras_do_card.py`, UI,
  serviço e Extrator;
- lançadores e testes resolvem os destinos novos;
- fórmulas e conteúdo de algoritmo idênticos por hash/AST onde os testes já cobrem;
- nenhuma referência de caminho antigo fora de snapshots e documentação histórica.
