# Editor da Ficha e molde v6 — conferência de 13/09/2026

O editor chama `public.site_novo_editor_avaliar_v1`, que delega a
`build_editor.avaliar_v1`. A função consulta `otimizador_molde` pela maior versão
existente (6 nesta conferência); não existe molde v5 fixo no JavaScript.
Foram relidos os alvos/pesos das funções 8 e 10 e confirmadas as mudanças aprovadas.

## Prova com resultados novos

21 linhas recebidas do lote `39da8ff4-7a4a-4ec7-8641-e81b5677ad4c`, cobrindo
19 especialidades, foram avaliadas com as mesmas barras, habilidades, técnico e
ímpetos. As 21 pontuações brutas coincidiram entre resultado recebido, avaliador
do editor e `regua.py:notaDe` executado localmente. A amostra inclui as linhas
3397142 (Meia Ofensivo: 374,3) e 3397146 (Meia Armador: 338,5).
Os snapshots das 19 linhas iniciais também coincidiram com os alvos/pesos v6.
Nota final inclui os bônus; esta prova não declara a rodada do Bonificador encerrada.

## Divergência encontrada no Otimizador

Não há paridade integral de atributos em duas das 21 linhas:

| Linha | Função | Atributo | Resultado recebido | Editor | Peso |
|---|---|---|---:|---:|---:|
| 3397269 | 5 | Resistência | 65 | 66 | 0 |
| 3397429 | 6 | Passe rasteiro | 76 | 77 | 0 |

Ambas usam Thomas Tuchel, ID 17606413224402. O catálogo confirmado fornece +1 nos
dois atributos. `motor.py:tecnicos_uteis` agrupa técnicos pelos atributos com peso
e sobrescreve `r['boost']` com essa lista reduzida. O cálculo dos atributos finais
consome essa lista e perde o boost nos atributos de peso zero. O editor usa todos
os boosts confirmados, conforme a equação do jogo. A pontuação destas linhas não
muda porque os atributos divergentes têm peso zero.

Pendência: corrigir a composição de atributos do Otimizador preservando a seleção
e a pontuação, testar e entregar atualização compatível para a Máquina 2, além de
tratar os resultados já emitidos. Não reduzir os atributos do editor para imitar
essa omissão. Nesta conferência nenhum processo, pacote selado ou resultado foi
alterado. A extensão total do problema ainda não foi medida.
