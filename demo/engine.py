"""Explicit workflow: parse -> preview -> persist -> recommend -> consume."""
import json
import math
import re
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

CATALOG = json.loads(Path(__file__).with_name('catalog.json').read_text(encoding='utf-8'))
FOODS = CATALOG['foods']
ALIASES = {alias: name for name, food in FOODS.items() for alias in food['aliases']}
NUMBERS = dict(zip('一二三四五六七八九十两半', [1,2,3,4,5,6,7,8,9,10,2,.5]))
NUMBER = r'(?:\d+(?:\.\d+)?|[一二三四五六七八九十两半])'
UNIT = r'(?:千克|公斤|kg|克|g|斤|个|根|枚)'


def number(value):
    return NUMBERS[value] if value in NUMBERS else float(value)


def parse_items(text):
    """Restricted Chinese grammar; reject the entire preview on unparsed clauses."""
    text = re.sub(r'^(?:我家里目前有|我家有|家里有|库存|补货|我买了|买了|补充|还有|有)[:：\s]*', '', text.strip())
    names = '|'.join(sorted(map(re.escape, ALIASES), key=len, reverse=True))
    patterns = [rf'(?P<name>{names})\s*(?P<num>{NUMBER})\s*(?P<unit>{UNIT})',
                rf'(?P<num>{NUMBER})\s*(?P<unit>{UNIT})\s*(?P<name>{names})']
    items, errors = [], []
    for clause in re.split(r'[,，、；;\n和]', text):
        clause = clause.strip().rstrip('。')
        if not clause:
            continue
        match = next((m for p in patterns if (m := re.fullmatch(p, clause))), None)
        if not match:
            errors.append(clause)
            continue
        name, unit, qty = ALIASES[match['name']], match['unit'], number(match['num'])
        food = FOODS[name]
        if unit in ('个','根','枚'):
            if 'grams' not in food or (unit == '根' and food['unit'] != '根'):
                errors.append(clause + '：请用克数')
                continue
            grams = qty * food['grams']
        else:
            grams = qty * (1000 if unit in ('kg','千克','公斤') else 500 if unit == '斤' else 1)
        if not math.isfinite(grams) or not 0 < grams <= 100000:
            errors.append(clause + '：数量需大于0且不超过100千克')
            continue
        items.append({'name':name, 'grams':grams, 'input':clause,
                      'estimated':unit in ('个','根','枚')})
    if errors or not items:
        raise ValueError('未保存。请明确食材和数量，例如“鸡蛋4个，番茄500克”。无法识别：' + '；'.join(errors))
    return items


