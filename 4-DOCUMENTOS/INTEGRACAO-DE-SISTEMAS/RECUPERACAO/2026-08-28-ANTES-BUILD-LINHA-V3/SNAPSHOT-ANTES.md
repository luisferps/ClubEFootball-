# Snapshot antes da Build Linha V3

Data: 2026-08-28

- As nove tabelas do desenho V2 estavam vazias.
- `clube_novo.build_carta` já havia sido removida.
- O desenho V2 permitia apenas uma Build ativa por `card_id` e foi revogado pela definição de linha por carta, função e posição.
- Nenhum motor, UI ou lote estava conectado às tabelas.
- A recuperação segura da V3 remove as três novas tabelas; o modelo V2 não é restaurado como runtime porque foi explicitamente revogado.

