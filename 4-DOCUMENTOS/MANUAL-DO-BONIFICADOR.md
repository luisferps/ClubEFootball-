# Manual do Bonificador

O Bonificador calcula as parcelas de corpo, altura, pé, estilos e IA previstas nas
regras do sistema. Não escolhe técnico nem distribui evolução; isso é do Otimizador.
Mudar técnico ou molde não obriga, por si só, a recalcular bônus compatíveis.

## Operação atual

Abra `2-MOTORES/BONIFICADOR/Bonificador ClubEfootball.exe`.
Na aba **Lote integral atual**:

1. **REAPROVEITAR CONFORMES** confere entradas e regras atuais e reaproveita resultados
   compatíveis. Nome ou número antigo da versão não determina sozinho a validade.
2. Ao terminar a conferência, **CALCULAR EXCEÇÕES** calcula o que falta ou diverge.
   Cartas novas nunca bonificadas entram aqui, não no reaproveitamento.
3. **ATUALIZAR** relê o progresso. **PARAR APÓS A FATIA** termina a fatia corrente;
   as fatias concluídas permanecem salvas para retomada.

Não iniciar outro Bonificador sobre a mesma operação. A conferência não significa
rebonificar todo mundo. Reuso conserva prova da origem, mas a nova linha tem sua
identidade e seus próprios registros. Não inventa bônus para cartas novas.

Bonificador e Otimizador podem rodar em paralelo. Bônus pronto pode aguardar o
Otimizador; resultado do Otimizador recebido pode aguardar bônus. Nenhuma dessas
esperas, isoladamente, prova falha ou publicação concluída.

## Regras essenciais

- Estilo principal é definido pela função; ativação é definida pela posição da build.
  Principal ativo vale 1,0 e secundário ativo 0,5. Básico/inativo vale zero. Não promover
  genericamente o secundário. Há duas exceções específicas: Defensor criativo e
  Lateral defensivo, com alcance no [contrato de estilos](BONIFICADOR/REGRA-ESTILOS-APROVADA-0909.md).
- Corpo usa medidas, direções e cortes canônicos. Direção zero não contribui; os cortes
  e pesos não devem ser reconstruídos a partir de nomes ou de exemplos de jogadores.
- Altura é parcela independente nas sete funções aprovadas, sem redistribuir os pesos
  das outras medidas. IA vale 0,1 por estilo até 0,5, conforme política V13.
  [Altura e IA](BONIFICADOR/ALTURA-0909/EXECUTOR-ALTURA-IA-V13.md).
- Pé usa a frequência e a precisão canônicas; não inferir esses dados por overall.
- Publicação aplica a normalização vigente e soma o bônus completo. Mudanças de
  valorização precisam ser iguais no motor, nos writers e no editor do site.

## Banco e conferência

O contexto vigente é `bonificador_contexto_fila_v7`; o writer é
`gravar_build_bonificador_v6`. Somente `clube_novo` é operacional. Não buscar resultados
legados para contornar entrada faltante. O servidor valida a composição e os selos.

Filtre cartas disponíveis antes de contar pendências. Carta excluída não representa
falta de bônus. Carta sem orçamento divulgado aguarda a fonte; não deve receber
orçamento zero artificial para entrar no motor.

Concluir a rodada exige conferir a população elegível, as exceções, os erros e os
resultados persistidos. Concluir publicação exige ainda a leitura pública da linha
composta. [Estado único da implantação](ESTADO-ATUAL.md).

Os demais painéis de lote, fila de resultados, teste de carta e auditoria servem ao
acompanhamento e diagnóstico. Não iniciar executores corretivos históricos por causa
de uma contagem antiga num documento. Configuração e credenciais permanecem locais.
