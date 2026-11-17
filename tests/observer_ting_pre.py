# 听讲解物理/化学预习（2026-11-17）：unl 开放日每周一开两段、芯片带「预习」、未开放提示、不进考前复习、没答上不写自测、一直听接在课内科后面
# 测试数据：python3 ~/math-plan/tools/publish_ting.py ~/math-plan/tools/ting_out --dry <DIR> --pass testpw（只写本地，不推仓库）
# 用法：python3 observer_dd_2.py [DRY_DIR]   DRY_DIR 默认读环境变量 TING_DRY；目录下要有 ting/index.enc.json 和 ting/<id>.enc
import subprocess, time, json, socket, sys, os, traceback
from pathlib import Path
from playwright.sync_api import sync_playwright

DRY = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get('TING_DRY', ''))
if not (DRY / 'ting' / 'index.enc.json').exists():
    sys.exit('缺测试数据：先跑 publish_ting.py --dry <DIR> --pass testpw，再把 DIR 传进来')

def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p
PORT = free_port()
srv = subprocess.Popen(['python3', '-m', 'http.server', str(PORT), '-d', '/home/coder/book-link'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
R = []
def ok(name, cond, extra=''):
    R.append((name, bool(cond))); print(('PASS ' if cond else 'FAIL ') + name, extra if not cond else '')

def gh(route):
    req = route.request; url = req.url.split('?')[0]
    if req.method == 'GET' and '/contents/ting/' in url:
        f = DRY / 'ting' / url.split('/contents/ting/')[1]
        if f.exists():
            return route.fulfill(status=200, body=f.read_text(), headers={'Access-Control-Allow-Origin': '*'})
    if req.method == 'PUT':
        return route.fulfill(status=201, body='{"content":{"sha":"x"}}', headers={'Access-Control-Allow-Origin': '*'})
    route.fulfill(status=404, body='{}', headers={'Access-Control-Allow-Origin': '*'})


def page_at(p, when):
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Shanghai')
    ctx.clock.install(time=when)
    ctx.route('https://api.github.com/**', gh)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    ev = lambda c: pg.evaluate('(c)=>(0,eval)(c)', c)
    pg.goto(f'http://localhost:{PORT}/observer/index.html'); pg.wait_for_timeout(1500)
    ev("SYNC = {repo:'me/observer-data', token:'x', pass:'testpw'}; TING.st = 'none'; TING.idx = null; loadTing(true); 0")
    for _ in range(60):
        if ev("TING.st === 'ok'"): break
        pg.wait_for_timeout(200)
    ev("""DB.ting = {}; DB.extests = {}; localStorage.removeItem('observer:tingPlan'); TING.pick = null; TING.cur = null; TING.list = []; TING.played = null;
          DB.settings.examDates = {}; state.tab = 'learn'; state.learn = {view: 'ting'}; render(); 0""")
    return b, pg, ev, errs

try:
    with sync_playwright() as p:
        # ---- 开放前（周三 11-18）----
        b, pg, ev, errs = page_at(p, '2026-11-18T20:00:00+08:00')
        ok('0 索引里有物理 40 段、化学 16 段', ev("[TING.idx.segs.filter(s=>s.subj==='wl').length, TING.idx.segs.filter(s=>s.subj==='hx').length]") == [40, 16], ev("[TING.idx.segs.filter(s=>s.subj==='wl').length, TING.idx.segs.filter(s=>s.subj==='hx').length]"))
        ok('0b 预习段都带 pre 和 unl，课内段不带', ev("TING.idx.segs.every(s => (s.subj==='wl'||s.subj==='hx') === !!(s.pre && s.unl))"))
        ok('0c 第一周开放日 11-23、每周两段', ev("TING.idx.segs.filter(s=>s.subj==='wl').map(s=>s.unl).slice(0,5).join()") == '2026-11-23,2026-11-23,2026-11-30,2026-11-30,2026-12-07')
        txt = pg.inner_text('.chiprow')
        ok('1 芯片有物理、化学且标预习', '物理' in txt and '化学' in txt and txt.count('预习') == 2, txt)
        pg.click('[data-act=tingsubj][data-v=wl]'); pg.wait_for_timeout(300)
        ok('2 开放前点物理：提示 11 月 23 日开始', '物理预习 11 月 23 日开始' in pg.inner_text('#main'), pg.inner_text('#tingbox')[:200])
        ok('2b 开放前随机不含预习段', ev("tingPlan(today(),'rand').every(s=>!s.pre)"))
        ok('2c 开放前无报错', not errs, errs)
        b.close()
        # ---- 开放第一周（周一 11-23）----
        b, pg, ev, errs = page_at(p, '2026-11-23T20:00:00+08:00')
        pg.click('[data-act=tingsubj][data-v=wl]'); pg.wait_for_timeout(300)
        L = ev("tingList(today()).map(s=>s.id)")
        ok('3 物理今天两段 wl-001 wl-101', L == ['wl-001', 'wl-101'], L)
        ok('3b 全部列表写预习已开 2/40', '预习已开 2/40 段' in pg.inner_text('#main'))
        pg.click('[data-act=tingplay]')
        ok('4 物理能放出声', any(ev("!!(TING.a && !TING.a.paused && TING.a.currentTime > 0.2)") or pg.wait_for_timeout(200) for _ in range(75)), ev("TING.err"))
        ev("tingStop && tingStop(); 0")
        ev("tingAnswer('wl-001', false); 0")
        ok('5 预习段没答上不写自测', ev("Object.keys(DB.extests).length") == 0 and ev("DB.ting['wl-001'].r") == 'no')
        ok('6 一直听：道法后面接物理、化学', ev("TING_CHAIN.slice(-3).join()") == 'df,wl,hx')
        ok('7 化学今天也开两段', ev("tingPlan(today(),'hx').map(s=>s.id).join()") == 'hx-001,hx-002', ev("tingPlan(today(),'hx').map(s=>s.id).join()"))
        ev("DB.settings.examDates = {}; 0")
        ok('8 开放后随机可含预习段', ev("TING.idx.segs.filter(s=>tingAvail(s,today(),tingWeek(today()))&&s.pre).length") == 4)
        ok('8b 无报错', not errs, errs)
        b.close()
        # ---- 第三周（12-08）+ 考前 ----
        b, pg, ev, errs = page_at(p, '2026-12-08T20:00:00+08:00')
        ok('9 第三周物理开 6 段', ev("TING.idx.segs.filter(s=>s.subj==='wl'&&tingAvail(s,today(),tingWeek(today()))).length") == 6)
        ev("DB.settings.examDates = {[termKey(today()) + '-end']: addD(today(), 10)}; 0")
        ok('10 考前 10 天进入考前复习', ev("!!tingExam(today())"))
        ok('10a 考前复习不含预习段', ev("tingPlan(today(),'exam').length > 0 && tingPlan(today(),'exam').every(s=>!s.pre)"), ev("tingPlan(today(),'exam').map(s=>s.id).join()"))
        ok('10c 考前点物理也只是没有内容不报错', ev("Array.isArray(tingPlan(today(),'wl'))"))
        ok('10b 无报错', not errs, errs)
        b.close()
finally:
    srv.terminate()
    n = sum(1 for _, c in R if c); print(f'{n}/{len(R)} 通过'); sys.exit(0 if n == len(R) else 1)
