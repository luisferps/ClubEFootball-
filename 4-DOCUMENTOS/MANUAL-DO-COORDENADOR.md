# Manual do Coordenador

**Estado deste documento:** projeto futuro, ainda não implementado.

O Coordenador será um quarto aplicativo **local**, separado do Extrator, do Otimizador e do Bonificador. Ele não substituirá nenhum deles e não fará cálculos. Sua função será organizar a ordem do trabalho, verificar se cada etapa terminou corretamente e mandar continuar somente quando os dados estiverem completos e compatíveis.

Hoje não existe Coordenador em execução. Não há tarefa agendada, serviço ligado, automação ativa nem aplicativo criado por este documento.

## Em linguagem de jogo

Quando o jogo receber uma atualização, o Coordenador deverá cuidar do processo inteiro:

1. acordar nos horários previstos de atualização do jogo no horário de Brasília: **quarta-feira às 05:00** e **domingo às 23:30**;
2. esperar os arquivos do jogo ficarem disponíveis e estáveis;
3. comparar os fingerprints com a última versão processada;
4. encerrar sem fazer nada se os arquivos forem exatamente os mesmos;
5. havendo mudança real, chamar o Extrator local;
6. aguardar o banco criar as pendências da nova versão das cartas;
7. liberar Otimizador e Bonificador locais para trabalharem em paralelo;
8. conferir se os dois devolveram resultados compatíveis com a mesma versão da carta;
9. permitir a publicação somente quando todos os gates estiverem aprovados.

Em resumo:

```text
Arquivos novos do jogo
        ↓
Extrator local
        ↓
Banco e pendências por versão
        ↓
Otimizador local ─────┐
                      ├──→ Build nova completa ──→ Publicação
Bonificador local ────┘
```

O Coordenador apenas acompanha e organiza essas etapas. As fórmulas continuam pertencendo aos seus motores e não podem ser alteradas por ele.

## Horários automáticos futuros

O funcionamento automático planejado terá duas verificações semanais, sempre considerando o horário do Brasil:

- quarta-feira às 05:00;
- domingo às 23:30.

Esses horários são momentos de verificação, não autorização para processar cegamente. Ao acordar, o Coordenador deverá:

- confirmar que os arquivos esperados existem;
- confirmar que não estão sendo modificados naquele momento;
- calcular e comparar fingerprints;
- validar a versão do contrato de leitura;
- continuar somente se existir mudança real e compatível.

Se não houver mudança, deverá registrar “sem atualização” e encerrar o ciclo.

## Processo futuro completo

### 1. Arquivos do jogo e Extrator

O Extrator consulta no banco o contrato vigente, lê somente os arquivos e campos pedidos, valida versão e fingerprints e devolve uma resposta selada. O Coordenador não informa endereços por conta própria e não mantém um mapa alternativo.

### 2. Banco e pendências

O banco aceita somente uma carga integral e compatível. Para cada carta nova ou alterada, cria pendências independentes para:

- Otimizador;
- Bonificador.

Cada pendência fica ligada à versão e ao fingerprint exatos da carta.

### 3. Motores em paralelo

Otimizador e Bonificador podem trabalhar ao mesmo tempo porque cada um grava sua contribuição em uma área separada:

- `clube_novo.build_resultado_otimizador`;
- `clube_novo.build_resultado_bonificador`.

Uma parte não pode apagar nem substituir a outra.

### 4. Build e publicação

Os resultados convergem para o vínculo correspondente em `clube_novo.build_carta`. A publicação final passa por `clube_novo.build_publicacao`.

O estado de publicação deverá apresentar, no mínimo:

- `status`;
- `pode_publicar`;
- `falta_o_que`.

Nenhuma etapa incompleta, inválida ou de versão diferente segue adiante. A tela online lê somente registros efetivamente publicados; nunca lê rascunhos, pendências ou resultados parciais.

## Recuperação e retomada

O processo precisa sobreviver a desligamentos e falhas.

Se o computador estiver desligado no horário previsto, o Coordenador não deve tentar reconstruir o passado por adivinhação. Na próxima abertura, ele consulta no banco:

