# 磨耳朵新版（2026-11-17）：四步（盲听 / 答题 / 跟读 / 单词）、只放挑中的 10 个词（中间跳过）、语速、放完一轮就停、计数进 DB.ting['e:…']、家长复盘一行、旧单元回落旧版
# 测试数据：python3 ~/math-plan/tools/publish_ear2.py --dry <DIR> --pass testpw（只写本地，不推仓库）
# 用法：python3 observer_ear2.py <DRY_DIR>
import subprocess, time, socket, sys, os, traceback
from pathlib import Path
from playwright.sync_api import sync_playwright

DRY = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get('EAR_DRY', ''))
if not (DRY / 'ear' / 'index.enc.json').exists():
    sys.exit('缺测试数据：先跑 publish_ear2.py --dry <DIR> --pass testpw')

def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p
PORT = free_port()
srv = subprocess.Popen(['python3', '-m', 'http.server', str(PORT), '-d', '/home/coder/book-link'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
R = []
def ok(name, cond, extra=''):
    R.append((name, bool(cond))); print(('PASS ' if cond else 'FAIL ') + name, extra if not cond else '')

def gh(route):
    req = route.request; url = req.url.split('?')[0]
    if req.method == 'GET' and '/contents/ear/' in url:
        f = DRY / 'ear' / url.split('/contents/ear/')[1]
        if f.exists():
            return route.fulfill(status=200, body=f.read_text(), headers={'Access-Control-Allow-Origin': '*'})
    if req.method == 'PUT':
        return route.fulfill(status=201, body='{"content":{"sha":"x"}}', headers={'Access-Control-Allow-Origin': '*'})
    route.fulfill(status=404, body='{}', headers={'Access-Control-Allow-Origin': '*'})

try:
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Shanghai')
        ctx.clock.install(time='2026-11-19T07:10:00+08:00')
        ctx.route('https://api.github.com/**', gh)
        pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        ev = lambda c: pg.evaluate('(c)=>(0,eval)(c)', c)
        pg.goto(f'http://localhost:{PORT}/observer/index.html'); pg.wait_for_timeout(1500)
        ev("""SYNC = {repo:'me/observer-data', token:'x', pass:'testpw'}; DB.ting = {}; DB.words = {};
              localStorage.removeItem('observer:earPick'); localStorage.removeItem('observer:earRate');
              lsSet('observer:earUnit', {u: 1, a: enUnit(today()) || 1}); EAR.st = 'none'; EAR.idx = null; loadEar(true); 0""")
        for _ in range(80):
            if ev("EAR.st === 'ok'"): break
            pg.wait_for_timeout(200)
        ok('0 索引加载（v3）', ev("EAR.st === 'ok' && EAR.idx.v === 3"), ev("EAR.st"))
        ok('1 Unit 1 走新版：课文 r、c、单词三条', ev("(earDay(1)||{}).v2 && earDay(1).parts.map(p=>p.id).join()") == '7a-u1-r,7a-u1-c,7a-u1-w', ev("earDay(1) && earDay(1).parts && earDay(1).parts.map(p=>p.id).join()"))
        ok('1b 没有新版的单元回落旧版整条', ev("(() => { const d = earDay(2); return !!(d && !d.v2 && d.segs); })()"))
        # 选词：到期没拿下的优先、已掌握的排后
        ev("""DB.words = {'trust': {due: today(), done: false, u: 1}, 'courage': {due: today(), done: false, u: 1}, 'guitar': {due: '2026-12-30', done: true, u: 1}};
              localStorage.removeItem('observer:earPick'); 0""")
        L = ev("earPlaylist(1).map(t => t.kind + ':' + (t.kind === 'word' ? t.title : ''))")
        ok('2 播放顺序：两篇×（盲听/答题/跟读）+ 单词说明 + 10 个词', [x.split(':')[0] for x in L] == ['listen', 'qa', 'shadow'] * 2 + ['words4'] + ['word'] * 10, L)
        words = [x.split(':')[1] for x in L if x.startswith('word:')]
        ok('2b 到期的 trust、courage 选进来，已掌握的 guitar 不选', 'trust' in words and 'courage' in words and 'guitar' not in words, words)
        ok('2c 同一天再算一次选词不变', ev("earPlaylist(1).filter(t=>t.kind==='word').map(t=>t.title).join()") == ','.join(words))
        # 界面
        ev("state.tab = 'learn'; state.learn = {view: 'ear'}; render(); 0"); pg.wait_for_timeout(300)
        txt = pg.inner_text('#main')
        ok('3 页面有语速三档、没有「放多久」', '慢速' in txt and '快速' in txt and '放多久' not in txt, txt[:400])
        ok('3b 开始按钮写明两篇课文 + 单词', '两篇课文 + 单词' in txt)
        # 固定选词，方便测跳过：guitar(第 1 个) 和 courage(第 6 个)，中间 4 个要跳过
        ev("lsSet('observer:earPick', {d: today(), u: 1, w: ['guitar', 'courage']}); 0")
        pg.click('[data-act=earplay]')
        for _ in range(60):
            if ev("!!(EAR.a && !EAR.a.paused && EAR.a.currentTime > 0.3)"): break
            pg.wait_for_timeout(200)
        ok('4 开始播放、从盲听开始', ev("EAR.on && EAR.cur.kind === 'listen' && !EAR.a.paused"), ev("[EAR.on, EAR.cur && EAR.cur.kind, EAR.err]"))
        ok('4b 不循环', ev("EAR.a.loop === false"))
        ok('4c 盲听时页面不直接给原文', '先别看' in pg.inner_text('#main'))
        pg.click('[data-act=earrate][data-v="0.85"]'); pg.wait_for_timeout(200)
        ok('5 切慢速 → playbackRate 0.85', abs(ev("EAR.a.playbackRate") - 0.85) < 1e-6, ev("EAR.a.playbackRate"))
        # 答题：跳到第 1 题答案开始处
        ev("""(() => { const i = EAR.list.findIndex(t => t.kind === 'qa'); earSeek(i); const t = EAR.list[i], a = t.items.find(x => x.k === 'a' && x.j === 0); EAR.a.currentTime = t.off + a.s + 0.3; })(); 0""")
        pg.wait_for_timeout(1200)
        main = pg.inner_text('#main')
        ok('6 答题段显示第 1 题和答案', '第 1 题' in main and 'good at maths' in main, main[:500])
        pg.click('[data-act=earqa] >> nth=0'); pg.wait_for_timeout(200)
        rec = ev("Object.entries(DB.ting).filter(([k]) => k.startsWith('e:')).map(([k, v]) => v)[0] || null")
        ok('6b 点「答上了」记进 DB.ting e: 记录', rec and rec.get('ok') == 1, rec)
        # 跟读计数：跳到某句跟读结束前 1 秒，自然放过去
        ev("""(() => { const i = EAR.list.findIndex(t => t.kind === 'shadow'); earSeek(i); const t = EAR.list[i], x = t.items.filter(x => x.k === 'shadow')[2]; EAR.a.currentTime = t.off + x.e - 0.8; ear2Ci(EAR.a.currentTime); })(); 0""")
        pg.wait_for_timeout(2500)
        sh = ev("Object.entries(DB.ting).filter(([k]) => k.startsWith('e:')).map(([k, v]) => v.sh)[0]")
        ok('7 自然放过一句跟读 → sh 计 1', sh == 1, sh)
        ok('7b 跟读段页面显示这一句和中文', '跟着大声说' in pg.inner_text('#main'))
        # 跳过没选的词：放到 guitar 结尾前 0.5 秒
        ev("""(() => { const i = EAR.list.findIndex(t => t.kind === 'word'); earSeek(i); EAR.a.currentTime = EAR.list[i].end - 0.5; })(); 0""")
        pg.wait_for_timeout(2000)
        st = ev("[EAR.cur && EAR.cur.title, EAR.a.currentTime, (EAR.list.find(t => t.title === 'courage') || {}).start]")
        ok('8 guitar 放完直接跳到 courage（跳过中间 4 个词）', st[0] == 'courage' and st[2] - 0.2 <= st[1] <= st[2] + 2.5, st)
        ok('8b 单词段显示中文和例句来源', 'courage' in pg.inner_text('#main') and ('课文原句' in pg.inner_text('#main') or '自编例句' in pg.inner_text('#main')))
        # 放完一轮就停
        ev("EAR.a.currentTime = EAR.list[EAR.list.length - 1].end - 0.5; 0")
        pg.wait_for_timeout(2000)
        ok('9 最后一个词放完就停、不循环', ev("!EAR.on && EAR.a.paused"), ev("[EAR.on, EAR.a.paused, EAR.a.currentTime]"))
        ok('9b 停后计数里单词 2 个（guitar、courage）', ev("Object.entries(DB.ting).filter(([k]) => k.startsWith('e:')).map(([k, v]) => v.w)[0]") == 2, ev("JSON.stringify(DB.ting)"))
        # 家长复盘
        ok('10 家长「练习难度」有磨耳朵一行', '磨耳朵答题跟读' in ev("practiceCard(addD(today(), -3), addD(today(), 3))"), ev("practiceCard(addD(today(), -3), addD(today(), 3))")[:300])
        # 今天页卡片
        ev("state.tab = 'today'; render(); 0"); pg.wait_for_timeout(300)
        ok('11 今天页早上卡片是新说明', '先盲听' in pg.inner_text('#main'), pg.inner_text('#main')[:300])
        ok('12 全程无报错', not errs, errs)
        pg.screenshot(path=str(DRY / 'ear_today.png'))
        b.close()
except Exception:
    traceback.print_exc(); R.append(('exception', False))
finally:
    srv.terminate()
n = sum(1 for _, x in R if x); print(f'\n{n}/{len(R)} passed'); sys.exit(0 if n == len(R) else 1)
