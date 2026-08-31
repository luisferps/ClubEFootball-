# Estado prévio a confirmar

- alvo: contratos privados do Bonificador no `public`, com dados operacionais em
  `clube_novo`;
- esperado antes da aplicação: `bonificador_regua_v1` e `bonificador_carta_v1`
  existentes; `bonificador_contexto_escrita_v2` e
  `gravar_build_bonificador_v1` ausentes;
- alteração vedada: fórmula, pesos, moldes, ordem, Otimizador, Extrator, legado,
  UI visual de outros motores e lote produtivo;
- recuperação preparada: `ROLLBACK-ESCRITOR-TRANSACIONAL-BONIFICADOR-V1-COMPOSAVEL.sql`.

O readback físico e o ensaio com rollback serão registrados após a conexão de banco
confirmar o estado acima. Nenhuma credencial é registrada.
