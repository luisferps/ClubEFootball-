"""Nomes Unicode em console redirecionado nao podem interromper um envio."""
import io
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

RAIZ=Path(__file__).resolve().parents[3]/'2-MOTORES/OTIMIZADOR'
sys.path.insert(0,str(RAIZ/'OPERACAO-LOCAL-JSON/programas'))
import operacao_local_json as api

class ConsoleUnicode(unittest.TestCase):
    def test_envio_com_nome_fora_de_cp1252(self):
        buffer=io.BytesIO()
        stream=io.TextIOWrapper(buffer,encoding='cp1252')
        erros=io.TextIOWrapper(io.BytesIO(),encoding='cp1252')
        args=SimpleNamespace(comando='enviar',limite=None,cards=None,linhas=None,lote='lote')
        def enviar(*a,**kw):
            print('Pavel Nedvěd — İrfan Can')
            return 0
        with patch.object(api.sys,'stdout',stream),patch.object(api.sys,'stderr',erros),\
             patch.object(api,'argumentos',return_value=args),\
             patch.object(api,'raiz_otimizador',return_value=RAIZ),\
             patch.object(api,'enviar',side_effect=enviar):
            self.assertEqual(api.main(),0)
            stream.flush()
            self.assertEqual(buffer.getvalue().decode('utf-8').splitlines(),['Pavel Nedvěd — İrfan Can'])

if __name__=='__main__':unittest.main()
