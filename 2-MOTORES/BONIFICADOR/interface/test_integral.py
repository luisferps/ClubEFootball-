import ast
import json
from pathlib import Path
import threading
import types
import unittest
import urllib.request
import urllib.error
import servidor

ID = '12090000-0000-4000-8000-000000001209'


class Gateway:
    def __init__(self):
        self.ready = False
        self.calls = []
    def rpc(self, name, body=None):
        self.calls.append((name, body))
        if name == 'bonificador_integral_status_v1':
            return {'existe': True, 'lote_id': ID, 'pode_calcular': self.ready}
        if name == 'bonificador_integral_reaproveitar_v1':
            return {'processadas': 3, 'reaproveitadas': 3, 'bloqueadas': 0}
        raise AssertionError(name)


class Pipeline:
    def __init__(self): self.started = []
    def estado(self): return {'ativo': False}
    def iniciar(self, lote_id, integral=False):
        self.started.append((lote_id, integral))
        return {'ativo': True}
    def parar(self): return {'ativo': False}


class Integral(unittest.TestCase):
    def setUp(self):
        self.gateway, self.pipeline = Gateway(), Pipeline()
        self.server = servidor.criar_servidor(types.SimpleNamespace(gateway=self.gateway), 0, self.pipeline)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:' + str(self.server.server_address[1])
    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
    def post(self, action):
        req = urllib.request.Request(self.url + '/api/integral/' + action + '?lote_id=' + ID, data=b'{}')
        with urllib.request.urlopen(req) as r: return json.load(r)
    def test_calculo_bloqueado_antes_da_conferencia(self):
        with self.assertRaises(urllib.error.HTTPError) as caught: self.post('calcular')
        self.assertEqual(caught.exception.code, 409)
        self.assertEqual(self.pipeline.started, [])
    def test_calculo_usa_apenas_modo_integral(self):
        self.gateway.ready = True
        self.post('calcular')
        self.assertEqual(self.pipeline.started, [(ID, True)])
    def test_reuso_nao_inicia_motor(self):
        self.assertEqual(self.post('reaproveitar')['resultado']['reaproveitadas'], 3)
        self.assertEqual(self.pipeline.started, [])
        self.assertEqual(self.gateway.calls, [('bonificador_integral_reaproveitar_v1', {'p_lote_id': ID, 'p_limite': 100})])


class MotorScope(unittest.TestCase):
    def test_fila_vazia_nao_oculta_pendencias(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'motor_bonus.py').read_text(encoding='utf-8-sig'))
        block = next(node for node in tree.body if isinstance(node, ast.If)
                     and isinstance(node.test, ast.UnaryOp) and isinstance(node.test.operand, ast.Name)
                     and node.test.operand.id == 'pares')
        for pending in ('nao_conferidas', 'bloqueadas', 'calcular_pendentes'):
            with self.subTest(pending=pending):
                status = {'existe': True, 'preparado': True, pending: 1}
                scope = {'pares': [], 'LOTE_INTEGRAL_ID': ID, 'rpc': lambda *args: status,
                         'pausa': lambda: None, 'sys': __import__('sys'), 'print': lambda *args: None}
                with self.assertRaises(SystemExit) as caught:
                    exec(compile(ast.Module(body=[block], type_ignores=[]), 'encerramento-integral', 'exec'), scope)
                self.assertEqual(caught.exception.code, 2)

    def test_integral_nao_consulta_fila_geral(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'motor_bonus.py').read_text(encoding='utf-8-sig'))
        block = next(node for node in tree.body if isinstance(node, ast.Try)
                     and isinstance(node.body[0], ast.If) and isinstance(node.body[0].test, ast.Name)
                     and node.body[0].test.id == 'LOTE_INTEGRAL_ID')
        calls = []
        scope = {'LOTE_INTEGRAL_ID': ID, 'LOTE_CORRECAO_ID': '', 'LOTE_OPERACIONAL_ID': '',
                 'rpc': lambda name, body: calls.append((name, body)) or [], 'urllib': types.SimpleNamespace(error=urllib.error)}
        exec(compile(ast.Module(body=[block], type_ignores=[]), 'fila-integral', 'exec'), scope)
        self.assertEqual(calls, [('bonificador_contexto_lote_integral_v1', {'p_lote_id': ID, 'p_limit': 100, 'p_offset': 0})])
        self.assertEqual(scope['paginas'], [[]])


if __name__ == '__main__': unittest.main()
