# Snapshot anterior — catálogo físico no contrato

- Data: 29/08/2026
- Schema operacional: `clube_novo`
- `to_regclass('clube_novo.contrato_leitura_catalogo_fisico')`: `null`
- SHA-256 da definição anterior de `clube_novo.obter_pedido_leitura_tipado_ativo()`: `174c8fcdeee159a1a180c31ea16a6d41254cb904216e20c06a54b903697a7639`
- Dados do jogo, cartões, relações, snapshots de conteúdo, motor, UI visual e legado: não alterados.

O rollback restaura a função à forma com política de revisão e remove somente a
tabela/linhas de mapeamento físico desta fase.
