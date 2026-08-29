# Validação isolada do executável do Otimizador — 28/08/2026

## Veredito

**APROVADO ISOLADAMENTE.** O executável, o servidor local e a consulta online funcionam; a tela preserva o bloqueio funcional devolvido pelo servidor e uma carta apta conclui cálculo e paridade sem escrita.

## Matriz de provas

| Prova | Resultado | Evidência |
|---|---|---|
| Abertura pelo executável/lançador | passou | `Otimizador ClubEfootball.exe` iniciou o servidor e abriu a interface |
| Servidor somente em loopback | passou | processo `pythonw`, porta 8767, endereço `127.0.0.1` |
| Configuração local do banco | passou | `2-MOTORES/config.txt` existe e contém URL/chave; valores não foram exibidos |
| Banco online real | passou | health e catálogos retornaram `otimizador_regua_v1 · apto`; carta Messi veio do contrato `otimizador_carta_v1` com 26 atributos, 12 posições, 12 medidas corporais, IDs e cardinalidades reais |
| Navegador sem credenciais | passou | navegador chamou somente rotas relativas em `127.0.0.1:8767`; URL/chave são lidas apenas pelo processo Python local |
| Carta, função e técnico reais | passou até o gate | Messi `89138556575063`, Centroavante fixo `funcao_id=1`, Fabio Capello `tecnico_id=17601312850052` foram aceitos e consultados |
| Fail-closed de Ímpetos | passou no servidor | `/api/simular` respondeu HTTP 200, `ok=false`, `falhas=["impetos_consumidor_desligado"]` |
| Mensagem na interface | passou após correção | a tela mostrou “Simulação bloqueada” e `impetos_consumidor_desligado`, com entradas, motivo e gates visíveis |
| POST/escrita/lote | passou | POST local retornou 405 `interface somente leitura`; servidor expõe somente GET e duas RPCs de leitura |
| Caso apto completo | passou | Axel Witsel `105553384739779`, Volante de construção `funcao_id=16`, Antonio Conte `17609097478250`: `ok=true`, nota `-441.5`, gasto `56` e 26 atributos devolvidos |
| Paridade do caso apto | passou após correção do verificador | hashes esperado e calculado idênticos: `8486821d2c61bf9aed093f493c545450a10e3620f2a7e59210e2ba56f5254a3e` |
| Regressão Messi=104 | passou | teste permanente: `99 -> 99 -> 100 -> 104`; o Messi continua bloqueado na consulta online porque seu Ímpeto não pode ser consumido |

## Causa exata encontrada

O servidor local está correto e devolve um bloqueio de domínio estruturado:

```json
{"ok": false, "falhas": ["impetos_consumidor_desligado"]}
```

Em `2-MOTORES/OTIMIZADOR/interface/app.js`, a função `api()` lança uma exceção sempre que `d.ok === false`:

```javascript
if (!r.ok || d.ok === false) throw new Error(d.erro || 'Consulta local indisponível');
```

Como a resposta bloqueada possui `falhas`, mas não possui `erro`, a função descartava a causa real e usava o texto genérico. A função `apresentar()` já sabia renderizar `ok=false` como “Simulação bloqueada”, porém não recebia essa resposta porque `api()` lançava antes.

## Correção aplicada

Somente `2-MOTORES/OTIMIZADOR/interface/app.js` foi alterado. A função de transporte agora lança exceção apenas quando o HTTP falha. Uma resposta HTTP válida com `ok=false` segue para `apresentar()`, que exibe o bloqueio e suas falhas.

O reteste real confirmou:

- health e catálogo online `otimizador_regua_v1 · apto`;
- Messi, função 1 e Capello consultados via servidor local e contratos online;
- tela com título “Simulação bloqueada”;
- motivo `impetos_consumidor_desligado` exibido no resumo, resultado e gate da carta;
- POST ainda recusado com 405;
- `app.js` não contém URL, chave ou cabeçalho de autorização e usa apenas rotas locais relativas.

## Comparação com o Bonificador

Os dois aplicativos usam servidor local e função JavaScript `api()` semelhante. No caso funcional do Bonificador, sua simulação aprovada retorna `ok=true`, portanto a tela recebe e apresenta o resultado. No Otimizador, o gate legítimo de Ímpetos retorna `ok=false`, atingindo o erro de tratamento da interface.

## Impacto

- Não é falha de porta, executável, configuração ou banco online.
- Não houve escrita nem execução de lote.
- Bloqueios esperados ficam parecendo indisponibilidade local.
- O botão de paridade sofre o mesmo problema quando a simulação é bloqueada.
- O defeito específico de apresentação está encerrado. A validação positiva/paridade de uma carta apta continua sendo uma prova separada da bateria integral, pois o caso Messi deve permanecer bloqueado enquanto o consumidor de Ímpetos estiver desligado.

Nenhuma fórmula, RPC, banco, regra, Ímpeto, credencial, executável compilado ou outro motor foi alterado.

## Segunda falha de interface encontrada e corrigida

O cálculo apto do Witsel terminou corretamente, mas o botão **Validar paridade**
reprovou a primeira execução. O verificador tentava reconstruir o boost do técnico
comparando índices numéricos com rótulos como `speed`; assim descartava o `+1` que o
próprio motor havia aplicado. A correção ficou somente em
`interface/servidor.py`: a simulação conserva os vetores exatos `impeto_add` e
`boost_add` produzidos pelo motor, e o validador passa esses mesmos vetores à equação
legível. Não houve reconstrução por nome, mudança de fórmula ou ativação de Ímpetos.

O reteste online retornou paridade verdadeira e hashes idênticos. O caso bloqueado
continuou retornando `impetos_consumidor_desligado`, POST continuou em HTTP 405 e a
busca estática no HTML/JS/CSS encontrou zero URL, chave, cabeçalho de autorização ou
credencial do banco.
