# Aplicativo local do Bonificador

**Versão:** 1.0.0 · **Data:** 28/08/2026 · **Estado:** somente leitura

Abra `2-MOTORES/BONIFICADOR/Bonificador ClubEfootball.exe`. Ele é um aplicativo local
com ícone próprio: o EXE inicia o executor oculto em `127.0.0.1:8766`, confirma a
saúde e abre a janela. `RODAR-INTERFACE-BONIFICADOR.bat` recompila somente esse
lançador, se necessário, e o abre.

Na tela, o usuário informa o `card_id` e escolhe a função. A resposta mostra corpo, pé
ruim, posição principal, os dois playstyles, IA, molde, régua, regras, bônus e gates.
Também mostra contrato, proveniência, cardinalidades e fingerprint do motor.

O browser não conhece Supabase: `app.js` não contém chave, URL, schema ou acesso a
tabelas. Ele só chama o executor local por `GET`. O executor usa a chave local e
permite unicamente os contratos `bonificador_regua_v1` e `bonificador_carta_v1`.
`POST`, lote, escrita e alteração de fórmula não existem nesta aplicação.

## Provas realizadas

- compilação do EXE com ícone multirresolução;
- abertura pelo EXE e health-check aprovado para `bonificador-regua-v1`;
- `TESTES/testar_interface_local.py`: Casillas determinístico, `b_estilo=1.5`, POST
  bloqueado (405) e frontend sem credencial;
- validação visual e online: Iker Casillas `88045755827028`, função #5, exibiu slots
  `291`/`336`, todos os gates aprovados, `b_estilo=1.5000`, `b_total=1.6875` e console
  sem erros.

O rollback de todos os arquivos exclusivos está em
`RECUPERACAO/2026-08-28-ANTES-INTERFACE-LOCAL`; ele não toca motor, `config.txt`,
contratos, banco, Otimizador ou Extrator.
