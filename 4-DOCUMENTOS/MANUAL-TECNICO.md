# Referência técnica atual

## Estrutura

| Caminho | Responsabilidade |
|---|---|
| `2-MOTORES` | Núcleo de cálculo, aplicativos, adaptadores e testes |
| `7-VARREDURA-DO-JOGO` | Extrator físico, níveis eFHUB, contrato e provas |
| `8 - EXTRATOR DE FOTOS` | Descoberta, imagens e atualização de URLs |
| `Site Novo` | Frontend, contratos SQL de tela e testes |
| `4-DOCUMENTOS` | Manuais atuais e anexos técnicos |
| `6-AVALIADOR-NO-RAILWAY` | Serviço preservado; uso atual não confirmado |

Os fontes e dependências acompanham os executáveis porque há componentes carregados
externamente e porque a entrega precisa ser reproduzível. Um BAT é um lançador, não
uma versão extra. Filas, recibos, configurações e provas locais não são lixo.

## Autoridades

`clube_novo` contém dados, regras e resultados operacionais. `public` expõe portas
controladas do site. `clube` é legado, sem fallback operacional. A identidade é a
chave real/código físico; texto traduzido é apresentação.

O contrato tipado do Extrator define procedência e leitura. `valor_do_dono` protege
decisões manuais por campo e chave completa. Não inferir orçamento pelo ID como prova.
Não converter dado desconhecido em zero.

Otimizador: núcleo `equacao.py`, `motor.py`, `regua.py`, `fonte_unica.py` e adaptadores
oficiais. Alterações de bytes podem mudar selos; respeitar `.gitattributes` e as
validações de pacote. Bonificador valida entradas/regras, não apenas rótulos de versão.

Normalização vigente: `100 + 50 × motor / (máximo teórico − mínimo teórico) + bônus`.
[Contrato](NORMALIZACAO-0909/AMPLITUDE-VIGENTE.md). Os limites de estrelas e as regras
de cada função vêm do banco; não manter outra tabela concorrente no frontend.

## Referências necessárias

- [Tabelas e contratos](MANUAL-DAS-TABELAS.md).
- [Textos oficiais](MANUAL-DOS-TEXTOS-DO-JOGO.md).
- [Mapa físico](MAPA-DO-CODIGO-DO-JOGO.md).
- [Correções manuais](EXTRATOR/PRIORIDADE-CORRECOES-MANUAIS.md).
- [Regras de habilidades](OTIMIZADOR/HABILIDADES-0909/REGRA-APROVADA.md).
- [Complemento](OTIMIZADOR/COMPLEMENTO-1009/REGRA-APROVADA.md).
- [Altura e IA](BONIFICADOR/ALTURA-0909/EXECUTOR-ALTURA-IA-V13.md).
- [Integração e publicação](MANUAL-DE-INTERLIGACAO-DE-SISTEMAS.md).

As pastas técnicas conservam SQL aplicado, casos de teste, hashes e provas de origem.
São referências de manutenção; nomes datados não indicam tarefas para executar outra
vez. Para saber o que falta, consultar somente [Estado atual](ESTADO-ATUAL.md).

## GitHub e atualização

Repositório oficial: https://github.com/luisferps/ClubEFootball- (`main`).
Antes de publicar, inspecionar o diff e os arquivos ignorados: sem `.env`, chaves,
credenciais DPAPI, arquivos privados do jogo, filas ou resultados locais.
Preservar histórico, fazer commit e push normal e confirmar o HEAD remoto.
Atualização de GitHub não equivale a deploy do site nem atualização da Máquina 2.
Não substituir executáveis ou apagar estados enquanto estão em uso.
