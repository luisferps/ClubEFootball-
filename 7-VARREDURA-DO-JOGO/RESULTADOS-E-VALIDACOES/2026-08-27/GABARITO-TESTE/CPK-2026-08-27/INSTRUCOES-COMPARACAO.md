# Como conferir a recarga completa

1. Abra o novo Extrator ClubEfootball pelo iniciador local.
2. Entre em **Recarga completa de cartas**.
3. Selecione o CPK atual com SHA-256 `44df868c2613d532292d87072c0863a907d6a5f0cc40f914d355e56d74edfcc5`.
4. Selecione `carta_jogo_GABARITO-INTEGRAL.csv` no campo **Gabarito ou base para comparar**.
5. Marque a confirmação, digite `RECARREGAR COMPLETO` e execute.
6. O resultado aceito deve mostrar **gabarito EXATO**, 43072 cartas, 43072 IDs únicos, zero duplicadas e SHA-256 `07c9b8cf9690b1f177cd724ada4329351424b71fb8c6d09e4cd35d3875389c38`.

Se aparecer **DIVERGENTE**, não prepare nem aplique dados. Gere e revise um novo manifesto. Essa conferência não escreve em banco.
