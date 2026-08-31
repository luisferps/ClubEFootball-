# Estrutura operacional do Bonificador

**Organizada em 28/08/2026.** Esta é a única cadeia de runtime do Bonificador.

```text
2-MOTORES/
├── BONIFICADOR/
│   ├── Bonificador ClubEfootball.exe   único aplicativo abrível do operador
│   ├── motor_bonus.py                  fonte exclusivo do motor
│   ├── interface/                      fonte do componente local
│   └── windows-app/                    fonte/ícone/payload de compilação nativo
└── config.txt                configuração compartilhada dos motores
```

## O que fica onde

- `2-MOTORES/BONIFICADOR/motor_bonus.py` é a única cópia executável do motor.
- `2-MOTORES/BONIFICADOR/Bonificador ClubEfootball.exe` é o único item que o operador
  abre. Ele carrega o componente local incorporado; não há segundo aplicativo na raiz.
- `windows-app/assets/BonificadorComponente.bin` é um payload de compilação, não é
  executável pelo operador. O compilador o incorpora no EXE principal.
- `2-MOTORES/config.txt` permanece comum porque também é procurado/usado pelos
  demais motores. O Bonificador sobe até esse diretório para encontrá-lo; não existe
  cópia de configuração dentro de `BONIFICADOR`.
- O motor importa somente a biblioteca padrão Python (`os`, `sys`, `json`, `time` e
  `urllib`). Não há módulo local do Bonificador para mover ou duplicar.
- Testes, SQL, auditorias, snapshots e rollback ficam em `4-DOCUMENTOS/BONIFICADOR`.
  O manual de funcionamento fica em `4-DOCUMENTOS/MANUAL-DO-BONIFICADOR.md`.

## Integridade e recuperação

O caminho histórico `2-MOTORES/motor_bonus.py` não existe mais e não é usado por
lançador ou import. A única menção operacional restante é uma defesa no
`1-LIMPAR-ANTES-DE-SUBIR.bat`: se uma cópia antiga reaparecer, ela é tratada como cópia
solta e movida ao lixo, nunca executada.

O snapshot de antes do movimento, o hash do arquivo e o rollback reversível estão em
`RECUPERACAO/2026-08-28-ANTES-ORGANIZACAO-OPERACIONAL`. A recuperação move o único
arquivo de volta; ela não restaura nem cria uma cópia paralela.

## Provas de lançamento e paridade

- `TESTES/testar_organizacao_operacional.py` valida localização única, hash, sintaxe,
  ausência de import local e a dependência compartilhada de configuração, sem rede e
  sem escrita.
- `TESTES/testar_lancamento_isolado.py` lança o executável em processo isolado, simula
  régua apta e zero pares e prova que o pipeline não escreve nessa rodada.
- `TESTES/testar_pipeline_incremental.py` prova offline a sequência fila vazia → espera
  → nova linha apta → writer e a recusa de linha incompleta, sem rede, banco ou arquivo.
- `TESTES/testar_migracao_bonificador.py --online` valida as três RPCs e as funções
  puras sem chamar `gravar_bonus`.
- O lote produtivo continua desligado; a projeção de pares está vazia. Não execute o
  motor como teste de organização, pois o executável é deliberadamente o caminho que
  gravaria o lote quando houver pares autorizados.
