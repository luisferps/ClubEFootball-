# Investigacao local do LiveData - 31/08/2026

## Conclusao direta

Os nove arquivos presentes em `C:\ProgramData\KONAMI\eFootball\ST\TempData\Download` foram abertos com sucesso, sem iniciar o jogo e sem alterar os originais. Todos sao PNGs de interface/promocao: oito banners de `1638 x 414` e um retrato de `534 x 726`. Eles nao sao CPK, PAK, UTOC, UCAS, tabela de cards nem catalogo de metadados.

O manifesto estrutural instalado continua sendo o de `27/08/2026`, versao `2026082701`, para o aplicativo `6.0.0`. Ele aponta para `dt870_console_win.cpk` e para 14 grupos `pc9242` a `pc9255`. Os tamanhos e SHA-256 de todos os 43 arquivos fisicos (`1 CPK + 14 PAK + 14 UCAS + 14 UTOC`) conferem exatamente com o manifesto. Nao existe entrada `pc9256` ou posterior no manifesto atual.

Portanto, a atualizacao observada em 31/08 baixou artes temporarias de campanhas e ativou/apresentou conteudo; ela nao depositou nesses nove temporarios um novo catalogo estruturado para o Extrator. Um card exibido em uma dessas artes e apenas imagem. Os dados estruturados do card precisam vir de um pacote LiveData ja instalado ou de uma resposta online do servidor. Como os Japanese Stars ja tinham sido encontrados no `dt870` de 27/08 em auditoria separada, este caso e compativel com ativacao pelo servidor mais imagens de apresentacao.

## Como os nove arquivos foram abertos

O executavel auditado foi:

- Caminho: `C:\Program Files (x86)\Steam\steamapps\common\eFootball\eFootball\Binaries\Win64\eFootball.exe`
- Tamanho: `352409088` bytes
- SHA-256: `a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4`

A cadeia estatica comprovada no PE e:

1. O inicializador em RVA `0x4774272` obtem o vetor gerado em `0x46E20C0` e o entrega a `OnlineSystemHttpAes` em `0x480DA10`.
2. O vetor e inicializado em RVA `0x46E28B7`: objeto ofuscado em RVA `0x6E6FA70`, funcao de derivacao em RVA `0x46E1C00`, destino global em RVA `0x86D52A8`.
3. As 32 operacoes XOR da funcao produzem a chave AES-256 `43740981523cdc171e71de2ccab1a5a9b86f4b833196c55facd4bd25846c33f5`.
4. A rotina em RVA `0x480DAA0` exige mais de 16 bytes, separa os primeiros 16 bytes e exige que o restante seja multiplo de 16. A reproducao que valida todos os arquivos e: AES-256-CBC, primeiros 16 bytes como IV, restante como texto cifrado e retirada de padding PKCS#7.
5. Nos nove casos, o padding e valido e o resultado tem assinatura, IHDR e IEND de PNG validos.

Ha ainda uma validacao independente muito forte do formato: os 64 caracteres antes do ponto em cada nome sao exatamente o SHA-256 do PNG decifrado. O numero depois do ponto e um horario Unix exatamente 3.600 segundos depois da gravacao fisica do temporario, compativel com prazo de cache de uma hora; ele nao e nome de tabela nem identificador de card.

## O que existe visualmente nos nove PNGs

| SHA inicial | Dimensao | Conteudo visivel |
|---|---:|---|
| `03e4168c` | 1638 x 414 | Fundo abstrato azul/roxo, sem texto e sem card. |
| `439fe8ba` | 1638 x 414 | Banner `That Time I Got Reincarnated in PES`. |
| `a026b4c5` | 1638 x 414 | Arte com card 98 CMF de Thiago Alcantara e `Exp. 4,000 x6`. |
| `b3da26cc` | 1638 x 414 | `Special Login Present / Campaign Hub`, miniaturas de cards e Frank Lampard com `Overload`. |
| `b6182d6d` | 1638 x 414 | Montagem promocional de Lionel Messi/Barcelona. |
| `cbe51825` | 1638 x 414 | Arte com card RWF 94 de Burchett, `Acceleration Burst` e `Rank 1-50,000`. |
| `cc1d3922` | 1638 x 414 | `KONAMI ID Link Campaign` e premio exibido de 3.000 moedas. |
| `cf3bbaab` | 534 x 726 | Retrato de jogador em uniforme vermelho; a imagem nao informa o nome e ele nao foi inferido. |
| `d80c5011` | 1638 x 414 | Montagem promocional de Lamine Yamal/Barcelona. |

Os unicos tipos de bloco encontrados nos PNGs foram `IHDR`, `sBIT`, `PLTE`, `tRNS`, `IDAT` e `IEND`. Nao ha bloco textual, arquivo embutido, JSON ou tabela. As miniaturas e nomes vistos acima sao pixels da arte.

## Manifesto LiveData estrutural

O arquivo `C:\ProgramData\KONAMI\eFootball\ST\Download\version.bin` tem:

