# ClubEfootball — a pasta do sistema novo

Tudo que nasceu da reforma da arquitetura de 16/08/2026 mora aqui dentro, e só aqui.
A pasta de cima (a do motor) continua como estava.

---

## 🔴 O DESTINO DESTA PASTA — decisão do Luis, 16/08 às 01h10

> *"no final a gente vai juntar todos os arquivos, inclusive os da pasta anterior,
> dentro dessa. E essa pasta aí vai valer."*

Ou seja: **a V7 não é uma pasta auxiliar. Ela é o sistema, a partir da mudança.**
No fim da reforma, o que presta da pasta de cima vem para cá, e a de cima vira histórico.

**Por isso nenhum programa daqui crava caminho.** Cada um **procura** o `config.txt`:
olha na própria pasta, e se não achar sobe um nível. Assim ele funciona **hoje**
(com o `config.txt` lá em cima) e **depois da mudança** (com ele aqui dentro), sem
ninguém precisar lembrar de editar nada.

⛔ **Regra para quem escrever programa novo aqui:** nunca escrever `cd ..` nem
`os.path.dirname(AQUI)` cravado. Sempre procurar. É a diferença entre a mudança ser
um arrastar de arquivos e ser uma noite de conserto.

---

## COMO RODAR — a ordem

| ordem | o que | onde |
|---|---|---|
| 1 | Abrir `CRIAR-TRADUTOR-NO-SUPABASE.html`, clicar no botão e colar no Supabase | uma vez só, é sua |
| 2 | Duplo clique em `SUBIR-TRADUTOR.bat` | aqui nesta pasta |

Os `.bat` daqui **trabalham na pasta de cima** de propósito: o `config.txt`, o
`CHAVES.json` e a pasta `dados\` moram lá. Eles sobem um nível sozinhos — é só dar
o duplo clique, não precisa mover nada.

---

## O QUE TEM AQUI

| arquivo | o que é |
|---|---|
| `CRIAR-TRADUTOR-NO-SUPABASE.html` | o comando que cria a tabela de tradução e as colunas novas das funções. Tem botão de copiar e o passo a passo. |
| `SUBIR-TRADUTOR.bat` | o duplo clique que preenche tudo |
| `subir_tradutor.py` | o programa que o `.bat` chama |

---

## O QUE ISTO FAZ, EM UMA FRASE

Leva o `CHAVES.json` — o tradutor que foi feito em **14/08** e que **nenhum programa
lia** — para dentro do banco, e dá às 19 funções um **código fixo** que nunca muda,
com o nome de tela ao lado.

Assim o nome da função passa a ser **rótulo**, não chave. Hoje ele é chave, e é por isso
que ele precisa ser trocado em cinco lugares na mão toda vez que muda.

---

## ⛔ O QUE ESTES PROGRAMAS NÃO FAZEM

- **Não apagam nada.** Nenhuma tabela, coluna ou linha.
- **Não trocam nenhuma chave.** A coluna `nome` das funções continua sendo a chave,
  exatamente como está hoje.
- **Não tocam em nenhuma linha de pontuação.**

A troca da chave — do nome para o código — é o único passo perigoso da reforma:
mexe em **11.115 linhas de resultado, 936 de molde e 144 de estilo**, e as três
apontam para o nome com **apagamento em cascata**. Esse passo se faz com o Luis
acordado, olhando, com backup fresco. Não está em nenhum `.bat`.

---

## AS TRAVAS QUE O PROGRAMA TEM

1. Antes de escrever qualquer coisa, ele lê as funções do banco e compara com a tabela
   dele. **Sobrou ou faltou uma? Ele para e não sobe nada** — e diz qual.
2. Confere os 19 códigos contra o `CHAVES.json`. Algum não existe lá? Para.
3. No fim ele **relê do banco** e mostra quantas funções ficaram com código e quantas
   linhas de tradução entraram, por assunto.
4. E lista **o que ainda falta medir**: as 7 habilidades sem par conferido, os 16 estilos
   de jogo, os 15 ímpetos órfãos e a chave da box. Buraco fica marcado como buraco —
   nenhum é preenchido por chute.

---

## ⚠️ SOBRAS NA PASTA DE CIMA

Estes três foram gravados por engano na raiz antes desta pasta existir, e são
**cópias velhas** dos que estão aqui. **Podem ser apagados:**

```
subir_tradutor.py
SUBIR-TRADUTOR.bat
CRIAR-TRADUTOR-NO-SUPABASE.html
```

*(a ponte do computador só sabe gravar arquivo, não sabe apagar — por isso ficou
para o Luis apagar ou para o programa da pasta limpa levar embora)*
