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

        # ===== 1. 新字段 qo：讲解段都有、跟背段没有；换算成秒在合理位置 =====
        st = ev("""(() => { const S = TING.idx.segs, talk = S.filter(s => s.kind !== 'recite'), rc = S.filter(s => s.kind === 'recite');
          const s = Object.assign({}, S.find(x => x.id === 'dl-01'), {start: 100}), T = tingQT(s);
          const fake = Object.assign({}, rc[0], {qo: {h: 10, q: 20, a: 30}});
          return {talk: talk.length, talkQO: talk.filter(tingQO).length, rcQO: rc.filter(tingQO).length, fakeRc: tingQO(fake), T, dur: s.dur, size: s.size, qo: s.qo,
            bad: tingQO(Object.assign({}, s, {qo: {h: 5, q: 3, a: 9}})) || tingQO(Object.assign({}, s, {qo: {h: 1, q: 2, a: s.size + 1}})) || tingQO(Object.assign({}, s, {qo: undefined})) }; })()""")
        ok('1 讲解段全部带 qo', st['talk'] == 110 and st['talkQO'] == 110, json.dumps({k: st[k] for k in ['talk', 'talkQO']}))
        ok('1b 跟背段不走先问后讲（硬塞 qo 也不走）', st['rcQO'] == 0 and st['fakeRc'] is False)
        ok('1c 偏移不合法 / 没有 qo 一律不走', st['bad'] is False)
        k = st['dur'] / st['size']
        ok('1d 秒数 = start + dur×字节/size', abs(st['T']['qs'] - (100 + st['qo']['q'] * k)) < 1e-6 and abs(st['T']['as'] - (100 + st['qo']['a'] * k)) < 1e-6)
        ok('1e 题头 < 问题 < 答案 < 段末，答案 2~40 秒', 100 < st['T']['he'] < st['T']['qs'] < st['T']['as'] < 100 + st['dur'] and 2 < 100 + st['dur'] - st['T']['as'] < 40, json.dumps(st['T']))
        # 和 48kbps CBR 的字节率一致（6000 字节/秒），说明换算口径对
        ok('1f 字节率≈6000/秒', abs(st['size'] / st['dur'] - 6000) < 60, st['size'] / st['dur'])

        # ===== 2. 平日计划：新课整段、7 天前听过的复习段走 qa；没有 qo 的旧数据退回整段 =====
        ev("""DB.ting = {'dl-01': {d: '2026-10-01', n: 1, u: 1}}; ['dl-02','dl-03','dl-04','dl-05'].forEach(id => DB.ting[id] = {d: '2026-10-12', n: 1, u: 1});
              localStorage.removeItem('observer:tingPlan'); lsSet('observer:tingMin', 8); 0""")
        L = ev("tingList(today()).map(s => ({id: s.id, rv: s.rv, qa: s.qa}))")
        rv = [x for x in L if x['rv']]
        ok('2 复习段 dl-01 走 qa', any(x['id'] == 'dl-01' and x['qa'] for x in L), json.dumps(L))
        ok('2b 新课不走 qa', all(not x['qa'] for x in L if not x['rv']) and any(not x['rv'] for x in L))
        ok('2c 计划缓存带 qa', ev("(lsGet('observer:tingPlan') || {}).qa") == ['dl-01'])
        ev("window.__qo = {}; TING.idx.segs.forEach(s => { __qo[s.id] = s.qo; delete s.qo; }); localStorage.removeItem('observer:tingPlan'); 0")
        L2 = ev("tingList(today()).map(s => ({id: s.id, rv: s.rv, qa: s.qa}))")
        ok('2d 旧 index 没有 qo：复习段整段播放', any(x['rv'] for x in L2) and not any(x['qa'] for x in L2), json.dumps(L2))
        ev("TING.idx.segs.forEach(s => { if (__qo[s.id]) s.qo = __qo[s.id]; }); localStorage.removeItem('observer:tingPlan'); 0")
        # nx 决定到期：答「一样」排到以后的段不再当复习段
        ev("DB.ting['dl-01'].nx = '2026-10-20'; localStorage.removeItem('observer:tingPlan'); 0")
        ok('2e nx 没到不复习', not any(x['id'] == 'dl-01' for x in ev("tingList(today()).map(s => ({id: s.id}))")))
        ev("DB.ting['dl-01'].nx = '2026-10-13'; localStorage.removeItem('observer:tingPlan'); 0")
        ok('2f nx 到了复习', any(x['id'] == 'dl-01' and x['qa'] for x in ev("tingList(today()).map(s => ({id: s.id, qa: s.qa}))")))
        ev("DB.ting['dl-01'].full = 1; localStorage.removeItem('observer:tingPlan'); 0")
        ok('2g 上次「不一样」：这次放完整版', any(x['id'] == 'dl-01' and not x['qa'] and x['rv'] for x in ev("tingList(today()).map(s => ({id: s.id, qa: s.qa, rv: s.rv}))")))

        # ===== 3. 复习日（周日 / 考前）一次最多 8 段短版 =====
        ev("""DB.ting = {}; TING.idx.segs.forEach(s => DB.ting[s.id] = {d: '2026-09-20', n: 1, u: 1}); lsSet('observer:tingMin', 12);
              DB.settings.examDates = {}; 0""")
        S = ev("(() => { const L = tingList('2026-10-18'); return {n: L.length, qa: L.filter(s => s.qa).length, rc: L.filter(s => s.kind === 'recite' && s.qa).length}; })()")
        ok('3 周日复习：qa ≤ 8 段', 0 < S['qa'] <= 8 and S['rc'] == 0, json.dumps(S))
        ev("DB.settings.examDates[termKey('2026-10-20') + '-mid'] = '2026-10-29'; lsSet('observer:tingMin', 20); 0")
        S = ev("(() => { const L = tingList('2026-10-20'); return {exam: tingSubjToday('2026-10-20'), n: L.length, qa: L.filter(s => s.qa).length}; })()")
        ok('3b 考前：qa 封顶 8 段，其余整段', S['exam'] == 'exam' and S['qa'] == 8 and S['n'] > 8, json.dumps(S))
        ev("DB.settings.examDates = {}; lsSet('observer:tingMin', 5); 0")

        # ===== 4. 播放：复习日（手动选「复习」）全是 qa 段 =====
        ev("""DB.ting = {}; ['dl-01','dl-02','dl-03','dl-04','ls-01','ls-02'].forEach((id, i) => DB.ting[id] = {d: '2026-10-0' + (i + 1), n: 1, u: 1});
              DB.extests = {}; localStorage.removeItem('observer:tingPlan'); TING.pick = {d: today(), s: 'review'}; TING.cur = null; TING.list = [];
              state.tab = 'learn'; state.learn = {view: 'ting'}; render(); 0""")
        L = ev("tingList(today()).map(s => ({id: s.id, qa: s.qa}))")
        ok('4 复习日：听过的都是 qa，周日带的新数学段整段', len([x for x in L if x['qa']]) >= 3 and all(x['qa'] == (x['id'] in ['dl-01','dl-02','dl-03','dl-04','ls-01','ls-02']) for x in L), json.dumps(L))
        pg.click('[data-act=tingplay]')
        ok('4b 开始放：题头阶段', wait("TING.qp === 'head' && TING.a && !TING.a.paused && TING.a.currentTime > 0.2", 75), ev("({qp: TING.qp, ct: TING.a && TING.a.currentTime, p: TING.a && TING.a.paused, err: TING.err})"))
        ok('4c 原文没摆出来', '先听问题' in pg.inner_text('#main') and ev("TING.cur.paras[0]") not in pg.inner_text('#main'))
        id0 = ev("TING.cur.id"); T = ev("tingQT(TING.cur)")
        ev(f"TING.a.currentTime = {T['he']} - 0.02; 0")
        ok('4d 题头放完跳到问题', wait("TING.qp === 'q' && TING.a.currentTime >= tingQT(TING.cur).qs - 0.05", 30), ev("({qp: TING.qp, ct: TING.a.currentTime})"))
        ev(f"TING.a.currentTime = {T['as']} - 0.5; 0")
        ok('4e 问题放完暂停，出「想好了」', wait("TING.qp === 'think' && TING.a.paused", 30) and pg.locator('[data-act=tingqgo]').count() == 1, ev("({qp: TING.qp, ct: TING.a.currentTime})"))
        ok('4f 停在答案起点前', abs(ev("TING.a.currentTime") - T['as']) < 0.3)
        ok('4g 390 宽无横向滚动', ev("document.documentElement.scrollWidth") <= 391)
        pg.wait_for_timeout(400)
        pg.click('[data-act=tingqgo]')
        ok('4h 想好了 → 放答案', wait("TING.qp === 'ans' && !TING.a.paused", 30) and ev("TING.a.currentTime") >= T['as'] - 0.1, ev("({qp: TING.qp, ct: TING.a.currentTime})"))
        ev("TING.a.currentTime = TING.cur.end - 0.6; 0")
        ok('4i 答案放完暂停，问「一样 / 不一样」', wait("TING.qp === 'judge' && TING.a.paused", 30) and pg.locator('[data-act=tingqj]').count() == 2 and ev("TING.cur.id") == id0)
        bw = ev("parseFloat(document.getElementById('ting-bar').style.width) || 0")
        ok('4i2 停在「一样吗」时进度条不是空的', bw > 80, bw)
        ok('4i3 一样吗阶段文字卡提示先选再看', '选完「一样 / 不一样」再看文字' in pg.inner_text('#main') and ev("TING.cur.paras[0]") not in pg.inner_text('#main'))
        ok('4j 作答前不记听过、不弹老的「答上了吗」', ev(f"DB.ting['{id0}'].d") != '2026-10-14' and not ev("TING.ask"))
        pg.click('[data-act=tingqj][data-v="1"]')
        r = ev(f"DB.ting['{id0}']")
        ok('4k 一样：记 h（ok、lat）', r.get('h') and r['h'][-1]['ok'] is True and r['h'][-1]['d'] == '2026-10-14' and isinstance(r['h'][-1]['lat'], (int, float)) and r['h'][-1]['lat'] >= 300, json.dumps(r))
        ok('4l 一样：间隔 7→14 天', r.get('iv') == 14 and r.get('nx') == '2026-10-28', json.dumps(r))
        ok('4m 一样：记听过、不写 extests', r['d'] == '2026-10-14' and r['n'] == 2 and not ev("Object.keys(DB.extests).length"))
        ok('4n 接着放下一段，题头阶段', wait("TING.i === 1 && TING.qp === 'head' && !TING.a.paused", 30), ev("({i: TING.i, qp: TING.qp})"))
        ok('4o 列表上这段打 ✓', '✓' in pg.inner_text('.ear-row >> nth=0'))

        # ===== 5. 没回答（15 秒）：退回整段，排期不动 =====
        id1 = ev("TING.cur.id"); T1 = ev("tingQT(TING.cur)")
        ev(f"TING.a.currentTime = {T1['as']} - 0.4; 0")
        wait("TING.qp === 'q' || TING.qp === 'think'", 10)
        ev(f"if (TING.qp === 'head') TING.a.currentTime = {T1['as']} - 0.4; 0")
        ok('5 到思考停顿', wait("TING.qp === 'think' && TING.a.paused", 30), ev("({qp: TING.qp, ct: TING.a.currentTime})"))
        pg.clock.fast_forward(16000); pg.wait_for_timeout(300)
        ok('5b 15 秒没点：整段模式，从正文开头放', wait("TING.qp === 'full' && !TING.a.paused", 20) and abs(ev("TING.a.currentTime") - T1['he']) < 1.5, ev("({qp: TING.qp, ct: TING.a.currentTime})"))
        r1 = ev(f"DB.ting['{id1}']")
        ok('5c 排期不动、不记 h', not r1.get('nx') and not r1.get('h') and not r1.get('iv'), json.dumps(r1))
        ok('5d 整段模式下原文可看', ev("TING.cur.paras[0]") in pg.inner_text('#main'))
        ev("TING.a.currentTime = TING.cur.start + 0.85 * (TING.cur.end - TING.cur.start); 0"); pg.wait_for_timeout(700)
        ok('5e 整段模式按 80% 记听过', ev(f"DB.ting['{id1}'].d") == '2026-10-14' and not ev(f"DB.ting['{id1}'].nx"))

        # ===== 6. 锁屏 / 切走：问题放完时页面在后台 → 直接整段；思考停顿里切走 → 整段 =====
        ev("TING.marked = {}; tingSeek(2); 0")
        T2 = ev("tingQT(TING.cur)"); id2 = ev("TING.cur.id")
        ok('6 第三段题头', wait("TING.i === 2 && TING.qp === 'head'", 20))
        ev("Object.defineProperty(document, 'visibilityState', {configurable: true, get: () => 'hidden'}); 0")
        ev(f"TING.a.currentTime = {T2['he']} + 0.1; 0"); wait("TING.qp === 'q'", 20)
        ev(f"TING.a.currentTime = {T2['as']} - 0.4; 0")
        ok('6b 后台到问题末尾：不停，整段', wait("TING.qp === 'full' && !TING.a.paused", 30), ev("({qp: TING.qp})"))
        ev("delete document.visibilityState; 0")
        ok('6c visibilityState 恢复', ev("document.visibilityState") == 'visible')
        ev("tingSeek(2); 0"); wait("TING.qp === 'head'", 20)
        ev(f"TING.a.currentTime = {T2['he']} + 0.1; 0"); wait("TING.qp === 'q'", 20)
        ev(f"TING.a.currentTime = {T2['as']} - 0.4; 0")
        ok('6d 回到前台再来：思考停顿', wait("TING.qp === 'think'", 30))
        ev("Object.defineProperty(document, 'visibilityState', {configurable: true, get: () => 'hidden'}); document.dispatchEvent(new Event('visibilitychange')); 0")
        ok('6e 思考时切走：整段', wait("TING.qp === 'full' && !TING.a.paused", 20), ev("({qp: TING.qp})"))
        ev("delete document.visibilityState; 0")

        # ===== 7. 不一样：nx +2、下次完整版、进弄懂知识点，当场从这段开头放完整讲解到问题处 =====
        ev("tingSeek(2); 0"); wait("TING.qp === 'head'", 20)
        ev(f"TING.a.currentTime = {T2['he']} + 0.1; 0"); wait("TING.qp === 'q'", 20)
        ev(f"TING.a.currentTime = {T2['as']} - 0.4; 0"); wait("TING.qp === 'think'", 30)
        pg.click('[data-act=tingpp]')   # ▶ 在思考停顿里 = 想好了
        ok('7 ▶ 在思考停顿里等于想好了', wait("TING.qp === 'ans'", 20))
        ev("TING.a.currentTime = TING.cur.end - 0.6; 0"); wait("TING.qp === 'judge'", 30)
        pg.click('[data-act=tingqj][data-v="0"]')
        r2 = ev(f"DB.ting['{id2}']")
        ok('7b 不一样：nx +2 天、full、iv 回 7', r2.get('nx') == '2026-10-16' and r2.get('full') == 1 and r2.get('iv') == 7 and r2['h'][-1]['ok'] is False, json.dumps(r2))
        x = ev(f"Object.values(DB.extests).filter(e => e.seg === '{id2}')")
        ok('7c 不一样：只排间隔，不写 extests（方案：自报不认定掌握）', len(x) == 0, json.dumps(x))
        row = pg.inner_text(f'.ear-row >> nth={ev("TING.i")}')
        red = ev(f"[...document.querySelectorAll('.ear-row')][TING.i].innerHTML.includes('--bad')")
        ok('7c2 列表上这段写中性的「2 天后再听」，不用红字「没答上」', '2 天后再听' in row and '没答上' not in row and not red, row)
        ok('7d 从这段开头放完整讲解', wait("TING.qp === 'full2' && !TING.a.paused", 20) and ev("TING.a.currentTime") < T2['he'] + 1)
        last = ev("TING.i === TING.list.length - 1")
        ev(f"TING.a.currentTime = {T2['qs']} - 0.3; 0")
        ok('7e 讲到问题处跳下一段（最后一段就停）', wait("TING.i === 3 && TING.qp === 'head'" if not last else "!TING.on", 30), ev("({i: TING.i, qp: TING.qp, on: TING.on, n: TING.list.length})"))
        ev("tingStop(); 0")
        # 2 天后放完整版：80% 记听过时清掉 full / nx，回到 d+7
        ev(f"""(() => {{ const s = Object.assign({{}}, TING.idx.segs.find(x => x.id === '{id2}'), {{start: 0, end: 10, qa: false}}); TING.cur = s; TING.marked = {{}}; tingMark(); }})(); 0""")
        r2b = ev(f"DB.ting['{id2}']")
        ok('7f 完整版听过后清 full / nx', 'full' not in r2b and 'nx' not in r2b and r2b.get('iv') == 7, json.dumps(r2b))

        # ===== 8. h 只留 5 条；连续一样 7→14→28→56 封顶；同步按 u 整条 LWW =====
        ev("""(() => { const L = tingLog(); L['zz'] = {d: '2026-10-01', n: 1, u: 1}; const fake = {id: 'zz', qa: true, start: 0, end: 10, dur: 10, subj: 'dl', lesson: 'x', title: 'x', paras: ['p'], q: 'q', a: 'a'};
              for (let i = 0; i < 7; i++) { TING.cur = fake; TING.qp = 'judge'; TING.marked = {}; TING.list = [fake]; TING.i = 0; tingQAJudge(true); } })(); 0""")
        z = ev("DB.ting['zz']")
        ok('8 h 最多 5 条、间隔封顶 56 天', len(z['h']) == 5 and z['iv'] == 56 and z['nx'] == '2026-12-09', json.dumps({k: z[k] for k in ['iv', 'nx']}))
        m = ev("""(() => { const A = fresh(), B = fresh(); A.ting.k = {d: '2026-10-01', n: 1, h: [{d: '2026-10-01', ok: true, t: 1}], u: 5};
              B.ting.k = {d: '2026-10-02', n: 2, h: [{d: '2026-10-02', ok: false, t: 2}], nx: '2026-10-04', full: 1, u: 9};
              const M = mergeDB(A, B).M, M2 = mergeDB(B, A).M; return {a: M.ting.k, b: M2.ting.k, fresh: !!fresh().ting}; })()""")
        ok('8b 同步：新的一条整条胜出（两个方向一致）', m['a']['u'] == 9 and m['b']['u'] == 9 and m['a']['full'] == 1 and len(m['a']['h']) == 1)
        ok('8c fresh() 带 ting', m['fresh'])
        # ===== 10. 只有到期的复习段走短版：周日 / 考前拉进来的没到期段整段放（不提前复习撑大间隔）=====
        ev("tingStop(); TING.pick = null; DB.settings.examDates = {}; lsSet('observer:tingMin', 8); 0")
        ev("""DB.ting = {'dl-01': {d: '2026-10-17', n: 1, u: 1}, 'dl-02': {d: '2026-10-13', n: 2, iv: 28, nx: '2026-11-10', u: 1}, 'dl-03': {d: '2026-10-01', n: 1, u: 1}}; localStorage.removeItem('observer:tingPlan'); 0""")
        L = ev("tingList('2026-10-18').map(s => ({id: s.id, rv: s.rv, qa: s.qa}))")
        g = {x['id']: x for x in L}
        ok('10 周日：昨天才听的新课整段放', 'dl-01' in g and not g['dl-01']['qa'], json.dumps(L))
        ok('10b 周日：nx 没到的段整段放', 'dl-02' in g and not g['dl-02']['qa'], json.dumps(L))
        ok('10c 周日：到期的段照旧走短版', 'dl-03' in g and g['dl-03']['qa'], json.dumps(L))
        ev("DB.settings.examDates[termKey('2026-10-20') + '-mid'] = '2026-10-29'; lsSet('observer:tingMin', 20); localStorage.removeItem('observer:tingPlan'); TING.pick = {d: '2026-10-20', s: 'dl'}; 0")
        L = ev("tingList('2026-10-20').map(s => ({id: s.id, qa: s.qa}))")
        ok('10d 考前：没到期的听过段不走短版', not any(x['qa'] for x in L if x['id'] in ('dl-01', 'dl-02')) and any(x['qa'] for x in L if x['id'] == 'dl-03'), json.dumps(L))
        ev("DB.settings.examDates = {}; TING.pick = null; lsSet('observer:tingMin', 5); localStorage.removeItem('observer:tingPlan'); 0")
        # ===== 11. 「一样吗」15 秒没点（暂停着）：答案已听完 → 文字照常给看，再点回不重新问 =====
        q = ev("""(() => { const s = Object.assign({}, TING.idx.segs.find(x => x.id === 'dl-03'), {qa: true, rv: true, start: 0, end: 10}); TING.cur = s; TING.list = [s]; TING.i = 0; TING.qp = 'judge'; TING.on = false;
              tingQASkip(); state.tab = 'learn'; state.learn = {view: 'ting'}; render(); const qp1 = TING.qp; tingQAEnter(); return {qp1, qp2: TING.qp, h: (DB.ting['dl-03'] || {}).h || null, nx: (DB.ting['dl-03'] || {}).nx || null}; })()""")
        txt = pg.inner_text('#main')
        ok('11 没点：排期不动、不记 h', q['qp1'] == 'done' and not q['h'] and not q['nx'], json.dumps(q))
        ok('11b 没点：文字卡不再藏讲解', ev("TING.cur.paras[0]") in txt and '先听问题、自己想' not in txt)
        ok('11c 再点回这段：不重新走问答', q['qp2'] is None, json.dumps(q))
        ok('9 无页面 JS 错误', not errs, errs[:3])
        b.close()
except Exception:
    traceback.print_exc()
finally:
    srv.terminate()
n = sum(1 for r in R if r[1])
print('\n%d/%d passed' % (n, len(R)))
sys.exit(0 if R and n == len(R) else 1)
