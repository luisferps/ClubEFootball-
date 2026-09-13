# Entrega da retomada completa V12 para a Máquina 2 — 09/09

## Reparo de retomada HTTP 403 e encerramento — 09/09/2026

A execução na Máquina 2 expôs uma permissão ausente na consulta da carta V3, após a preparação já validada. Corrigido o acesso restrito ao catálogo no banco; HTTP e gravação testados. A única falha 488143 foi recuperada, com prioridade preservada. Bonificador agora retorna código 2 em falha e não anuncia conclusão indevida. Novo pacote único `REPARO-MOTORES-V12` inclui também a correção de prioridade do Otimizador; instalar em `2-MOTORES` por `APLICAR.cmd`, preservando os BATs anteriores. Ver `4-DOCUMENTOS/BONIFICADOR/REPARO-RETOMADA-403-V12.md`. Os registros de prontidão anteriores descrevem a conferência parcial daquela etapa.


## Retomada V12 conferida — 09/09/2026

Pacote do Bonificador completo validado (15 arquivos). Retomada, controle e primeira reserva passaram em transação revertida; lote continua pausado, com 14.107 pendentes. Corrigidos no banco o filtro da auditoria e as restrições de versão do lote, agora compatíveis com os conjuntos coerentes V11/V12. Usar o mesmo `OPERACAO-CORRECAO-FISICA/INICIAR-REPROCESSAMENTO.bat`. Nenhuma nova cópia necessária por esses ajustes. Detalhes em `4-DOCUMENTOS/BONIFICADOR/RETOMADA-CONFERIDA-0909.md`.


Usuário autorizou copiar os arquivos atualizados para a pasta espelhada
2-MOTORES/BONIFICADOR da Máquina 2, para iniciar depois da correção seletiva.
São 14.107 itens pendentes: 631 já têm Otimizador concluído e 13.476 ainda o aguardam.

O mesmo INICIAR-REPROCESSAMENTO.bat passa a validar a instalação e consultar
public.bonificador_preparar_retomada_v12 antes de iniciar o lote existente.
Enquanto a correção seletiva não estiver concluída, a RPC devolve liberada=false,
sem alterar política, lote ou item. Ao ser chamada pelo operador após conclusão,
atualiza apenas os metadados V11→V12 do lote, registra os anteriores e ativa
a política geral; depois o controle normal inicia a execução.
Não há ativação automática pelo fim da correção e não há início nesta entrega.

As rotinas de vínculo e reaproveitamento aceitam V12 com estilos conferidos.
A reserva e o writer V12 exigem a versão correta do lote. O controle recusa
início por arquivos antigos. As parcelas de corpo, pé e IA permanecem iguais.

Migração aplicada: preparar_retomada_completa_bonificador_v12_apos_correcao_seletiva.
Fonte: SQL/PREPARAR-RETOMADA-BONIFICADOR-COMPLETO-V12.sql.
Validações: 25 casos manuais de estilo e seis testes do consumidor; fórmula
física preservada (caso Messi 0,975); vínculo V12 conferido em transação revertida;
retomada antecipada devolveu bloqueio sem reservar linha.

Os arquivos são copiados da pasta oficial para uma área de entrega com as mesmas
subpastas do Bonificador. O manifesto SHA-256 acompanha a cópia e é conferido
novamente no início. Configuração e resultados da outra máquina não são incluídos.
