> Substituído para operação na máquina 2 pelo modelo FILA-LOCAL-MAQUINA-2.md: baixar fila, processar offline e enviar JSONs em lotes por botão separado.

# Correção seletiva de altura e IA — 10/09/2026

## Estado
Contratos instalados, aplicativo compilado e execução iniciada na máquina oficial.
176.306 linhas na auditoria inicial; 53.402 tinham publicação. Isso não significa
conclusão: consultar public.correcao_altura_ia_status_v13 para o estado real.

## Regra vigente
Altura independente: ativa em 1,4,5,6,17,18,19, direção +1, peso 5.
Demais funções: zero. Cortes preservados. As onze outras parcelas físicas ficam
exatamente iguais, inclusive seus resíduos de arredondamento. Não redistribuir.
IA: min(quantidade real de estilos,5)*0,1. Não dividir o bônus antigo pela metade:
o antigo saturava em quatro estilos; o novo satura em cinco.
Pé ruim, estilos de jogo e outros bônus preservados. Otimizador e normalização
oficial não mudam. Amplitude continua exclusivamente no comparativo.

## Persistência e compatibilidade
clube_novo.bonificador_altura_ia_sucessor_v13 liga cada base ao sucessor, registra
as duas parcelas anteriores/novas e impede duplicação. Resultados anteriores não
são apagados. A versão final é v13-1009-altura-ia-v1, contrato bonificador-altura-ia-v13,
fórmula afa495d927fe99730fa154e5d91c227e56c36c51bd048cd8881b688bc2aa126f.
O corpo guarda a soma exata do detalhe; o total do bônus continua arredondado a 4 casas.
corpo_soma/corpo_pct derivados usam a referência física congelada, não novos pesos ativos.

Os writers V6/correção V2 mantêm a validação V12 da entrada e aplicam altura/IA
no banco antes de devolver o ID/selo definitivo. Isso permite a continuidade do
cliente V12 existente sem aceitar resultados finais com a regra antiga.
As implementações anteriores estão preservadas em funções internas, sem acesso público.
O gate de estilos aceita V13 e continua conferindo ativação/parcelas de estilo.

O runtime local mantém cálculo-base neutro. A transformação definitiva ocorre no
writer, com retorno politica_aplicada=altura-ia-v13 e valores finais. Não aplicar
a transformação novamente no cliente; isso inverteria altura duas vezes.

## Executor
Pasta: 2-MOTORES/BONIFICADOR/OPERACAO-ALTURA-IA-V13.
Abrir ABRIR-CORRETOR-ALTURA-IA.bat ou Corretor de altura e IA.exe.
Configuração compartilhada em 2-MOTORES/config.txt; nenhuma credencial no pacote.
Painel local com pausa/retomada/encerramento, recibos em ESTADO-LOCAL, trava contra
duas instâncias. Não usa IA nem depende de Codex. Fechar a aba não interrompe.

Publicação com Otimizador ainda pendente é preservada. O sucessor fica guardado
em aguardando_otimizador; o executor o publica quando a linha estiver pronta.
O aplicativo não declara conclusão enquanto existirem essas pendências.
Não reordenar nem recalcular filas do Otimizador. Manter Bonificador completo
pausado durante a correção; o executor recusa concorrência desse lote.

## Testes
Piloto transacional com rollback: goleiro 2569, Zola 36534 e Ronaldinho 36851.
Onze outras medidas idênticas. Goleiro físico -0,5 -> +0,5; Ronaldinho IA
0,25 -> 0,1 e físico igual; Zola IA 0,5 -> 0,2 e só altura retirada do físico.
Teste inicial persistido: dez resultados, quatro publicações e seis aguardando
Otimizador. Consultar o status para dados atuais, não reutilizar essa contagem como final.

Nenhum deploy de Netlify/GitHub foi solicitado nesta etapa. Avaliações de Boxes
congeladas são históricas e não são reescritas por este executor.
