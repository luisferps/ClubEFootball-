import struct
import unittest
import boxes_runtime as b

class Reader:
    base = 0x100000
    def __init__(self, total=5, second=False):
        self.mem = {}
        self.put(self.base + b.card_levels_runtime.ROOT_RVA, struct.pack("<Q",0x20000))
        self.put(0x20028,struct.pack("<Q",0x30000))
        self.put(0x30020,struct.pack("<Q",0x40000))
        self.put(0x40280,struct.pack("<Q",1))
        count = 2 if second else 1
        self.put(0x40000,struct.pack("<QQQ",0x50000,0x50000+count*b.AGENT_STRIDE,0x50000+count*b.AGENT_STRIDE))
        for n in range(count):
            agent=0x50000+n*b.AGENT_STRIDE
            self.put(agent+8,struct.pack("<Q",n+1))
            self.put(agent+0x128,struct.pack("<I",total))
            title=("Oferta "+str(n)).encode()
            self.put(agent+0x68,title.ljust(16,b"\0")+struct.pack("<QQ",len(title),15))
            data=0x70000+n*0x1000
            self.put(agent+0xE8,struct.pack("<QQQ",data,data+3*0xF8,data+3*0xF8))
            for i in range(3):self.put(data+i*0xF8+8,struct.pack("<Q",i+1))
        self.put(0x40380,struct.pack("<QQQ",0x90000,0x90000+5*0xF0,0x90000+5*0xF0))
        self.put(0x40398,struct.pack("<I",total))
        for i in range(5):self.put(0x90000+i*0xF0+8,struct.pack("<Q",i+1))
    def put(self,a,data):self.mem.update({a+i:x for i,x in enumerate(data)})
    def read(self,a,n,purpose):return bytes(self.mem.get(a+i,0) for i in range(n))

class DetailsTests(unittest.TestCase):
    def test_catalog_does_not_read_participants_or_require_physical_cards(self):
        r=Reader(second=True)
        original=r.read
        def read(a,n,purpose):
            if a in (0x40280,0x40380,0x40398,0x500e8,0x50320):
                raise AssertionError("Catálogo não deve depender de participantes")
            return original(a,n,purpose)
        r.read=read
        result=b.read_loaded_boxes(r,set(),capture_id="x",captured_at="x",catalog_only=True)
        self.assertEqual([x["agente_id"] for x in result["boxes"]],["1","2"])
        self.assertEqual(result["cobertura"],"catalogo_agentes_carregado")
    def capture(self,r):
        result=b.read_loaded_boxes(r,{str(x) for x in range(1,6)},capture_id="x",captured_at="x")
        result["jogo"]={"executavel_sha256":"x"}
        return b._public_payload(result)
    def test_full_list_replaces_three_highlights(self):
        p=self.capture(Reader())
        self.assertEqual(p["boxes"][0]["cartas"],["1","2","3","4","5"])
        self.assertEqual(p["boxes"][0]["total_jogo"],5)
    def test_partial_page_is_not_published(self):
        self.assertEqual(self.capture(Reader(total=150))["boxes"],[])
    def test_ambiguous_agent_is_not_published(self):
        self.assertEqual(self.capture(Reader(second=True))["boxes"],[])
    def test_unknown_card_is_rejected(self):
        r=Reader();r.put(0x90000+4*0xF0+8,struct.pack("<Q",999))
        with self.assertRaises(ValueError):self.capture(r)
    def test_previous_details_are_not_assigned_to_another_selected_agent(self):
        r=Reader();r.put(0x40280,struct.pack("<Q",2))
        self.assertEqual(self.capture(r)["boxes"],[])
    def test_complete_agent_list_does_not_require_opening_details(self):
        r=Reader(total=3);r.put(0x40280,struct.pack("<Q",99))
        p=self.capture(r)
        self.assertEqual(p["boxes"][0]["cartas"],["1","2","3"])
        self.assertEqual(p["boxes"][0]["total_jogo"],3)
    def test_detail_total_must_match_agent_total(self):
        r=Reader();r.put(0x50128,struct.pack("<I",150))
        self.assertEqual(self.capture(r)["boxes"],[])

if __name__=="__main__":unittest.main()
