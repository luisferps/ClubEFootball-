# Checkpoint da Reforma A — 04/09/2026

Status: registro documental recebido; nenhuma escrita ou nova validação foi executada no banco nesta etapa.

Fonte integral recebida:

`C:\Users\Luis Fernando\.codex\attachments\bd701a6c-7f6f-4952-808e-c0abab47fbf6\pasted-text.txt`

SHA-256 da fonte: `2E1280DCD407152A3A84ACDF6237E7E694C334812E638FCD2A4A3D9B628122B6`

Este documento registra o estado informado da Reforma A. Como `clube_novo` estava sendo alterado durante a reconstrução, os fatos abaixo formam um checkpoint datado; eles devem ser revalidados antes de conexão, migração ou publicação posterior.

## 1. Migrações registradas

Ordem recebida:

1. `20260904201650 a_nota_vai_para_a_linha_parte_1_colunas`
2. `20260904201701 a_nota_vai_para_a_linha_parte_2_carga`
3. `20260904201858 a_nota_vai_para_a_linha_parte_3_views`
4. `20260904201950 a_nota_vai_para_a_linha_parte_3b_ficha_e_lista`
5. `20260904202722 a_nota_vai_para_a_linha_parte_4_degraus_e_drop`

## 2. Contrato atual informado

- `clube_novo.build_pontuacao_normalizada_v2` não existe mais.
- As notas fechadas moram na própria linha de build em `clube_novo.build_linha_card`.
- `build_otimizador` e `build_bonificador` continuam separados nesta Reforma A.
- As 24 colunas de nota são colunas normais, não geradas ou recalculadas automaticamente pelo banco.
- `nota_final` é a única nota que a tela deve exibir.
- `nota_final` é gravada uma vez pela publicação; o banco não recalcula e a tela não recalcula.
- a finalizadora canônica por linha passou a gravar na linha a partir do vetor real do motor.
- `frontend_degraus_da_linha_v1`, as três views e a lista pronta foram recriadas para ler a linha, mantendo os nomes e grants informados.

### 2.1 As 24 colunas `nota_*`

1. `nota_contrato`
2. `nota_otimizador_resultado_fingerprint`
3. `nota_bonificador_resultado_fingerprint`
4. `nota_carta_fingerprint`
5. `nota_formula_fingerprint`
6. `nota_contrato_fingerprint`
7. `nota_bruta_selada`
8. `nota_bonus_pe`
9. `nota_bonus_fisico_total`
10. `nota_bonus_posicao`
11. `nota_bonus_playstyle_1`
12. `nota_bonus_playstyle_2`
13. `nota_bonus_ia`
14. `nota_bonus_outros`
15. `nota_bonus_total`
16. `nota_numerador`
17. `nota_denominador`
18. `nota_do_motor`
19. `nota_final`
20. `nota_normalizacao_fingerprint`
21. `nota_calculo_fingerprint`
22. `nota_publicacao_fingerprint_v1`
23. `nota_publicada_em_v1`
24. `nota_calculada_em`

## 3. Evidência de integridade recebida

Conferência informada antes do drop:

| Medição | Resultado recebido |
|---|---:|
| Linhas na tabela antiga | 55.757 |
| Linhas com nota em `build_linha_card` | 55.757 |
| Divergências entre as duas fontes | 0 |

A remoção da tabela separada foi informada como posterior a essa conferência. Nenhuma linha teria sido apagada pelas cinco migrações.

## 4. Evidência pública recebida

Testes informados no papel do visitante, todos sob teto de 3 segundos:

| Leitura | Resultado recebido |
|---|---:|
| Lista, primeira página | 500 linhas |
| Lista, última página | 430 linhas |
| Lista de uma função | 500 linhas |
| Ficha de um card | 16 linhas |
| Estado do card | publicada |

Topo de ranking informado no checkpoint:

1. Neymar — 114,19
2. Modrić — 112,83
3. Messi — 112,56

Esses números são evidência recebida do checkpoint de 04/09, não uma medição refeita por esta documentação.

## 5. Contrato da nova Ficha

A nova Ficha deve manter estas fronteiras:

```text
contrato público versionado
        ↓
SupabaseFichaAdapter
        ↓ valida versão, publicação e tipos
FichaViewModel.notaFinal
        ↓
componente visual exibe o valor recebido
```

Regras obrigatórias:

- o adaptador é de leitura e versionado;
- a página não consulta `clube_novo.build_linha_card` diretamente;
- o adaptador recebe `nota_final` de um contrato público aprovado e apenas valida/mapeia o valor;
- `FichaViewModel.notaFinal` representa `nota_final`, sem soma, normalização, arredondamento de composição ou fallback;
- sem publicação válida ou sem `nota_final`, a Ficha mostra estado indisponível/bloqueado;
- as outras 23 colunas de nota são proveniência/selos do resultado, não números concorrentes para escolher na tela;
- nenhuma fórmula, função de ranking ou regra antiga entra no componente visual;
- degraus e listas chegam prontos do contrato de leitura; a tela não os recompõe.

O nome e o retorno exatos do contrato público novo ainda precisam de aprovação. A arquitetura não fica acoplada diretamente às views atuais.

## 6. Ordem operacional preservada

Esta ordem é bloqueante:

1. recuperar/subir os números das **2.721 builds** ainda sem os números;
2. confirmar que o ranking voltou a **55.757** linhas/resultados esperados;
3. somente depois considerar a junção de `build_otimizador` e `build_bonificador` em `build_linha_card`.

Não executar, propor como próxima ação imediata nem preparar agora a junção das duas tabelas. A recuperação dos números e a confirmação do ranking vêm primeiro.

## 7. Superfície escritora para migração futura

As dez funções informadas que hoje escrevem nas duas tabelas separadas são:

1. `otimizador_producao_concluir_linha_v6`
2. `otimizador_producao_importar_json_local_v1`
3. `otimizador_completar_vals_v1`
4. `otimizador_producao_concluir_linha_v3`
5. `otimizador_concluir_linha_teste_v1`
6. `otimizador_concluir_linha_teste_v2`
7. `bonificador_gravar_resultados_v1`
8. `gravar_build_bonificador_v3`
9. `gravar_build_bonificador_v4`
10. finalização/publicação automática por linha

Essa lista é somente o inventário da superfície que precisará ser migrada no futuro. Nenhuma dessas funções foi alterada, chamada ou reescrita nesta etapa.

## 8. Junção futura — fora do escopo atual

O checkpoint informa ligação 1:1, sem órfão: 57.950 resultados de motor para 57.950 linhas e 57.950 bônus para 57.950 linhas, sem sobra dos dois lados.

Quando houver autorização futura, a junção deverá migrar para `build_linha_card` os campos do motor e do bonificador, reescrever e testar individualmente as dez funções com chamadas reais e somente apagar as duas tabelas antigas por último. Isso não é plano de execução atual.

## 9. Declaração desta atualização

- nenhuma consulta ou escrita foi feita no Supabase;
- nenhuma migração foi executada;
- nenhuma junção foi proposta para execução imediata;
- nenhum arquivo fora de `Site Novo` foi alterado;
- este checkpoint documenta a Reforma A recebida e suas restrições operacionais.
