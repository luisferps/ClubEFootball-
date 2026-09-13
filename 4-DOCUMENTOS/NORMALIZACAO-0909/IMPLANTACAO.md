> Atualização 10/09/2026: normalização vigente por amplitude: 100 + 50 × motor / (máximo teórico − mínimo teórico) + bônus. Consulte 4-DOCUMENTOS/NORMALIZACAO-0909/AMPLITUDE-VIGENTE.md; curvas anteriores são históricas.

# Implantação confirmada — 09/09/2026

**Concluída no banco e publicada no Netlify.**

- 55.151 publicações ativas, 55.151 na regra nova, zero pendentes de normalização e zero sem delta no readback das 11:42 UTC.
- Zero divergência de bruto, bônus, soma final, par de motores, ponte/delta ou componentes (atributos, arows, barras e habilidades). O verificador cobre todas as publicações, não apenas os primeiros cards.
- 55.292 registros de histórico de pontuação naquele instante. O número pode superar o de linhas porque preserva cada versão anterior, inclusive finalizações concorrentes.
- 820 pontos das 19 curvas conferidos; extremos molde=100 e teto=110. Casos manuais de Ronaldinho e Buffon reproduzidos.
- Finalização nova ensaiada em transação com rollback; chamada repetida na linha 2907 confirmou `ja_publicada`, `idempotente=true`, nota 110,82539794737939.
- Editor: pontuação bruta, bônus integral e nota final idênticos à publicação nos líderes das 19 funções. O editor mantém escolhas manuais livres. Guardas de ímpetos de GO agora reconhecem o estado já aprovado `convencao_go_aprovada_usuario_delta_fisico`. Nenhum efeito foi alterado.
- Limite da auditoria de atributos do editor: os 26 atributos de jogo coincidiram em 18 desses 19 casos. Na linha 30016 o Passe alto existente é 78 e a avaliação das escolhas atuais devolve 79. As duas notas brutas são 438,1 e as duas notas finais 112,24819972960016. Essa divergência não foi sobrescrita na tabela do motor nem atribuída à normalização. A entrega muda a escala da nota e preserva o resultado do motor; não declara equivalência universal de todos os atributos históricos.
- Goleiros na leitura: 160 linhas defensivas e 289 ofensivas, zero mistura de estilos. A ponte produtiva conserva as linhas; nenhuma foi removida pela seleção de vitrine.
- Testes de Boxes com HTTP real, shell, navegação, Ranking e três comportamentos do editor aprovados. Conferência visual em desktop e celular, seis níveis, sem porcentagens/etiquetas nos cards e sem rolagem horizontal.

## Netlify

Projeto: `imaginative-granita-ace1ca`.
Deploy publicado: `6aa145d2cc4c3074ca5b98fa`, 09/09/2026 às 08:41 (Brasília).
Site: https://imaginative-granita-ace1ca.netlify.app/

21 arquivos públicos conferidos. Vinte são idênticos por SHA-256 ao pacote. Em `ficha.html`, o Netlify apenas reescreveu os sete links de `index.html#...` para `/#...` e normalizou a marcação desses links; a comparação da estrutura HTML confirmou equivalência. JS, CSS e demais conteúdos conferidos. Os manuais/SQLs não foram enviados ao site. Não houve push para GitHub.

## Artefatos oficiais

- `REGRA-APROVADA.md`, `parametros.json` e `regua-comparativo.cjs`.
- SQLs 01–05: normalização, ativação/finalizador, estrelas, editor e filtros de leitura dos goleiros.
- `READBACK-IMPLANTACAO.json`, `MANIFESTO-WEB.json` e `VALIDACAO-ESTRELAS.json`.
- Os adendos atuais de `AGENTS.md`, `MANUAL-DAS-TABELAS.md`, `MANUAL-DA-TELA.md`, manual e caderno do Site Novo apontam para esta decisão. SQLs anteriores à entrega permanecem históricos; não reaplicá-los depois dos SQLs 01–05.

## Curvas uniformes

Foi preparada comparação separada, sem publicação ou gravação de outra fórmula: `COMPARATIVO-NOTAS/curva-unica-0909` nos outputs da tarefa, servida em http://127.0.0.1:8766/curva-unica-0909/ . Mesma fotografia, bônus integral e nenhum ajuste por nome nas três alternativas.

Na fotografia comparada, a oficial tem 1,45 ponto entre líderes e oito funções no top 10 geral. Linear: 3,24 e seis; quadrática: 4,06 e cinco; racional: 3,97 e cinco. Esses primeiros controles uniformes não justificam substituir a oficial. O comparativo fica disponível para avaliação futura; não é autorização para mudar produção.
