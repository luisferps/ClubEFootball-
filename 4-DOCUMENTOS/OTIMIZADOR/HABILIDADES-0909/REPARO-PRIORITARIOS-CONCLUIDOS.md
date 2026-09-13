# Reparo da validação de lotes prioritários concluídos — 09/09/2026

A seleção mantinha corretamente dois lotes prioritários antigos em lotes_sem_pendentes. A montagem pulava esses pacotes, mas a validação exigia que todos os prioritários estivessem montados e abortava com “lotes prioritários inválidos para a fila ativa”.

O processador agora valida as prioridades contra a seleção completa antes de tocar nos resultados. Apenas para executar, exclui as prioridades que a fotografia já confirmou sem pendências. A FILA-ATIVA.json, a ordem, os lotes e o histórico permanecem intactos. Prioridades desconhecidas ou repetidas continuam rejeitadas.

Fonte e EXE oficiais atualizados. Passaram 15 testes de prioridade e 21 da operação local. O instalador e o EXE foram executados em espelho isolado, sem acesso ao banco: fila concluída aceita, código zero, seleção e resultado sentinela preservados. O pacote consolidado REFILA-V12 também foi atualizado para não restaurar a falha numa futura instalação.

Entrega incremental: REPARO-PRIORIDADE-V12, dois arquivos (bin/OperacaoLocalJson.exe e programas/operacao_local_json.py). Colar a pasta em OPERACAO-LOCAL-JSON e abrir APLICAR.cmd. Faz backup, não renova fotografias, não consulta banco e não inicia motor/enviador. Os BATs principais permanecem os mesmos. A instalação na Máquina 2 depende de o operador executar esse reparo; não foi presumida a partir do teste local.


## Enviador e critério de encerramento V12 — 09/09/2026

O critério aprovado é terminar com toda linha vigente correta e gravada em `clube_novo`, reaproveitando o que já está correto e refazendo somente o necessário. Não declarar encerramento a partir de instalação, JSON local ou ausência de linhas elegíveis de um lote. Preservar históricos, antecessores e a ordem existente. A normalização permanece inalterada.

O operador confirmou a instalação do reparo anterior `REPARO-MOTORES-V12` (backup `motores-retomada-v12-9866126a7fa84046b2e713e53878ce31`). O **novo REPARO-ENVIADOR-V12** corrige a leitura de fotografias antigas e preserva JSONs de outra fórmula sem enviá-los. Atualiza fonte e EXE com backup; mesmos BATs. 44 testes e instalador/EXE conferidos. A instalação deste novo reparo na Máquina 2 ainda não foi confirmada.

Correção de terminologia dos registros anteriores: `lotes_sem_pendentes` significa **sem linhas elegíveis na fotografia atual**, não necessariamente lote inteiro concluído. Dos 1.220 IDs antigos, 1.138 têm resultado e 82 já estão no prefixo. Os demais seis lotes têm 126.318 elegíveis esperando V12. Os 28 antecessores com bloqueios já têm substitutas V12; as seis exclusões anteriores por falta de evidência são cartas removidas, sem publicação. Não reabrir antecessores nem inventar entradas de cartas removidas.

Detalhes e limites da conferência: `4-DOCUMENTOS/OTIMIZADOR/HABILIDADES-0909/AUDITORIA-ENVIO-E-COBERTURA-V12.md`. Esta auditoria foi somente leitura; não declara que a produção ou o envio terminaram.
