# 第 9 章方案第 1 条：到期背诵复习先背后看（hide 视图 / 偷看只当练习 / 漏字行号 / 抽段 / 用时）
import subprocess, time, json, socket, sys, traceback
from playwright.sync_api import sync_playwright

def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p
PORT = free_port()
srv = subprocess.Popen(['python3', '-m', 'http.server', str(PORT), '-d', '/home/coder/book-link'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
R = []
def ok(name, cond, extra=''):
    R.append((name, bool(cond))); print(('PASS ' if cond else 'FAIL ') + name, extra if not cond else '')

try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Shanghai')
        ctx.clock.install(time='2026-10-14T20:00:00+08:00')
        ctx.route('https://api.github.com/**', lambda r: r.fulfill(status=404, body='{}'))
        pg = ctx.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        ev = lambda c: pg.evaluate('(c)=>(0,eval)(c)', c)
        pg.goto(f'http://localhost:{PORT}/observer/index.html'); pg.wait_for_timeout(1500)
        for _ in range(40):
            if ev("!!(LIB.recite && LIB.recite.items && LIB.recite.items.length)"): break
            pg.wait_for_timeout(250)
        ok('0 背诵库已加载', ev("!!LIB.recite"))
        T = ev("today()"); ok('0b 固定时钟', T == '2026-10-14', T)
        S = ev("LIB.recite.items.find(x => x.text && x.mode !== 'title' && !recSegs(x).length && x.text.length >= 2).id")
        L = ev("LIB.recite.items.filter(x => x.text && x.mode !== 'title' && recSegs(x).length >= 3)[0].id")
        NS = ev(f"recSegs(LIB.recite.items.find(x => x.id === '{L}')).length")
        def setup(i, extra='{}'):
            ev(f"DB.recite['{i}'] = Object.assign({{st:'can', box:1, due:today(), rev:recRev(LIB.recite.items.find(x => x.id === '{i}')), hist:[{{d:'2026-10-01', st:'voice', score:96}}], u:now()}}, {extra}); save(); 0")
        def openp(i):
            ev(f"state.tab='learn'; state.learn = state.learn || {{}}; ACT.rpoem({{dataset:{{v:'{i}'}}}}); 0"); pg.wait_for_timeout(200)
        main = lambda: pg.inner_text('#main')
        def first_line(i): return ev(f"LIB.recite.items.find(x => x.id === '{i}').text[0]")

        # ===== 1. 短篇：先背页有按钮，不露原文 =====
        setup(S); openp(S)
        ok('1 到期篇目打开是 hide', ev("state.learn.pmode") == 'hide')
        ok('1b 先背卡在首屏', pg.locator('.rvhide').count() == 1 and pg.locator('.rvhide').bounding_box()['y'] < 844)
        ok('1c 短篇写「从题目开始背」', '从题目开始背' in pg.inner_text('.rvhide'))
        ok('1d 短篇有「背给我听」按钮', pg.locator('.rvhide [data-act=rcheck][data-v=voice]').count() == 1 and '背给我听' in pg.inner_text('.rvhide [data-act=rcheck][data-v=voice]'))
        ok('1e 原文不在页面上', first_line(S) not in main())
        ok('1f 看原文/听朗读在下面', pg.locator('[data-act=pmode][data-v=full]').count() >= 1 and pg.locator('.ptools [data-act=sayzh]').count() == 1)
        ok('1g 390 宽无横向滚动', ev("document.documentElement.scrollWidth") <= 391)
        fs0 = ev(f"JSON.stringify(DB.recite['{S}'].fs || null)")
        # 不偷看，打字默写全对 → 进 FSRS，hist 有 rv:1，原文自动出现
        pg.click('.rvhide [data-act=rcheck][data-v=type]'); pg.wait_for_timeout(200)
        txt = ev(f"LIB.recite.items.find(x => x.id === '{S}').text.join('')")
        pg.fill('#rc-type', txt); pg.click('[data-act=rctype]'); pg.wait_for_timeout(600)
        h = ev(f"DB.recite['{S}'].hist.filter(e => e.score != null).slice(-1)[0]")
        ok('2 不偷看：记为复习 rv:1', h.get('rv') == 1 and not h.get('peek') and h['st'] == 'type', json.dumps(h))
        ok('2b 不偷看：due 往后排', ev(f"DB.recite['{S}'].due") > T and ev(f"DB.recite['{S}'].hist.some(e => e.st === 'rv-ok' && e.d === today())"))
        ok('2c 结果页没有练习提示', pg.locator('.rcpeek').count() == 0)
        ok('2d 打字模式不记用时', 'sec' not in h)
        pg.click('[data-act=rcclose]'); pg.wait_for_timeout(200)
        ok('2e 背完后原文自动显示', first_line(S) in main() and pg.locator('.rvhide').count() == 0)

        # ===== 3. 长篇：cue + 背这段；看原文后再背 = 练习 =====
        ev("state.learn.peek = {}; 0")
        setup(L, "{fs: {s:3, df:5, r:2, l:0, st:2, lr:'2026-10-10', due:'2026-10-14'}}"); openp(L)
        seg = ev(f"recPickSeg(LIB.recite.items.find(x => x.id === '{L}'))")
        ok('3 长篇写「今天背第 N 段」', f'今天背第 {seg + 1} 段' in pg.inner_text('.rvhide'), pg.inner_text('.rvhide'))
        cue = ev(f"(x => x.text[recSegs(x)[{seg}][0]].replace(/[，。；：？！、“”]/g, '').slice(0, 4))(LIB.recite.items.find(x => x.id === '{L}'))")
        ok('3b 给前 4 字提示', f'「{cue}」' in pg.inner_text('.rvhide'))
        ok('3c 背这段 / 默写按钮带段号', pg.locator(f'.rvhide [data-act=rcheck][data-v=voice][data-s="{seg}"]').count() == 1 and pg.locator(f'.rvhide [data-act=rcheck][data-v=type][data-s="{seg}"]').count() == 1)
        ok('3d 原文不在页面上', first_line(L) not in main())
        pg.click('.ptools [data-act=pmode][data-v=full]'); pg.wait_for_timeout(200)
        ok('4 看原文 → peek 标记', ev(f"recPeeked('{L}')") and first_line(L) in main())
        ok('4b 页面写「明天不看再背一次就算数」', '看了原文，明天不看再背一次就算数' in main())
        fs0 = ev(f"JSON.stringify(DB.recite['{L}'].fs)")
        # 背第 seg 段，漏掉段内第 2 行 → mi 存全文绝对行号
        ev(f"ACT.rcheck({{dataset:{{v:'type', s:'{seg}'}}}}); 0"); pg.wait_for_timeout(200)
        sg = ev(f"recSegs(LIB.recite.items.find(x => x.id === '{L}'))")
        lines = ev(f"LIB.recite.items.find(x => x.id === '{L}').text")
        a, bnd = sg[seg]
        part = lines[a:bnd]
        typed = ''.join(l for k, l in enumerate(part) if k != 1)
        pg.fill('#rc-type', typed); pg.click('[data-act=rctype]'); pg.wait_for_timeout(600)
        r = ev(f"DB.recite['{L}']"); h = [e for e in r['hist'] if e.get('score') is not None][-1]
        ok('5 偷看：hist st=peek peek:1 m=type', h['st'] == 'peek' and h.get('peek') == 1 and h.get('m') == 'type' and h.get('seg') == seg, json.dumps(h))
        ok('5b 偷看：不进 FSRS（fs 不变、无 rv-ok/rv-no）', json.dumps(r['fs'], separators=(',', ':')) == json.dumps(json.loads(fs0), separators=(',', ':')) and not any(e['st'] in ('rv-ok', 'rv-no') and e['d'] == T for e in r['hist']))
        ok('5c 偷看：due = 明天', r['due'] == '2026-10-15', r['due'])
        ok('5d 当晚算完成：不再到期', ev("reciteDue().length") == 0 or ev(f"!reciteDue().some(x => x.id === '{L}')"))
        ok('5e 结果页写练习提示', pg.locator('.rcpeek').count() == 1)
        want = a + 1
        ok('5f 漏字记全文绝对行号', want in (h.get('mi') or []) and all(a <= li < bnd for li in h['mi']), f"mi={h.get('mi')} want={want} seg={sg[seg]}")
        ok('5g FSRS 回放忽略 peek', ev("recHistRate({peek:1, score:95})") == 0 and ev("recHistRate({score:95})") == 3)
        pg.click('[data-act=rcclose]'); pg.wait_for_timeout(200)
        ok('5h 记录行写「看后背」', '看后背' in main())
        # 今天页「语文背诵」清掉
        ev("Object.keys(DB.recite).forEach(k => { if (DB.recite[k].due && DB.recite[k].due <= today()) DB.recite[k].due = '2026-11-30'; }); save(); setTab('today'); 0"); pg.wait_for_timeout(300)
        ok('5i 今天页背诵行完成', ev("reciteDue().length") == 0 and '复习 0 篇' not in main())

        # ===== 6. 其他偷看入口：听朗读 / 挖空点开行；全默档不算 =====
        def fresh_due():
            ev("state.learn.peek = {}; 0"); setup(L); openp(L)
        fresh_due(); pg.click('.ptools [data-act=sayzh]'); pg.wait_for_timeout(300)
        ok('6 听朗读 → peek', ev(f"recPeeked('{L}')") and 'rvpeek' in pg.inner_html('#main'))
        ev("try { window.__poemAudio && window.__poemAudio.pause(); } catch(e) {} 0")
        fresh_due(); ev("ACT.pmode({dataset:{v:'blank'}}); 0"); pg.wait_for_timeout(200)
        ok('6b 从先背页切挖空默认全默、不算偷看', ev("state.learn.lvl") == 3 and not ev(f"recPeeked('{L}')"))
        pg.locator('[data-act=preveal]').first.click(); pg.wait_for_timeout(200)
        ok('6c 挖空里点开一行 → peek', ev(f"recPeeked('{L}')"))
        fresh_due(); ev("ACT.pmode({dataset:{v:'blank'}}); ACT.plvl({dataset:{v:'1'}}); 0")
        ok('6d 挖空切到提示多 → peek', ev(f"recPeeked('{L}')"))
        ev("state.learn.peek = {}; 0"); setup(L, "{due:'2026-10-20'}"); openp(L)
        ok('6e 没到期打开是原文，看原文不记 peek', ev("state.learn.pmode") == 'full' and (ev("ACT.pmode({dataset:{v:'full'}}), 0") == 0) and not ev(f"recPeeked('{L}')"))
        # 前一天的 peek 不算今天
        ev(f"state.learn.peek = {{'{L}': '2026-10-13'}}; 0")
        ok('6f 昨天偷看今天不算', not ev(f"recPeeked('{L}')"))

        # ===== 7. 抽段：没查过的先、覆盖每一段、再按漏字 =====
        x = f"LIB.recite.items.find(x => x.id === '{L}')"
        ev(f"DB.recite['{L}'] = {{st:'can', box:1, due:today(), rev:recRev({x}), hist:[], fs:{{s:3, df:5, r:2, l:0, st:2, lr:'2026-10-10', due:'2026-10-14'}}, u:now()}}; 0")
        seen = []
        for k in range(NS):
            sgk = ev(f"recPickSeg({x})"); seen.append(sgk)
            ev(f"DB.recite['{L}'].hist.push({{d:'2026-10-1' + {k % 4}, st:'voice', score:95, seg:{sgk}}}, {{d:'2026-10-1' + {k % 4}, st:'rv-ok'}}); 0")   # 真实流程 reviewRecite 会同时写 rv-ok（无 seg）
        ok('7 抽段覆盖每一段', sorted(seen) == list(range(NS)), str(seen))
        # 全部近期查过 → 按近 3 次漏字最多的段（段 NS-1）
        lastA = sg[NS - 1][0]
        ev(f"DB.recite['{L}'].hist.push({{d:'2026-10-13', st:'voice', score:80, seg:{NS - 1}, mi:[{lastA}, {lastA + 1}]}}); 0")
        ok('7b 都查过 → 抽漏字最多的段', ev(f"recPickSeg({x})") == NS - 1, str(ev(f"recPickSeg({x})")))
        # 段 1 超过 2 个复习周期（周期 4 天 → 8 天）没查过 → 先抽它
        ev(f"DB.recite['{L}'].hist.forEach(e => {{ if (e.seg === 1) e.d = '2026-10-01'; }}); 0")
        ok('7c 超过 2 个周期没查的段优先', ev(f"recPickSeg({x})") == 1, str(ev(f"recPickSeg({x})")))
        # 整篇检验算每段都查过；peek 不算查过
        ev(f"DB.recite['{L}'].hist = [{{d:'2026-10-13', st:'voice', score:95}}]; 0")
        r1 = ev(f"recPickSeg({x})")
        ok('7d 整篇检验覆盖所有段 → 回到日期轮', r1 == ev(f"dayDiff('2026-01-01', today()) % {NS}"), str(r1))
        ev(f"DB.recite['{L}'].hist = [{{d:'2026-10-13', st:'peek', peek:1, score:95, seg:0}}]; 0")
        ok('7e peek 不算查过', ev(f"recPickSeg({x})") == 0)
        ok('7f 老记录（无 fs、无 mi）不报错', ev(f"(DB.recite['{L}'] = {{st:'can', box:2, due:today(), rev:recRev({x}), hist:[{{d:'2026-09-01', st:'rv-ok'}}]}}, recPickSeg({x}))") == 0)

        # ===== 8. 语音模式记用时 =====
        ev(f"state.learn.peek = {{}}; DB.recite['{S}'] = {{st:'can', box:1, due:today(), rev:recRev(LIB.recite.items.find(x => x.id === '{S}')), hist:[], u:now()}}; state.learn.poem = '{S}'; ACT.rcheck({{dataset:{{v:'voice'}}}}); 0")
        ev(f"REC = {{sr: {{stop(){{}}}}, on: true, t0: Date.now() - 7000}}; state.rcheck.said = LIB.recite.items.find(x => x.id === '{S}').text.join(''); 0")
        pg.evaluate("() => recStop()"); pg.wait_for_timeout(1500)
        h = ev(f"DB.recite['{S}'].hist.filter(e => e.score != null).slice(-1)[0]")
        ok('8 语音模式写 sec', h and h.get('st') == 'voice' and isinstance(h.get('sec'), int) and 6 <= h['sec'] <= 9, json.dumps(h))
        ev("ACT.rcclose(); 0")

        # ===== 9. 今天页只有 1 篇到期 → 直接打开先背页；2 篇 → 列表 =====
        ev("Object.keys(DB.recite).forEach(k => delete DB.recite[k]); save(); 0")
        setup(S); ev("setTab('today'); 0"); pg.wait_for_timeout(300)
        ev("ACT.golearn({dataset:{v:'recite'}}); 0"); pg.wait_for_timeout(200)
        ok('9 1 篇到期 → 直接先背页', ev("state.learn.view") == 'poem' and ev("state.learn.poem") == S and pg.locator('.rvhide').count() == 1)
        setup(L); ev("setTab('today'); 0"); pg.wait_for_timeout(200)
        ev("ACT.golearn({dataset:{v:'recite'}}); 0"); pg.wait_for_timeout(200)
        ok('9b 2 篇到期 → 篇目列表', ev("state.learn.view") == 'recite')

        # ===== 10. 同步合并：hist 新字段保留 =====
        m = ev("mergeRec({u:1, st:'can', hist:[{d:'2026-10-13', st:'peek', peek:1, score:80, mi:[1,2], m:'voice', sec:30}]}, {u:2, st:'can', hist:[{d:'2026-10-14', st:'type', score:99, rv:1}]}).v")
        ok('10 mergeRec 保留 peek/mi/sec/rv', len(m['hist']) == 2 and m['hist'][0].get('mi') == [1, 2] and m['hist'][0].get('sec') == 30 and m['hist'][1].get('rv') == 1)

        # ===== 12. 偷看后背对：不升状态、不写 segs、结果页不说「记为」 =====
        ev("Object.keys(DB.recite).forEach(k => delete DB.recite[k]); state.learn.peek = {}; save(); 0")
        setup(S); openp(S); pg.click('.ptools [data-act=pmode][data-v=full]'); pg.wait_for_timeout(200)
        ev("ACT.rcheck({dataset:{v:'type'}}); 0"); pg.wait_for_timeout(200)
        pg.fill('#rc-type', ev(f"LIB.recite.items.find(x => x.id === '{S}').text.join('')")); pg.click('[data-act=rctype]'); pg.wait_for_timeout(600)
        r = ev(f"DB.recite['{S}']")
        ok('12 偷看后默写全对：st 仍是 can', r['st'] == 'can', r['st'])
        ok('12b 偷看后：今天没有 dict/can 记录、回放评分 0', not any(e['d'] == T and e['st'] in ('dict', 'can') for e in r['hist'])
           and ev(f"(()=>{{let v=0; for (const e of DB.recite['{S}'].hist.filter(h => h.d === today())) {{ const k = recHistRate(e); if (k) v = k; }} return v}})()") == 0, json.dumps(r['hist'], ensure_ascii=False))
        ok('12c 偷看后：due = 明天', r['due'] == '2026-10-15', r['due'])
        ok('12d 结果页不写「记为」', '记为' not in pg.inner_text('.wiz') and '这遍背对了' in pg.inner_text('.wiz'))
        ev("ACT.rcclose(); 0")
        setup(L); openp(L); pg.click('.ptools [data-act=pmode][data-v=full]'); pg.wait_for_timeout(200)
        ev("ACT.rcheck({dataset:{v:'type', s:'0'}}); 0"); pg.wait_for_timeout(200)
        pg.fill('#rc-type', ''.join(lines[sg[0][0]:sg[0][1]])); pg.click('[data-act=rctype]'); pg.wait_for_timeout(600)
        r = ev(f"DB.recite['{L}']")
        ok('12e 偷看后背对一段：不写 segs、st 仍 can', not (r.get('segs') or {}) and r['st'] == 'can', json.dumps({k: r.get(k) for k in ('segs', 'st')}))
        ev("ACT.rcclose(); 0"); pg.wait_for_timeout(200)

        # ===== 13. 原文视图（到期且偷看）：今天该复习卡在首屏；seg 有「先背」可切回 =====
        ev("state.learn.peek = {}; 0"); setup(L); openp(L); pg.click('.poemv .seg [data-act=pmode][data-v=full]'); pg.wait_for_timeout(200)   # 偷看一次（还没背，仍到期）
        ok('13 原文视图：今天该复习卡在第一屏', pg.locator('.rvdue').count() == 1 and pg.locator('.rvdue').bounding_box()['y'] < 844, str(pg.locator('.rvdue').bounding_box()))
        ok('13b 今天该复习卡在原文上面', ev("(() => { const c = document.querySelector('.rvdue'), t = document.querySelector('.poemv [data-act=sayzh]'); return c.getBoundingClientRect().top < t.getBoundingClientRect().top; })()"))
        ok('13c seg 有「先背」且原文是选中态', pg.locator('.poemv .seg [data-act=pmode][data-v=hide]').count() == 1 and pg.locator('.poemv .seg [data-act=pmode][data-v=full].on').count() == 1)
        pg.click('.poemv .seg [data-act=pmode][data-v=hide]'); pg.wait_for_timeout(200)
        ok('13d 点「先背」回到先背页且「先背」选中', pg.locator('.rvhide').count() == 1 and pg.locator('.poemv .seg [data-act=pmode][data-v=hide].on').count() == 1 and first_line(L) not in main())
        ok('13e 先背页 390 宽无横向滚动', ev("document.documentElement.scrollWidth") <= 391)
        ev("state.learn.peek = {}; 0"); setup(L, "{due:'2026-10-20'}"); openp(L)
        ok('13f 没到期不显示「先背」', pg.locator('.poemv .seg [data-act=pmode][data-v=hide]').count() == 0)

        # ===== 14. 真实流程连续复习：每段都能抽到 =====
        ev("Object.keys(DB.recite).forEach(k => delete DB.recite[k]); state.learn.peek = {}; save(); 0")
        ev(f"DB.recite['{L}'] = {{st:'can', box:1, due:today(), rev:recRev({x}), hist:[{{d:'2026-09-20', st:'voice', score:96}}], fs:{{s:3, df:5, r:2, l:0, st:2, lr:'2026-10-10', due:'2026-10-14'}}, u:now()}}; save(); 0")
        picks = []
        for rnd in range(6):
            k = ev(f"recPickSeg({x})"); picks.append(k)
            ev(f"state.learn.peek = {{}}; ACT.rpoem({{dataset:{{v:'{L}'}}}}); ACT.rcheck({{dataset:{{v:'voice', s:'{k}'}}}}); 0"); pg.wait_for_timeout(150)
            said = ''.join(lines[sg[k][0]:sg[k][1]]); said = said[:3] + said[4:]   # 漏一个字，仍 ≥90 分
            ev(f"state.rcheck.said = {json.dumps(said)}; 0")
            pg.evaluate("() => finishCheck()"); pg.wait_for_timeout(400)
            nd = ev(f"DB.recite['{L}'].due"); ev("ACT.rcclose(); 0")
            if not nd: break
            pg.clock.set_fixed_time(nd + 'T20:00:00+08:00'); pg.wait_for_timeout(100)
        ok('14 真实流程连续复习覆盖每一段', sorted(set(picks)) == list(range(NS)), str(picks))
        ok('14b rv-ok 不算查过某段', ev(f"(() => {{ const r = DB.recite['{L}']; return r.hist.some(h => /^rv-/.test(h.st)); }})()"))

        ok('11 无页面报错', not errs, str(errs))

        # ===== 15. FSRS 没加载：吃力（70–89 分）也排下次复习 =====
        ctx2 = b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Shanghai')
        ctx2.clock.install(time='2026-10-14T20:00:00+08:00')
        ctx2.route('https://api.github.com/**', lambda r: r.fulfill(status=404, body='{}'))
        ctx2.route('**/vendor/ts-fsrs*', lambda r: r.abort())
        pg2 = ctx2.new_page(); pg2.goto(f'http://localhost:{PORT}/observer/index.html'); pg2.wait_for_timeout(1500)
        ev2 = lambda c: pg2.evaluate('(c)=>(0,eval)(c)', c)
        ok('15 FS 为空', ev2("FS === null"))
        d2 = ev2("(DB.recite.zz = {st:'can', box:1, due:today(), hist:[], u:now()}, reviewRecite('zz', true, 2), DB.recite.zz)")
        ok('15b 吃力：due 往后排、box 不动', d2['due'] and d2['due'] > '2026-10-14' and d2['box'] == 1, json.dumps(d2))
        ctx2.close()
        b.close()
except Exception:
    traceback.print_exc(); R.append(('exception', False))
finally:
    srv.terminate()
n = sum(1 for _, c in R if c)
print(f'{n}/{len(R)} passed')
sys.exit(0 if n == len(R) else 1)
