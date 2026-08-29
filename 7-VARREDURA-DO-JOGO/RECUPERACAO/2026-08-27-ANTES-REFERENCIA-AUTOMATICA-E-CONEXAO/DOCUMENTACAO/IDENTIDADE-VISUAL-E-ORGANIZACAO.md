# Identidade visual e organização — Extrator eFootball

## Identidade final

- Nome no Explorer: `Extrator eFootball.exe`.
- Título da janela: `Extrator eFootball`.
- Símbolo: bola de futebol dentro de uma lupa, seta verde de extração e base de dados azul.
- Fundo: transparente.
- Cores: azul-marinho, azul-ciano, verde-limão e branco, com contraste alto.
- Tamanhos nativos no `.ico`: 16, 20, 24, 32, 40, 48, 64, 128 e 256 pixels.

O ícone foi criado com o gerador de imagens integrado e convertido localmente para um `.ico` multirresolução. Nenhuma API externa, chave ou credencial foi colocada no aplicativo.

### Prompt final usado na arte selecionada

> Crie um único símbolo centralizado para um aplicativo Windows, combinando uma bola de futebol, uma lupa e uma seta clara de extração de dados. Use formas geométricas grossas, fundo realmente transparente, contorno azul-marinho, lupa azul-ciano, seta verde-limão e bola branca. Sem texto, letras, números, marca, jogador ou estádio. Mantenha alto contraste, poucos detalhes e leitura nítida em 16, 24, 32 e 48 pixels.

Arquivos permanentes da identidade:

- `SISTEMA-EXTRATOR\windows-app\assets\icone-extrator-clubefootball.ico`;
- `SISTEMA-EXTRATOR\windows-app\assets\icone-extrator-clubefootball.png`;
- `03-validacao\PREVIA-ICONE-WINDOWS-16-A-64.png`;
- `03-validacao\ICONE-EXTRAIDO-DO-EXECUTAVEL-32PX.png`;
- `03-validacao\VALIDACAO-ICONE-WINDOWS-2026-08-27.json`.

O `.ico` contém todas as nove resoluções e tem SHA-256 `0e59b5429be34dd6bef3983b9a053d02b2608166a85557ba1fb134f444e25cb1`. O ícone extraído do executável instalado é diferente do ícone do lançador anterior, provando que o recurso foi incorporado ao arquivo real e não apenas ao HTML.

O nome físico confirmado é `Extrator eFootball.exe`. Em instalações do Windows que ocultam extensões conhecidas, o Explorer mostra apenas `Extrator eFootball`; isso é a apresentação normal do Shell e não altera o nome real do arquivo. A validação registrou tipo `Aplicativo`, nome e descrição do produto `Extrator eFootball`, um único lançador visível e o ícone nativo extraído.

## Organização da pasta operacional

Na visão normal do Explorer, a raiz contém:

```text
7-VARREDURA-DO-JOGO\
├── Extrator eFootball.exe
├── DOCUMENTACAO\
├── RESULTADOS-E-VALIDACOES\
└── RECUPERACAO\
```

Os componentes técnicos necessários continuam na raiz com atributo oculto. Nenhum arquivo do jogo, gabarito, prova, manual, relatório ou versão de recuperação foi apagado.

Movimentos e renomeações realizados:

- `ABRIR-EXTRATOR-CLUBEFOOTBALL.exe` → `RECUPERACAO\2026-08-27-ANTES-ICONE-E-NOME`;
- novo lançador → `Extrator eFootball.exe`;
- `VERSOES-ANTERIORES` → `RECUPERACAO`;
- `ENTREGAS` → `RESULTADOS-E-VALIDACOES`;
- `COMO-ABRIR.md` e arquivos legados soltos → `RECUPERACAO\ARQUIVOS-LEGADOS-DA-PASTA`;
- instrução atual → `DOCUMENTACAO\COMO-USAR.md`;
- cache temporário do executor → `RECUPERACAO\ARQUIVOS-TEMPORARIOS-RETIDOS`.

Remoções definitivas: nenhuma. Itens ambíguos ou temporários foram retidos em recuperação.
