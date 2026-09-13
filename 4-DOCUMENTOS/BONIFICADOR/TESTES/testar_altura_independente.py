import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / '2-MOTORES/BONIFICADOR'))
from altura_independente import separar_altura, ATIVAS


class AlturaIndependente(unittest.TestCase):
    def detalhe(self, altura):
        return dict(altura=altura,coxa=.05357143,peito=.05357143,panturrilha=-.00004286,
                    cintura=0,altOmbro=0,tamBraco=.05357143,largOmbro=0,
                    comprBraco=0,comprPerna=-.05357143,tamPescoco=0,comprPescoco=0)

    def test_separacao_nao_muda_nenhum_numero(self):
        for f in range(1,20):
            for h in ('-0.5','0','0.26785714','0.5'):
                d=self.detalhe(h);r=separar_altura(d,f)
                self.assertEqual(r['total'],sum(Decimal(str(v)) for v in d.values()))
                self.assertEqual(r['delta'],0)

    def test_ronaldinho_meia_ofensivo(self):
        r=separar_altura(self.detalhe(0),8,True)
        self.assertEqual(r['total'],Decimal('0.10710000'))

    def test_somente_altura_muda(self):
        for f in range(1,20):
            d=self.detalhe('.26785714');r=separar_altura(d,f,True)
            self.assertEqual({k:v for k,v in r['detalhe'].items() if k!='altura'},
                             {k:v for k,v in d.items() if k!='altura'})
            expected=Decimal('-.26785714') if f in (4,6) else Decimal('.26785714') if f in ATIVAS else Decimal(0)
            self.assertEqual(r['altura'],expected)

    def test_sem_fallback_para_detalhe_incompleto(self):
        with self.assertRaises(ValueError): separar_altura({'altura':0},8,True)
        with self.assertRaises(ValueError): separar_altura(self.detalhe(0),20,True)

if __name__=='__main__': unittest.main()
