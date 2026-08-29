# Contrato de validação final do Extrator

Este documento é a lista fixa para a validação final. Não basta uma tarefa informar que atualizou o Extrator: depois que todas as frentes forem concluídas, o Extrator deverá ler novamente os arquivos atuais do jogo e cada item abaixo deverá ser conferido contra o banco `clube_novo`.

## Regra de aprovação

Cada item deve passar nestas três comparações:

1. o arquivo atual do jogo contém o dado;
2. o Extrator lê o mesmo dado a partir desse arquivo;
3. o banco recebe o mesmo dado na tabela e relação corretas, sem órfãos.

Falha em qualquer uma das três reabre a frente responsável. Nenhuma frente é aprovada por relatório ou por contagem isolada.

## Técnicos — encerrada, ainda entra na validação final

- Cada versão de técnico deve manter seu identificador próprio.
- O Extrator deve reler: idade, nacionalidade, afinidade, estilos de jogo, proficiências e boosts.
- Sobreposição deve ser relida como estilo de jogo: a amostra obrigatória é Antônio Conte, com proficiência 96.
- A amostra de controle é Fabio Capello, sem Sobreposição.
- Link-up está fora deste escopo e não será cobrado nesta validação.

## Textos — encerrada, ainda entra na validação final

- O Extrator deve localizar o arquivo oficial de textos em português e reler as chaves oficiais de texto.
- A tabela central de textos deve receber os textos com a mesma chave do jogo.
- Catálogos que mostram nome, sigla ou descrição devem resolver os textos apenas pela tabela central, sem fallback para o legado.
- A leitura integral deve encontrar **11.679 textos** e **11.679 chaves oficiais únicas** (`secao`, `id_texto`), com zero duplicidade.
- As **11.679 linhas** devem conservar a procedência física integral: origem, arquivo, CPK, offsets, medidas físicas, fingerprints, presença na fonte e instante de extração conforme o contrato instalado.
- As **166 referências de catálogo** devem resolver pela chave oficial composta em `clube_novo.texto_do_jogo`.
- A validação deve encontrar **zero referência de catálogo sem texto**.
- As **oito FKs compostas** de texto devem existir e estar validadas: atributo, estilo de IA, habilidade, ímpeto, pé, playstyle, sigla de posição e nome de posição.
- A comparação automática da leitura atual do Extrator contra `clube_novo.texto_do_jogo` deve terminar com **zero novas, zero alteradas e zero ausentes** para a fonte vigente.

## Dimensões das cartas — em aberto

- O Extrator deve reler, para cada carta: nacionalidade/região, clube, liga/categoria e tipo de carta.
- Nacionalidade deve usar o catálogo compartilhado `nacionalidade_jogo`, quando a compatibilidade física já comprovada for mantida.
- Amostra obrigatória: Neymar Jr, com Brasil, Santos, Brasileirão Betano e o tipo de carta exibido na tela.
- Cada rótulo de tipo de carta precisa ter ponte comprovada entre código físico e texto oficial antes de entrar no banco.

## Ímpetos — em aberto

- O Extrator deve reler os dois slots de ímpeto de cada carta, incluindo vaga real.
- Cada ímpeto deve resolver seus atributos afetados, efeito máximo, tipo, ativação e faixas de efeito.
- País, clube e liga são relações distintas quando usados como condição; nunca texto livre ou inferência pelo nome.
- Amostras obrigatórias: Vózinha para efeito sempre ativo; Messi para Proteção de posse por nacionalidade; Neymar Jr para Pacote completo por ligas brasileiras.

## Execução final

Quando todas as quatro frentes estiverem concluídas, executar uma leitura nova do jogo e gerar um relatório único com, para cada frente:

- campos e relações exigidos;
- contagens esperadas e encontradas;
- amostras obrigatórias;
- diferenças encontradas;
- resultado: aprovado ou reabrir a frente.

O relatório final só será aprovado se não houver campo faltante, relação órfã, amostra divergente ou dado que o Extrator deixou de reler.