class PantryAgent:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS pantry(name TEXT PRIMARY KEY, grams REAL NOT NULL CHECK(grams >= 0));
                CREATE TABLE IF NOT EXISTS profile(id INTEGER PRIMARY KEY CHECK(id=1), people INTEGER NOT NULL);
                INSERT OR IGNORE INTO profile VALUES(1,2);
                CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, kind TEXT, payload TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS plans(id TEXT PRIMARY KEY, payload TEXT, consumed INTEGER DEFAULT 0);
                CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, body TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS drafts(id TEXT PRIMARY KEY, payload TEXT, applied INTEGER DEFAULT 0);
                CREATE TABLE IF NOT EXISTS recipes(id TEXT PRIMARY KEY, payload TEXT);
                CREATE TABLE IF NOT EXISTS foods(name TEXT PRIMARY KEY, payload TEXT);
            ''')
            for recipe in CATALOG['recipes']:
                db.execute('INSERT OR IGNORE INTO recipes VALUES(?,?)', (recipe['id'],json.dumps(recipe,ensure_ascii=False)))
            for name, food in FOODS.items():
                db.execute('INSERT OR IGNORE INTO foods VALUES(?,?)',(name,json.dumps(food,ensure_ascii=False)))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def state(self):
        with self.connect() as db:
            return {'pantry':[dict(r) for r in db.execute('SELECT * FROM pantry ORDER BY name')],
                    'people':db.execute('SELECT people FROM profile').fetchone()[0],
                    'events':[dict(r) for r in db.execute('SELECT * FROM events ORDER BY rowid DESC LIMIT 20')],
                    'messages':[dict(r) for r in db.execute('SELECT * FROM messages ORDER BY id DESC LIMIT 10')],
                    'nutrition_source':CATALOG['nutrition_source']}

    def preview(self, text, mode='add'):
        if mode not in ('add','set'):
            raise ValueError('未知库存操作')
        items = parse_items(text)
        if mode == 'set' and len({i['name'] for i in items}) != len(items):
            raise ValueError('盘点时同一种食材请只填写一次')
        draft = {'id':uuid.uuid4().hex,'mode':mode,'items':items}
        with self.connect() as db:
            db.execute('INSERT INTO drafts(id,payload) VALUES(?,?)',(draft['id'],json.dumps(draft,ensure_ascii=False)))
        return {'type':'preview','message':'请核对后确认。补货为累加；盘点仅设置列出的食材，未列出的保留。', 'draft':draft}

    def apply(self, draft_id):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM drafts WHERE id=?',(draft_id,)).fetchone()
            if not row:
                raise ValueError('找不到待确认记录')
            if row['applied']:
                return {'message':'这笔库存已更新，无重复入库。'}
            draft = json.loads(row['payload'])
            for item in draft['items']:
                existing = db.execute('SELECT grams FROM pantry WHERE name=?',(item['name'],)).fetchone()
                qty = item['grams'] + (existing[0] if existing and draft['mode']=='add' else 0)
                db.execute('INSERT OR REPLACE INTO pantry VALUES(?,?)',(item['name'],qty))
            db.execute('UPDATE drafts SET applied=1 WHERE id=?',(draft_id,))
            db.execute('INSERT INTO events(id,kind,payload) VALUES(?,?,?)',(draft_id,draft['mode'],row['payload']))
        return {'message':'已保存库存，下次会自动读取。'}

    def recommend(self, people=None):
        with self.connect() as db:
            if people is None:
                people = db.execute('SELECT people FROM profile').fetchone()[0]
            if isinstance(people,bool) or not isinstance(people,int) or not 1<=people<=20:
                raise ValueError('人数应为1至20的整数')
            db.execute('UPDATE profile SET people=?',(people,))
            pantry = {r['name']:r['grams'] for r in db.execute('SELECT * FROM pantry')}
            foods = {r['name']:json.loads(r['payload']) for r in db.execute('SELECT * FROM foods')}
            plans, unavailable = [], []
            for row in db.execute('SELECT payload FROM recipes ORDER BY id').fetchall():
                recipe = json.loads(row[0])
                required = {k:round(v*people/recipe['people'],2) for k,v in recipe['ingredients'].items()}
                missing = [f'{k}还差{round(v-pantry.get(k,0),2)}克' for k,v in required.items() if pantry.get(k,0)+1e-8<v]
                if missing:
                    unavailable.append({'title':recipe['title'],'missing':missing})
                    continue
                total = [0.0]*4
                complete = True
                for name, grams in required.items():
                    nutrients = foods.get(name,{}).get('nutrition')
                    if nutrients is None:
                        complete = False
                    else:
                        total = [a+b*grams/100 for a,b in zip(total,nutrients)]
                plan = {**recipe,'id':uuid.uuid4().hex,'recipe_id':recipe['id'], 'people':people,
                        'ingredients':required, 'nutrition_per_person':dict(zip(['kcal','protein_g','fat_g','carbs_g'],[round(x/people,1) if complete else None for x in total]))}
                db.execute('INSERT INTO plans(id,payload) VALUES(?,?)',(plan['id'],json.dumps(plan,ensure_ascii=False)))
                plans.append(plan)
        return {'type':'recipes','people':people,'recipes':plans,'unavailable':unavailable,
                'message':f'按记住的库存，为{people}人找到{len(plans)}道可选菜。各道独立核算，并非可同时制作的套餐；确认做菜时会重新检查余量。' if plans else '当前库存没有匹配菜谱。下列是未匹配原因，不属于零采购推荐。'}

    def consume(self, plan_id):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM plans WHERE id=?',(plan_id,)).fetchone()
            if not row:
                raise ValueError('菜谱记录不存在，请重新推荐')
            if row['consumed']:
                return {'message':'已记录这次做饭，没有再次扣库存。'}
            plan = json.loads(row['payload'])
            for name, grams in plan['ingredients'].items():
                stock = db.execute('SELECT grams FROM pantry WHERE name=?',(name,)).fetchone()
                if not stock or stock[0]+1e-8<grams:
                    raise ValueError(f'{name}库存已变化，数量不足。请重新推荐。')
            for name, grams in plan['ingredients'].items():
                db.execute('UPDATE pantry SET grams=max(0,grams-?) WHERE name=?',(grams,name))
            db.execute('UPDATE plans SET consumed=1 WHERE id=?',(plan_id,))
            db.execute('INSERT INTO events(id,kind,payload) VALUES(?,?,?)',(plan_id,'cook',row['payload']))
        return {'message':f'已记录{plan["title"]}，食材已扣减。'}

    def chat(self, text):
        text = text.strip()
        if not text or len(text)>2000:
            raise ValueError('请输入1至2000字')
        with self.connect() as db:
            db.execute('INSERT INTO messages(body) VALUES(?)',(text,))
        if any(x in text for x in ['买了','补货','补充']):
            return self.preview(text,'add')
        if any(x in text for x in ['家有','家里有','家里目前有','库存：','库存:']):
            return self.preview(text,'set')
        if any(x in text for x in ['做饭','吃什么','推荐','人饭','个人的饭']):
            m = re.search(rf'({NUMBER})\s*(?:个)?人',text)
            return self.recommend(int(number(m[1])) if m else None)
        if any(x in text for x in ['还有什么','查看库存','冰箱']):
            return {'type':'inventory','message':'这些是数据库中记住的库存。',**self.state()}
        return {'message':'可以说：我家有鸡蛋4个，番茄2个，盐20克，油100克；给2个人做饭；补货鸡蛋6个；我想做饭。数量不明确时请先补充数量。'}
