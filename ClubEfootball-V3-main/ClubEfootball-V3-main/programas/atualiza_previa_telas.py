"""Atualiza somente a camada da ficha na previa ja gerada.

Uso de desenvolvimento quando a casca-fonte (arquivo grande e ignorado) nao
esta presente na copia de trabalho. Nao altera dados nem remonta o Encaixe.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import telas


def atualiza(caminho):
    texto = open(caminho, encoding='utf-8').read()
    bloco = telas.js_telas()
    m = re.fullmatch(r'\s*<script id=TELAS_1808_JS>\s*(.*?)\s*</script>\s*',
                     bloco, flags=re.S)
    if not m:
        raise RuntimeError('a fonte telas.py nao devolveu o script esperado')
    miolo = m.group(1)
    css = telas.CSS_TELAS

    # A previa antiga ja continha uma copia da camada dentro do script
    # principal, antes do bloco com id. Essa e a copia que o navegador de fato
    # executa. Atualizar somente o bloco com id mudava o HTML desenhado, mas os
    # cliques continuavam presos na regra velha. Substitui a PRIMEIRA camada
    # ativa e elimina todas as copias inertes posteriores.
    marca = '/* O MOTOR DO MOLDE'
    ini = texto.find(marca)
    if ini < 0:
        raise RuntimeError('nao achei a camada ativa em ' + caminho)
    fim = texto.find('</script>', ini)
    if fim < 0:
        raise RuntimeError('a camada ativa nao tem fechamento em ' + caminho)
    texto2 = texto[:ini] + miolo + '\n' + texto[fim:]
    texto2 = re.sub(r'\s*<script id=TELAS_1808_JS>.*?</script>\s*', '\n',
                    texto2, flags=re.S)
    # Estilo e comportamento formam uma unica camada. Atualizar apenas o JS
    # deixava o HTML novo obedecendo às larguras antigas, sobretudo no mobile.
    if re.search(r'<style id=TELAS_1808>.*?</style>', texto2, flags=re.S):
        texto2 = re.sub(r'<style id=TELAS_1808>.*?</style>', css,
                        texto2, count=1, flags=re.S)
    else:
        texto2 = texto2.replace('</head>', css + '\n</head>', 1)
    # A camada compartilhada precisa consultar o mesmo catálogo da casca.
    # Publicá-lo no window evita que a avaliação em outra camada veja uma
    # lista vazia e suma com o seletor de habilidades adicionadas.
    texto2 = texto2.replace('const HABEF=', 'window.HABEF=', 1)
    # A barra nova nao usa mais `.cbfn.cbfnq`; a funcao aberta ja esta no card.
    # Sem esta ponte, o salvar herdado do modal antigo aborta dizendo que nao
    # existe funcao selecionada.
    if 'window.bldSalvaDireto=' not in texto2:
        texto2 = texto2.replace(
            'var func=funcaoSelecionada();',
            'var func=funcaoSelecionada();'
            'if(!func){try{var cf=_card(k);func=cf&&cf.tipo;}catch(e){}}', 1)
    if 'window._T6_CHAVE_ATUAL' not in texto2:
        texto2 = texto2.replace(
            'try{ if(typeof CUR!=="undefined" && CUR) return CUR; }catch(e){}',
            'try{ if(typeof CUR!=="undefined" && CUR) return CUR; }catch(e){}'
            'try{ if(window._T6_CHAVE_ATUAL) return window._T6_CHAVE_ATUAL; }catch(e){}', 1)
    # A ficha nova entrega chave e funcao explicitamente. Exponha uma entrada
    # direta para o salvamento, sem depender do botao selecionado no modal
    # antigo. A tela do Elenco continua apenas consumindo as builds gravadas.
    if 'window.bldSalvaDireto=' not in texto2:
        texto2 = texto2.replace(
            'window.bldSalva=function(){\n  var k=chaveAberta(); if(!k) return;\n'
            '  var func=funcaoSelecionada();',
            'function salvaBuildDireta(k,func){\n  if(!k) return;', 1)
        texto2 = texto2.replace(
            '\n window.bldUsa=function(idb, i){',
            '\n }\n window.bldSalvaDireto=function(k,func){return salvaBuildDireta(k,func);};'
            '\n window.bldSalva=function(){var k=chaveAberta();if(!k)return;'
            'return salvaBuildDireta(k,funcaoSelecionada());};'
            '\n window.bldUsa=function(idb, i){', 1)
    # Corrige a primeira previa produzida pela ponte acima: o fechamento era
    # de uma atribuicao (`};`), mas agora e uma declaracao de funcao (`}`).
    texto2 = texto2.replace(
        '\n };\n }\n window.bldSalvaDireto=',
        '\n }\n window.bldSalvaDireto=', 1)
    texto2 = texto2.replace(
        'function salvaBuildDireta(k,func){',
        'function salvaBuildDireta(k,func,nomeForcado){', 1)
    texto2 = texto2.replace(
        'var nome=prompt("Nome desta build:", sug);',
        'if(nomeForcado===undefined && typeof window.t6PedeNomeBuild==="function"){'
        'window.t6PedeNomeBuild(sug,function(v){if(v!==null)salvaBuildDireta(k,func,v);});return;}'
        'var nome=(nomeForcado!==undefined)?nomeForcado:prompt("Nome desta build:", sug);', 1)
    texto2 = texto2.replace(
        'alert("Build \\u201c"+nome+"\\u201d salva: "+b.n.toFixed(2)\n'
        '   +" em "+func+".\\n\\nEla j\\u00e1 vale no seu elenco.");',
        'var msg="Build \\u201c"+nome+"\\u201d salva: "+b.n.toFixed(2)'
        '+" em "+func+". Ela j\\u00e1 vale no seu elenco.";'
        'if(typeof window.t6Notifica==="function")window.t6Notifica(msg);else alert(msg);', 1)
    with open(caminho, 'w', encoding='utf-8', newline='') as f:
        f.write(texto2)
    print('camada da ficha atualizada:', caminho)


if __name__ == '__main__':
    atualiza(sys.argv[1] if len(sys.argv) > 1
             else os.path.join('encaixe-web', 'ENCAIXE-DO-BANCO.html'))