- a última versão concluída;
- ciclos interrompidos;
- pendências ainda abertas;
- etapas prontas;
- etapas inválidas ou com erro.

Depois retoma somente o que estiver faltando. Etapas já concluídas com a mesma chave idempotente e os mesmos fingerprints não são repetidas, duplicadas nem sobrescritas.

Se uma etapa falhar, as anteriores permanecem preservadas. O ciclo fica bloqueado exatamente no ponto da falha, com causa registrada, até uma nova tentativa válida.

## Interface pretendida

O futuro aplicativo local deverá ser simples e mostrar somente ações operacionais claras:

- **Atualizar agora** — inicia manualmente a mesma verificação segura do ciclo automático;
- **Última atualização** — versão, horário, resultado e fingerprints;
- **Etapas e pendências** — Extrator, banco, Otimizador, Bonificador e publicação;
- **Tentar novamente** — repete somente uma etapa que falhou;
- **Histórico** — ciclos, mudanças detectadas, falhas, retomadas e publicações.

As credenciais e chaves permanecem no ambiente local protegido. O navegador da interface e a tela pública não recebem credenciais, chave de serviço nem acesso direto às tabelas privadas.

## Arquitetura do Coordenador

O Coordenador deverá operar como uma máquina de estados persistente. Cada ciclo terá uma identidade única composta por versão do jogo, fingerprints das fontes e versão do contrato.

Estados conceituais esperados:

```text
aguardando_arquivos
→ validando_mudanca
→ extraindo
→ carregando_banco
→ aguardando_motores
→ validando_build
→ publicando
→ concluido
```

Uma falha leva o ciclo a um estado bloqueado, preservando a última etapa confirmada. A retomada começa desse checkpoint.

Os nomes finais de tabelas ou funções exclusivas do Coordenador somente serão definidos depois da auditoria de integração. Este manual não declara que essas estruturas já existam.

## Gates obrigatórios de segurança

1. **Um pipeline por vez:** não pode haver dois ciclos alterando a mesma versão simultaneamente.
2. **Versão e fingerprint:** toda entrada e toda saída precisa carregar a versão e os fingerprints correspondentes.
3. **Idempotência:** repetir a mesma etapa com a mesma chave deve produzir o mesmo estado, sem duplicar registros.
4. **Fail-closed:** ausência, incompatibilidade ou dúvida bloqueia o avanço.
5. **Rollback e readback:** qualquer futura escrita precisa ter transação, recuperação e leitura posterior comprovando o resultado.
6. **Pendências registradas:** nenhuma falha pode desaparecer silenciosamente; etapa, causa, tentativa e próximo passo ficam registrados.
7. **Mesma versão da carta:** Otimizador e Bonificador só podem formar uma publicação quando trabalharam sobre a mesma versão e fingerprint.
8. **Sem resultado parcial:** a Build não é publicada com apenas um motor concluído.
9. **Sem legado em runtime:** tabelas antigas servem apenas para histórico e recuperação, nunca como fallback operacional.
10. **Sem credenciais no navegador:** somente serviços locais autorizados acessam contratos e tabelas privadas.

## Estado atual versus futuro

### Já existe

- Extrator, Otimizador e Bonificador como frentes separadas;
- contratos e referências do modelo novo por IDs;
- Build canônica em `clube_novo`;
- vínculo M:N `build_carta`;
- resultados separados de Otimizador e Bonificador;
- gate de banco que recusa publicação parcial;
- [Manual de Interligação de Sistemas](./MANUAL-DE-INTERLIGACAO-DE-SISTEMAS.md).

### Ainda será construído

- o aplicativo local Coordenador;
- seu executável, ícone e interface;
- o agendamento de quarta-feira e domingo;
- a máquina de estados e checkpoints do ciclo;
- a consulta e retomada automática de pendências;
- a ligação operacional entre os três aplicativos e a Build nova;
- logs e histórico próprios do Coordenador.

Nada desta seção futura foi ativado, agendado ou ligado pela criação deste manual.
