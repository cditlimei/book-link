# 第 9 章方案第 2 条：听讲解复习段先问后讲（题头 → 问题 → 想好了 → 答案 → 一样 / 不一样）
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

try:
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Shanghai')
        ctx.clock.install(time='2026-10-14T20:00:00+08:00')   # 周三 = 地理日
        ctx.route('https://api.github.com/**', gh)
        pg = ctx.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        ev = lambda c: pg.evaluate('(c)=>(0,eval)(c)', c)
        def wait(cond, n=60, ms=200):
            for _ in range(n):
                if ev(cond): return True
                pg.wait_for_timeout(ms)
            return False
        pg.goto(f'http://localhost:{PORT}/observer/index.html'); pg.wait_for_timeout(1500)
        T = ev("today()"); ok('0 固定时钟', T == '2026-10-14', T)
        ev("SYNC = {repo:'me/observer-data', token:'x', pass:'testpw'}; TING.st = 'none'; TING.idx = null; loadTing(true); 0")
        ok('0b 解密到本地生成的 index', wait("TING.st === 'ok'"), ev("TING.st"))

        # ===== 一直听：一组放完自动接下一组，不按时长停 =====
        ev("""DB.ting = {}; DB.extests = {}; localStorage.removeItem('observer:tingPlan'); TING.pick = null; TING.cur = null; TING.list = []; TING.played = null;
              DB.settings.examDates = {}; state.tab = 'learn'; state.learn = {view: 'ting'}; render(); 0""")
        ok('1 设置里没有时长按钮了', pg.locator('[data-act=tingmin]').count() == 0)
        ok('1b 卡片写明会自动接着放', '放完自动接着放' in pg.inner_text('#main'))
        g1 = ev("tingList(today()).map(s => s.id)"); s1 = ev("tingSubjToday(today())")
        pg.click('[data-act=tingplay]')
        ok('2 开始放', wait("TING.a && !TING.a.paused && TING.a.currentTime > 0.2", 75), ev("TING.err"))
        ev("TING.a.currentTime = TING.a.duration - 1; 0")
        ok('3 第一组放完自动接第二组', wait("TING.list.length && TING.list[0].id !== %r && TING.a && !TING.a.paused && TING.a.currentTime > 0.2" % g1[0], 100), ev("({ids: TING.list.map(s=>s.id), on: TING.on, err: TING.err})"))
        g2 = ev("TING.list.map(s => s.id)")
        ok('3b 第二组不重复第一组', not set(g1) & set(g2), json.dumps([g1, g2]))
        ok('3c 第一组最后一段记为听过（跳过的不算）', ev("!!tingLog()[%r]" % g1[-1]))
        ok('3d 第一组仍是同一科没听过的（%s）' % s1, ev("tingSubjToday(today())") == s1 or not ev("tingPlan(today(), %r).some(s => !tingLog()[s.id])" % s1), ev("tingSubjToday(today())"))
        # 最后一段按「下一段」也是接下一组
        ev("tingSeek(TING.list.length - 1); 0"); pg.wait_for_timeout(500)
        pg.click('[data-act=tingnext][data-v="1"]')
        ok('4 最后一段按下一段 = 接下一组', wait("TING.list.length && !%r.includes(TING.list[0].id) && !TING.a.paused" % g2, 100), ev("TING.list.map(s=>s.id)"))
        # 连着放到别的科
        subs = set()
        for _ in range(12):
            subs.add(ev("tingSubjToday(today())"))
            if len(subs) >= 2: break
            ev("TING.a.currentTime = TING.a.duration - 1; 0"); wait("TING.a.currentTime < TING.a.duration - 2 && !TING.a.paused", 100)
        ok('5 这科放完自动轮到别的科', len(subs) >= 2, str(subs))
        # 全都放过：停下并提示
        ev("TING.idx.segs.forEach(s => tingPlayed(today()).add(s.id)); TING.a.currentTime = TING.a.duration - 1; 0")
        ok('6 全部放过才停', wait("!TING.on", 60))
        ok('7 无页面报错', not errs, '; '.join(errs))

except Exception:
    traceback.print_exc()
finally:
    srv.terminate()
n = sum(1 for r in R if r[1])
print('\n%d/%d passed' % (n, len(R)))
sys.exit(0 if R and n == len(R) else 1)
