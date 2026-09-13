# Executor seletivo de estilos V12 — operação de 09/09/2026

## Encerramento confirmado em 09/09/2026

A correção seletiva dos bônus de estilo terminou: **67.795 resultados e 7.455 publicações concluídos, zero pendências e erros nessa operação**. O banco e o painel confirmaram o encerramento em 2026-09-09T08:13:50.106412+00:00. As nove publicações finais foram conferidas no contrato da Ficha, preservando a revisão de habilidades do Otimizador e a ordem dos lotes. A falha do UPDATE de encerramento foi corrigida no banco e no SQL oficial.

Evidência e alcance: [Conclusão dos bônus de estilo](CONCLUSAO-BONUS-ESTILOS-0909.md). A produção geral do Bonificador e as execuções do Otimizador têm estados próprios; este encerramento não significa que seus lotes foram executados. Os registros de andamento abaixo são históricos.

## Retomada futura na Máquina 2 — arquivos preparados

Os arquivos V12 do Bonificador completo estão preparados para cópia direta.
O operador usa o mesmo INICIAR-REPROCESSAMENTO.bat após terminar a correção de
estilos. Antes disso, o comando não inicia nem reserva linhas. A versão do lote
e a política geral só serão atualizadas no início solicitado pelo operador.
Detalhes: [Entrega da Máquina 2](ENTREGA-MAQUINA-2-V12.md). Os registros anteriores abaixo são históricos.

## Estado
Executor criado, validado e iniciado na máquina oficial. O progresso é consultado
no painel local e no banco; este documento não declara conclusão antecipada.
Último registro desta entrega: 2026-09-09T05:42:19.917775+00:00.

O usuário autorizou manter as publicações atuais disponíveis durante a correção.
Cada substituição atualiza dados, selos e publicação na mesma transação.
A Máquina 2 e a fila geral permanecem adiadas/pausadas. A política mantém
aprovada_implantacao_pendente porque a produção geral V12 ainda não foi liberada;
a operação seletiva abaixo já consome e aplica a regra aprovada.

## Escopo
- 178.528 resultados vigentes auditados.
- 67.795 resultados com parcelas de estilo divergentes.
- 7.455 publicações a substituir gradualmente.
- Apenas clube_novo é fonte e destino operacional. As RPCs em public são
  portas de acesso; não usam tabelas do schema histórico clube.
- Sem alteração de Otimizador, normalização, corpo, pé, IA, ordem de lotes,
  prioridades, tentativas ou estado dos itens da fila geral.

## Contratos e registros
clube_novo.correcao_estilos_execucao_v12 registra a auditoria e conclusão.
clube_novo.correcao_estilos_item_v12 liga resultado anterior, resultado novo,
estilos esperados, publicação anterior e estado por linha.
public.correcao_estilos_status_v12 consulta o progresso.
public.correcao_estilos_tick_v12 corrige até 500 resultados e publica até 20
por chamada; o aplicativo solicita 250. As chamadas são exclusivas de service_role.
clube_novo.bonus_estilo_conforme_v12 impede novas finalizações incompatíveis
com a política. Resultados V11 numericamente corretos continuam aproveitáveis.

Os campos físicos das cartas e seus fingerprints foram preservados.
public.site_novo_ficha_v2 agora projeta os estilos efetivos de ataque e defesa,
incluindo Primeiro Volante e Meia Versátil nos dois slots quando aplicável.

SQL oficial: SQL/EXECUTOR-CORRECAO-ESTILOS-V12.sql e
SQL/PREPARAR-AUDITORIA-EXECUTOR-ESTILOS-V12.sql.
Migrações aplicadas:
- instalar_executor_seletivo_estilos_v12_e_publicacao_compativel
- preservar_publicacoes_ate_troca_atomica_estilos_v12
- conferir_referencia_publicada_historica_equivalente_estilos_v12

## Preservação da publicação
Algumas publicações usam outro ID histórico de Bonificador, com parcelas
idênticas ao resultado vigente. A conferência exige o ID/selo do snapshot
público preservado e igualdade de todas as parcelas antes da substituição.
O primeiro bloqueio na linha 2545 foi investigado e corrigido por esse motivo;
o fato e a retomada ficaram registrados na auditoria do banco.

## Validação
Piloto persistido: Vieira 36663, estilo 0,5 → 1,5; Desailly 382550 e 382551,
estilo 0,5 → 1,0. Demais parcelas e Otimizador conferidos iguais.
Repetição do piloto: zero novas correções/publicações, confirmando idempotência.
Conferência posterior em 4.503 resultados: zero alterações nos demais bônus;
publicações ainda aguardando troca conservaram os IDs e selos anteriores.
Total público permaneceu 55.151. Estados e prioridades da fila original
foram comparados com o snapshot e permaneceram iguais.

Testes locais: teste_executor_estilos_v12.py cobre confirmação após perda de
resposta e pausa após terminar o lote, sem iniciar outro. O EXE foi testado
com o banco e a reabertura do aplicativo usa o mesmo executor.
SHA-256 do EXE: 0be4ab02808cbfa4fb28c52ae3ed9d5bb04afbc03fcfb810dd0ee2ca6b3206ca

Segurança: RLS habilitada nas duas tabelas internas; nenhum acesso de
anon/authenticated. O aviso informativo de
[RLS sem política pública](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy)
é esperado nesse registro fechado. O painel só atende 127.0.0.1, protege
os comandos com token local e não expõe a credencial do banco.

## Operação
Pasta: 2-MOTORES/BONIFICADOR/OPERACAO-ESTILOS-V12.
Abrir: ABRIR-CORRETOR-ESTILOS.bat ou Corretor de estilos.exe.
O painel oferece Pausar com segurança, Retomar e Encerrar.
Fechar o navegador não para a execução. O banco decide de onde retomar.
ESTADO-LOCAL/estado.json e recibos.jsonl são locais e ignorados pelo Git.
Não é preciso manter uma conversa de IA aberta; a execução não usa tokens.

## Pendências deliberadamente separadas
Concluir a execução automática, indicada pelo estado do banco.
Depois: atualizar a Máquina 2 e liberar a fila geral V12 com seus contratos.
Os quatro estilos sem ativação definida continuam aguardando extração futura.
Nenhuma alteração foi enviada ao GitHub ou Netlify nesta entrega.
