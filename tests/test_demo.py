import tempfile
import threading
import unittest
import urllib.request
import json
from pathlib import Path
from demo.engine import PantryAgent, parse_items
from demo.server import make_server

class DemoTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'pantry.db'
        self.agent=PantryAgent(self.path)
    def tearDown(self): self.tmp.cleanup()
    def stock(self,text,mode='set'):
        d=self.agent.preview(text,mode)['draft']; self.agent.apply(d['id']); return d['id']
    def test_full_journey_and_restart(self):
        d=self.agent.chat('我家有鸡蛋4个，番茄2个，油100克，盐20克')['draft']
        self.assertEqual(self.agent.state()['pantry'],[])
        self.agent.apply(d['id']); self.agent.apply(d['id'])
        plan=next(p for p in self.agent.chat('给2个人做饭')['recipes'] if p['recipe_id']=='tomato-egg')
        self.assertGreater(plan['nutrition_per_person']['kcal'],0)
        self.agent.consume(plan['id']); self.agent.consume(plan['id'])
        reopened=PantryAgent(self.path)
        self.assertEqual({i['name']:i['grams'] for i in reopened.state()['pantry']}['鸡蛋'],50)
        d=reopened.chat('补货鸡蛋6个')['draft']; reopened.apply(d['id'])
        self.assertEqual({i['name']:i['grams'] for i in reopened.state()['pantry']}['鸡蛋'],350)
        self.assertEqual(reopened.chat('我想做饭')['people'],2)
    def test_scaling_no_implicit_condiments(self):
        self.stock('鸡蛋4个，番茄2个')
        self.assertEqual(self.agent.recommend(2)['recipes'],[])
        self.stock('油100克，盐20克')
        self.assertTrue(self.agent.recommend(2)['recipes'])
        self.assertFalse(any(p['recipe_id']=='tomato-egg' for p in self.agent.recommend(4)['recipes']))
    def test_invalid_input(self):
        for text in ['鸡蛋一些','鸡蛋4个，面包100克','鸡蛋-2个','鸡蛋0个','豆腐2个']:
            with self.assertRaises(ValueError): self.agent.preview(text)
        self.assertEqual(self.agent.state()['pantry'],[])
        self.assertEqual(parse_items('两个西红柿')[0]['grams'],300)
    def test_stale_plan_atomicity(self):
        self.stock('鸡蛋4个，番茄2个，油100克，盐20克')
        p=next(p for p in self.agent.recommend(2)['recipes'] if p['recipe_id']=='tomato-egg')
        self.stock('番茄1克'); before=self.agent.state()['pantry']
        with self.assertRaises(ValueError): self.agent.consume(p['id'])
        self.assertEqual(before,self.agent.state()['pantry'])
    def test_http(self):
        s=make_server(self.path,0); t=threading.Thread(target=s.serve_forever,daemon=True); t.start()
        base=f'http://127.0.0.1:{s.server_port}'
        try:
            with urllib.request.urlopen(base) as r: self.assertIn('冰箱私厨',r.read().decode())
            req=urllib.request.Request(base+'/api/chat',data=json.dumps({'text':'我想做饭'}).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req) as r: self.assertEqual(json.load(r)['type'],'recipes')
        finally: s.shutdown(); s.server_close(); t.join()

if __name__=='__main__': unittest.main()