- Tamanho: `4404` bytes
- SHA-256 cifrado: `c6e01db4d3de2fad2d8d94bd1ed995685c18e5acd3275f3826a8516c606213c3`
- Data fisica UTC: `2026-08-27T07:08:04.6641441Z`

O PE mostra as chaves de esquema `version`, `targetAppVersion`, `dt870Hash`, `dt870FileSize`, `dt880`, `name`, `hash`, `ucas`, `utoc`, `hashFileSize`, `ucasFileSize` e `utocFileSize`. A leitura/escrita em RVA `0x46A9B90`/`0x46A9DC0` constroi `VernamCipher` em RVA `0x4A0BA30` com semente `0x5FDFBB52DC46AEE8`, transforma os bytes em `0x4A0BA90` e produz o byte de fluxo em `0x4A0BB80`.

O JSON decifrado informa:

- `version = 2026082701`
- `targetAppVersion = 6.0.0`
- `dt870Hash = 44df868c2613d532292d87072c0863a907d6a5f0cc40f914d355e56d74edfcc5`
- `dt870FileSize = 9415400`
- `dt880 = pc9242 ... pc9255` (14 entradas)

O readback fisico deu `43/43` tamanhos corretos e `43/43` SHA-256 corretos. Isso prova que o manifesto e os pacotes instalados sao coerentes; nao prova, por si so, que todo conteudo remoto possivel ja esteja no disco.

## Cadeia de classes e caminhos

O RTTI local confirma `LiveDataManager`, `LiveDataDownloader`, `LiveDataLoader`, `LiveDataVersionLoader`, `LiveDataHashChecker`, `LiveDataValidChecker`, `LiveDataBinder`, `LiveDataInfo`, `CommandObjectCmdGetLivedata`, `OnlineSystemHttpAes` e `OnlineSystemHttpBlowfish`. Tambem foram localizados `BindCpk` e `BindPak` no fluxo do binder.

As referencias estaticas ligam:

- `CmdGetLivedata.php`, `version_file` e `livedata_list` ao fluxo do comando online;
- `Download/` aos pacotes persistentes;
- `TempData/Download/` ao cache HTTP temporario;
- `.pak`, `.ucas` e `.utoc` ao carregamento/binding de pacotes.

As importacoes do PE incluem WinHTTP/WinINet e geracao/hash criptografico do Windows, mas nao expoem uma funcao importada que, sozinha, identifique o esquema. A prova do AES usado aqui vem do RTTI/fluxo interno, da chave reconstruida e da decifragem integral dos nove arquivos.

## Reproducao segura

Executar a partir de `7-VARREDURA-DO-JOGO`:

```powershell
# Reconstrui a chave diretamente do executavel, em somente leitura.
python .\artefatos\investigacao-livedata\reconstruir-chave-http-aes.py

# Confere os temporarios inteiramente em memoria, sem criar PNGs.
& .\artefatos\investigacao-livedata\abrir-tempdata-livedata.ps1 -InspectOnly

# Decodifica o manifesto para a tela, sem gravar no diretorio do jogo.
python .\artefatos\investigacao-livedata\decodificar-version-bin.py
```

Para preservar copias derivadas fora do jogo, informar uma pasta vazia do checkout em `-OutputDirectory`. O script recusa sobrescrever arquivos existentes e verifica SHA-256, tamanho e data de modificacao dos originais antes/depois.

Os resultados desta rodada estao em:

- `artefatos/investigacao-livedata/pngs-20260831/manifesto-auditado.json`
- `artefatos/investigacao-livedata/pngs-20260831/manifesto-auditado.csv`
- `artefatos/investigacao-livedata/version-bin-20260831.json`
- `artefatos/investigacao-livedata/verificacao-pacotes-version-bin-20260831.json`
- `artefatos/investigacao-livedata/identificacao-visual-20260831.json`
- `artefatos/investigacao-livedata/evidencia-rtti-livedata.txt`
- `artefatos/investigacao-livedata/evidencia-xrefs-textos.txt`
- `artefatos/investigacao-livedata/evidencia-desmontagem-aes.txt`
- `artefatos/investigacao-livedata/evidencia-desmontagem-version-bin.txt`
- `artefatos/investigacao-livedata/evidencia-imports-relevantes.txt`
- `artefatos/investigacao-livedata/evidencia-strings-crypto-livedata.txt`

## Limites e proximo ponto de observacao

Os nove temporarios foram completamente identificados e podem ser descartados como fonte de tabelas estruturadas. Se aparecer na tela um `card_id` realmente ausente do `dt870`/`pc9242...pc9255`, a proxima fonte a observar e a resposta online que monta box/campanha (por exemplo, o fluxo do comando de dados do modo), ou um futuro `version.bin` com novo `dt870`/`pcNNNN`. Nao se deve tentar transformar texto ou miniatura desses banners em registro de banco.

Nenhum arquivo do jogo foi modificado, copiado ou apagado; somente artefatos derivados foram gravados dentro do checkout operacional. O jogo nao foi executado e nenhum banco de dados foi acessado.
