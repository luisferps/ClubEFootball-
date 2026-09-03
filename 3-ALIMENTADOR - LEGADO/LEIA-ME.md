# ALIMENTADOR — o aplicativo que leva a coleta para dentro do banco

**Como abrir:** dê dois cliques no `index.html`. Ele abre no Chrome como um
aplicativo — sem Console, sem arquivo solto.

## O que ele faz

```
pasta da coleta  ──►  ALIMENTADOR  ──►  caixa de entrada (clube.recebimento)
   (o coletor grava)                      só ACEITA: ninguém lê o banco por aqui
```

1. **Escolher a pasta** — aponte para `Resultado da Coleta`.
2. Ele lê os lotes já fechados e mostra quantos cards e quantas fotos validadas.
3. **Levar para o banco** — sobe em blocos de 400, com barra de progresso.
4. **A caixa de entrada** — mostra quanto já entrou, quanto foi conferido e
   quanto já passou para a casa.

## O que ele NÃO faz

- não escreve na casa (`clube.carta`, `clube.build`): quem faz isso é a
  conferência, depois;
- não roda motor;
- não apaga nem altera nada na sua pasta.

## Coisas boas de saber

- **Pode rodar com a coleta ligada.** Ele só lê lote fechado.
- **Rodar duas vezes não duplica.** O banco confere `card_id + sha256` e ignora
  o que já tem.
- **Se cair no meio, é só abrir e mandar de novo** — o que já entrou fica.
- A chave usada aqui é a pública, que só consegue ENTREGAR. A chave secreta não
  entra neste arquivo nunca.
