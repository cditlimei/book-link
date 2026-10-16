# 第 9 章方案第 3 条：单词卡先表态（想出来了 / 想不起来）+ 去掉「只是手滑」直接记对（改成看清了等会儿再拼）
import subprocess, time, json, socket, sys, traceback
from playwright.sync_api import sync_playwright

def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p
PORT = free_port()
srv = subprocess.Popen(['python3', '-m', 'http.server', str(PORT), '-d', '/home/coder/book-link'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
R = []
nt = lambda h: {k: v for k, v in h.items() if k not in ('ms', 'del', 'spR')}   # 第 7 条给单词 hist 加了用时字段（只记录），比对条目内容时去掉
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
            if ev("!!(LIB.words && LIB.words.words && LIB.words.words.length)"): break
            pg.wait_for_timeout(250)
        ok('0 词库已加载', ev("!!LIB.words"))
        T = ev("today()"); ok('0b 固定时钟', T == '2026-10-14', T)
        ev("DB.words = {}; save(); 0")
        def openc():
            ev("state.tab='learn'; state.learn = {view:'card'}; render(); 0"); pg.wait_for_timeout(150)
        main = lambda: pg.inner_text('#main')
        q0 = lambda: ev("wordQueue()[0].w")
        st = lambda w: ev(f"DB.words[{json.dumps(w.lower())}] || null")
        def typ(v): pg.fill('#w-spell', v)

        # ===== 1. 新词：两个表态按钮，没有「翻面看答案」 =====
        openc()
        ok('1 有「想出来了」「想不起来」', pg.locator('[data-act=wflip][data-pj="1"]').count() == 1 and pg.locator('[data-act=wflip][data-pj="0"]').count() == 1)
        ok('1b 新词没有「翻面看答案」', '翻面看答案' not in main())
        ok('1c 新词仍有「早就会了」', pg.locator('[data-act=wknown]').count() == 1)
        ok('1d 怎么背：不再写 1、3、7、21', '1、3、7、21' not in pg.content() and '想出来了' in ev("document.querySelector('#main details').textContent"))
        ok('1e 390 宽无横向滚动', ev("document.documentElement.scrollWidth") <= 391)
        # 想不起来（没打字）→ 当场记错，翻面只剩「下一个」
        wA = q0(); pg.click('[data-act=wflip][data-pj="0"]'); pg.wait_for_timeout(150)
        s = st(wA)
        ok('2 想不起来：当场记 ok:false pj:0', s and s['hist'][-1].get('pj') == 0 and s['hist'][-1]['ok'] is False, json.dumps(s))
        ok('2b 翻面显示的是这个词', wA in main())
        ok('2c 翻面后只有「下一个」', pg.locator('[data-act=wnext]').count() == 1 and pg.locator('[data-act=wmark]').count() == 0)
        ok('2d 当晚重考', s['due'] == T and s['triesD'] == T)
        pg.click('[data-act=wnext]'); pg.wait_for_timeout(150)
        ok('2e 下一个换了词', q0() != wA and not ev("state.learn.flip"))
        ok('2f 隔几张再考', ev(f"wordQueue().findIndex(w => w.w === {json.dumps(wA)})") >= 3)

        # ===== 3. 想不起来但打对了 → 记对，评分 2（吃力）=====
        wB = q0(); typ(wB); pg.click('[data-act=wflip][data-pj="0"]'); pg.wait_for_timeout(150)
        s = st(wB); h = s['hist'][-1]
        ok('3 想不起来但拼对：ok pj:0 sp ty', h['ok'] is True and h.get('pj') == 0 and h.get('sp') and h.get('ty') == 1, json.dumps(h))
        ok('3b 评分 2：due 等于 FSRS 吃力', s['due'] == ev(f"fsStep(null, today(), 2).due") and ev(f"rateOf({json.dumps(h)})") == 2)
        ok('3c 只剩下一个', pg.locator('[data-act=wnext]').count() == 1)
        pg.click('[data-act=wnext]'); pg.wait_for_timeout(150)

        # ===== 4. 想出来了 + 打对 → 自动判对（评分 4），少点一下 =====
        wC = q0(); typ(wC); pg.click('[data-act=wflip][data-pj="1"]'); pg.wait_for_timeout(150)
        s = st(wC); h = s['hist'][-1]
        ok('4 想出来了 + 拼对：ok pj:1 sp', h['ok'] is True and h.get('pj') == 1 and h.get('sp'), json.dumps(h))
        ok('4b 评分 4', s['due'] == ev("fsStep(null, today(), 4).due"))
        ok('4c 直接下一个', pg.locator('[data-act=wnext]').count() == 1 and pg.locator('[data-act=wmark]').count() == 0)
        ok('4d 不置 sm', not s.get('sm'))
        pg.click('[data-act=wnext]'); pg.wait_for_timeout(150)

        # ===== 5. 想出来了 + 打错 → 自动判错，sm=1，提示下次要拼 =====
        wD = q0(); typ(wD + 'x'); pg.click('[data-act=wflip][data-pj="1"]'); pg.wait_for_timeout(150)
        s = st(wD); h = s['hist'][-1]
        ok('5 想出来了 + 拼错：ok:false pj:1 ty', h['ok'] is False and h.get('pj') == 1 and h.get('ty') == 1, json.dumps(h))
        ok('5b sm=1', s.get('sm') == 1)
        ok('5c 显示「下一次这个词要拼出来」', pg.locator('.wsmnote').count() == 1)
        pg.click('[data-act=wnext]'); pg.wait_for_timeout(150)

        # ===== 6. 想出来了没打字 → 翻面后「对了 / 其实不对」 =====
        wE = q0(); pg.click('[data-act=wflip][data-pj="1"]'); pg.wait_for_timeout(150)
        ok('6 没打字：还没记', st(wE) is None)
        ok('6b 按钮是「对了」「其实不对」', pg.locator('[data-act=wmark][data-v="1"]').inner_text().strip() == '对了' and '其实不对' in pg.locator('[data-act=wmark][data-v="0"]').inner_text())
        pg.click('[data-act=wmark][data-v="0"]'); pg.wait_for_timeout(150)
        s = st(wE); h = s['hist'][-1]
        ok('6c 其实不对：pj:1 ok:false，sm=1', h.get('pj') == 1 and h['ok'] is False and s.get('sm') == 1 and not h.get('ty'), json.dumps(s))
        ok('6e 其实不对：当场提示下一次要拼', ev("document.querySelector('#toast').textContent") == '下一次这个词要拼出来' and ev("document.querySelector('#toast').classList.contains('show')"))
        wF = q0(); pg.click('[data-act=wflip][data-pj="1"]'); pg.wait_for_timeout(150)
        pg.click('[data-act=wmark][data-v="1"]'); pg.wait_for_timeout(150)
        s = st(wF); h = s['hist'][-1]
        ok('6d 对了：pj:1 ok，评分 3', h.get('pj') == 1 and h['ok'] is True and s['due'] == ev("fsStep(null, today(), 3).due"), json.dumps(s))

        # ===== 7. sm 的词：必须拼；拼对后清 sm =====
        # 把新词数用满（10 个 first=今天的占位），队列只剩到期的词，方便把指定词排到第一个
        ev("for (let i = 0; i < 10; i++) DB.words['zzfill' + i] = {box: 0, hist: [], first: today(), due: '2026-12-31', u: 1}; save(); 0")
        def only(word, rec):
            ev(f"for (const k in DB.words) if (!k.startsWith('zzfill')) delete DB.words[k]; DB.words[{json.dumps(word.lower())}] = Object.assign({{u: now()}}, {json.dumps(rec)}); save(); 0")
            openc()
        only(wE, st(wE) or {})
        ok('7 前提：sm 词在队首', q0() == wE, q0())
        ok('7b sm 词要拼（placeholder）', '这一轮要拼出来' in (pg.get_attribute('#w-spell', 'placeholder') or ''))
        ok('7c sm 词没有表态按钮', pg.locator('[data-act=wflip][data-pj]').count() == 0 and pg.locator('[data-act=wflip]').count() == 1)
        pg.click('[data-act=wflip]'); pg.wait_for_timeout(150)
        ok('7d 不打字翻不了面', not ev("state.learn.flip"))
        typ(wE); pg.click('[data-act=wflip]'); pg.wait_for_timeout(150)
        ok('7e 拼对出现「拼对了 ✓」', pg.locator('[data-act=wmark][data-v="1"]').count() == 1 and '拼对了' in main())
        pg.click('[data-act=wmark][data-v="1"]'); pg.wait_for_timeout(150)
        s = st(wE); h = s['hist'][-1]
        ok('7f 拼对后清 sm，hist 带 sp ty', not s.get('sm') and h.get('sp') and h.get('ty') == 1, json.dumps(s))

        # ===== 8. box≥2 拼错：没有「只是手滑」，改「看清了，等会儿再拼一次」=====
        fs0 = ev("fsStep(fsStep(null, '2026-10-01', 3), '2026-10-05', 3)")
        W = 'apple' if ev("uniqWords().some(w => w.w === 'apple' && !w.u)") else ev("uniqWords().find(w => !w.u && /^[a-z]{5,}$/.test(w.w)).w")
        rec8 = {'box': 2, 'first': '2026-10-01', 'due': T, 'fs': fs0, 'hist': [{'d': '2026-10-01', 'ok': True}, {'d': '2026-10-05', 'ok': True}]}
        only(W, rec8)
        ok('8 前提：box2 词在队首', q0() == W, q0())
        typ(W + 'q'); pg.click('[data-act=wflip]'); pg.wait_for_timeout(150)
        c = main()
        ok('8b 没有「只是手滑」', '只是手滑' not in c and '过两天再考' not in c)
        ok('8c 有「看清了，等会儿再拼一次」和「拼错了，隔几张再考」', pg.locator('[data-act=wslip]').count() == 1 and '看清了，等会儿再拼一次' in c and '拼错了，隔几张再考' in c)
        bx = ev("[...document.querySelectorAll('[data-act=wslip],[data-act=wmark][data-v=\"0\"]')].map(b => { const r = b.getBoundingClientRect(); return {h: Math.round(r.height), top: Math.round(r.top), sw: b.scrollWidth, cw: b.clientWidth, lh: parseFloat(getComputedStyle(b).lineHeight) || 20}; })")
        ok('8c2 390 宽：两个按钮同一行、同样高、文字不折行不溢出', len(bx) == 2 and bx[0]['h'] == bx[1]['h'] and bx[0]['top'] == bx[1]['top'] and bx[0]['h'] <= 56 and all(x['sw'] <= x['cw'] for x in bx) and ev("document.documentElement.scrollWidth") <= 391, json.dumps(bx))
        pg.click('[data-act=wslip]'); pg.wait_for_timeout(150)
        s = st(W)
        ok('8d 手滑：box 不变', s['box'] == 2)
        ok('8e 手滑：fs 不变', json.dumps(s['fs'], sort_keys=True) == json.dumps(fs0, sort_keys=True))
        ok('8f 手滑：hist 记 slip、当晚重考', nt(s['hist'][-1]) == {'d': T, 'ok': False, 'slip': 1} and s['slipD'] == T and s['due'] == T and s['triesD'] == T, json.dumps(s))
        ok('8g 手滑后不算掌握、没记对', not s.get('done') and len([x for x in s['hist'] if x['d'] == T and x['ok']]) == 0)
        ok('8h 重考必须拼（needSpell 认 slipD，box 降到 0 也一样）', ev(f"needSpell({{w:'x'}}, {{box:0, slipD:today()}})") and not ev(f"needSpell({{w:'x'}}, {{box:0, slipD:'2026-10-13'}})"))
        # 隔 3 张：放几个到期复习词在前面
        ev("const ks = uniqWords().filter(w => !w.u && w.w !== %s).slice(0, 4); ks.forEach((w, i) => DB.words[wordKey(w)] = {box: 0, hist: [{d: '2026-10-10', ok: true}], first: '2026-10-10', due: today(), u: i + 1}); save(); 0" % json.dumps(W))
        ok('8i 手滑的词排在 3 张之后', ev(f"wordQueue().findIndex(w => w.w === {json.dumps(W)})") >= 3)
        ev("for (const k in DB.words) if (DB.words[k].first === '2026-10-10') delete DB.words[k]; save(); 0"); openc()
        ok('8j 重考：要拼，且不再给手滑按钮', q0() == W and '拼出来' in (pg.get_attribute('#w-spell', 'placeholder') or ''))
        typ(W + 'q'); pg.click('[data-act=wflip]'); pg.wait_for_timeout(150)
        ok('8k 当晚第二次拼错不再有手滑', pg.locator('[data-act=wslip]').count() == 0 and pg.locator('[data-act=wmark][data-v="0"]').count() == 1)
        pg.click('[data-act=wnext]') if pg.locator('[data-act=wnext]').count() else None
        # 改走：重考拼对 → box+1、af=1、按 3 分排
        only(W, dict(rec8, hist=rec8['hist'] + [{'d': T, 'ok': False, 'slip': 1}], slipD=T, triesD=T, tries=0))
        typ(W); pg.click('[data-act=wflip]'); pg.wait_for_timeout(150)
        pg.click('[data-act=wmark][data-v="1"]'); pg.wait_for_timeout(150)
        s = st(W); h = s['hist'][-1]
        ok('8l 手滑后拼对：box+1，af=1', s['box'] == 3 and h.get('af') == 1 and h.get('sp'), json.dumps(s))
        ok('8m 手滑后拼对按 3 分（不按 4）', s['due'] == ev(f"fsStep({json.dumps(fs0)}, today(), 3).due") and ev(f"fsStep({json.dumps(fs0)}, today(), 3).due") != ev(f"fsStep({json.dumps(fs0)}, today(), 4).due"))

        # ===== 9. 手滑后拼错：记一次遗忘，当晚还能再考一次，第二次错才明天 =====
        only(W, dict(rec8, hist=rec8['hist'] + [{'d': T, 'ok': False, 'slip': 1}], slipD=T, triesD=T, tries=0))
        typ(W + 'q'); pg.click('[data-act=wflip]'); pg.wait_for_timeout(150)
        pg.click('[data-act=wmark][data-v="0"]'); pg.wait_for_timeout(150)
        s = st(W)
        ok('9 手滑后拼错：box 清零，记遗忘', s['box'] == 0 and s['fs']['l'] == fs0['l'] + 1, json.dumps(s))
        ok('9b 手滑不算一次没想起来：当晚还再考', s['due'] == T and s['tries'] == 1)
        typ(W + 'q'); pg.click('[data-act=wflip]'); pg.wait_for_timeout(150)
        pg.click('[data-act=wmark][data-v="0"]'); pg.wait_for_timeout(150)
        s = st(W)
        ok('9c 第二次错 → 明天，不重复记遗忘', s['due'] == '2026-10-15' and s['fs']['l'] == fs0['l'] + 1, json.dumps(s))
        # 多日前的 tries 残留不影响手滑
        ok('9d 隔天残留 tries 被手滑清零', ev("(() => { const w = uniqWords().find(x => !x.u); DB.words[wordKey(w)] = {box: 2, hist: [], tries: 2, triesD: '2026-10-10', due: today(), u: 1}; slipWord(w); return DB.words[wordKey(w)].tries; })()") == 0)

        # ===== 10. 只要求认识的词：box≥2 / sm 都不强制拼 =====
        U = ev("(uniqWords().find(w => w.u) || {}).w || null")
        if U:
            only(U, {'box': 3, 'sm': 1, 'first': '2026-10-01', 'due': T, 'hist': [{'d': '2026-10-01', 'ok': True}]})
            ok('10 只认识的词：needSpell=false', not ev(f"needSpell(uniqWords().find(w => w.w === {json.dumps(U)}), DB.words[{json.dumps(U.lower())}])"))
            ok('10b 只认识的词：显示表态按钮', q0() == U and pg.locator('[data-act=wflip][data-pj]').count() == 2)
        else:
            ok('10 只认识的词：needSpell=false', not ev("needSpell({w:'x', u:1}, {box:3, sm:1})"))

        # ===== 11. 老记录回放结果不变 =====
        olds = [[{'d': '2026-09-01', 'ok': True}, {'d': '2026-09-03', 'ok': True, 'sp': True}, {'d': '2026-09-10', 'ok': False}, {'d': '2026-09-10', 'ok': True}],
                [{'d': '2026-09-02', 'ok': True, 'known': True}], [{'d': '2026-09-05', 'ok': False}, {'d': '2026-09-06', 'ok': True}, {'d': '2026-09-20', 'ok': True, 'sp': True}]]
        ok('11 fsReplay 老记录：rateOf 与 wordRate 一致', all(ev(f"JSON.stringify(fsReplay({json.dumps(hh)}, rateOf)) === JSON.stringify(fsReplay({json.dumps(hh)}, wordRate))") for hh in olds))
        ok('11b rateOf 各档', ev("[rateOf({ok:false}), rateOf({ok:true,pj:0,sp:true}), rateOf({ok:true,sp:true}), rateOf({ok:true}), rateOf({ok:true,pj:1}), rateOf({ok:false,slip:1}), rateOf({ok:true,sp:true,af:1}), rateOf({ok:true,known:true})].join()") == '1,2,4,3,3,0,3,4')
        ok('11c 回放跳过手滑', ev("JSON.stringify(fsReplay([{d:'2026-09-01',ok:true},{d:'2026-09-03',ok:false,slip:1}], rateOf)) === JSON.stringify(fsReplay([{d:'2026-09-01',ok:true}], rateOf))"))
        ok('11d markWord 兼容布尔第三参', ev("(() => { const w = uniqWords().find(x => !x.u && !DB.words[wordKey(x)]); markWord(w, true, true); const h = DB.words[wordKey(w)].hist.slice(-1)[0]; return h.sp === true && h.pj === undefined && h.ty === undefined; })()"))

        # ===== 12. 同步合并：新字段并集保留 =====
        m = ev("""(() => { const a = {words: {abc: {box: 1, hist: [{d:'2026-10-13', ok:false, pj:1, ty:1}], sm: 1, u: 10}}}, b = {words: {abc: {box: 2, hist: [{d:'2026-10-14', ok:false, slip:1}], slipD:'2026-10-14', u: 20}}};
          const M = mergeDB(Object.assign(fresh(), a), Object.assign(fresh(), b)).M.words.abc; return M; })()""")
        ok('12 合并：hist 并集保留 pj/ty/slip', len(m['hist']) == 2 and m['hist'][0].get('pj') == 1 and m['hist'][1].get('slip') == 1, json.dumps(m))
        ok('12b 合并：整条按 u 取新的（slipD）', m.get('slipD') == '2026-10-14')

        # ===== 13. 家长统计：≥10 次才显示 =====
        ev("""DB.words = {}; const ws = uniqWords().filter(w => !w.u).slice(0, 12);
          ws.forEach((w, i) => { const H = [{d:'2026-10-0' + (1 + i % 9), ok: i % 3 !== 0, pj: 1}];
            if (i < 4) H.push({d:'2026-10-12', ok: true, sp: true, ty: 1});          // 后来拼对
            else if (i < 6) H.push({d:'2026-10-12', ok: false, slip: 1});          // 后来手滑 = 拼错
            else if (i === 6) H[0].ty = 1;                                           // 当场打字判
            DB.words[wordKey(w)] = {box: 1, hist: H, u: 1}; });
          DB.words.zz0 = {box: 0, hist: [{d:'2026-10-11', ok:false, pj:0}, {d:'2026-10-12', ok:false, pj:0}], u: 1}; save(); 0""")
        wp = ev("wordPjStat('2026-10-01', '2026-10-14')")
        # i=6 当场判：ok = (6%3 !== 0) = false
        ok('13 统计：N=12，拼过 K=7，拼对 M=4，想不起来 2', wp == {'n': 12, 'n0': 2, 'k': 7, 'm': 4}, json.dumps(wp))
        fd = ev("(() => { try { const s = Object.assign(stats('2026-10-08', '2026-10-14'), {recDays: 7}); return findings(s, null, {}, 7).map(f => f.t).join('\\n'); } catch(e) { return 'ERR ' + e.message; } })()")
        ok('13b 详细记录里出现这一行（先写次数，带分母）', '先说「想出来了」12 次' in fd and '分母是拼过的 7 次' in fd, fd[:300])
        ev("const ks = Object.keys(DB.words).filter(k => k !== 'zz0').slice(0, 3); ks.forEach(k => delete DB.words[k]); save(); 0")
        fd = ev("(() => { try { return findings(Object.assign(stats('2026-10-08', '2026-10-14'), {recDays: 7}), null, {}, 7).map(f => f.t).join('\\n'); } catch(e) { return 'ERR ' + e.message; } })()")
        ok('13c 少于 10 次不显示', '想出来了' not in fd and not fd.startswith('ERR'), fd[:200])
        # 几轮自评「想出来了」后只拼过一次：这次拼写只配一次（配离它最近的那次表态）
        ev("DB.words = {xq: {box: 2, hist: [{d:'2026-10-02', ok:true, pj:1}, {d:'2026-10-04', ok:true, pj:1}, {d:'2026-10-11', ok:false, ty:1}], u: 1}}; save(); 0")
        ok('13d 两次自评 + 一次拼写：k=1', ev("JSON.stringify(wordPjStat('2026-10-01', '2026-10-14'))") == json.dumps({'n': 2, 'n0': 0, 'k': 1, 'm': 0}, separators=(',', ':')), ev("JSON.stringify(wordPjStat('2026-10-01', '2026-10-14'))"))
        ev("DB.words = {xq: {box: 2, hist: [{d:'2026-10-02', ok:true, pj:1}, {d:'2026-10-05', ok:true, sp:true, ty:1}, {d:'2026-10-08', ok:true, pj:1}, {d:'2026-10-12', ok:false, slip:1}], u: 1}}; save(); 0")
        ok('13e 自评、拼写交替：各配各的', ev("JSON.stringify(wordPjStat('2026-10-01', '2026-10-14'))") == json.dumps({'n': 2, 'n0': 0, 'k': 2, 'm': 1}, separators=(',', ':')), ev("JSON.stringify(wordPjStat('2026-10-01', '2026-10-14'))"))
        # 这周没记作业（recDays=0）也给家长看单词这一行
        ev("""DB.words = {}; uniqWords().filter(w => !w.u).slice(0, 12).forEach((w, i) => DB.words[wordKey(w)] = {box: 1, hist: [{d: '2026-10-1' + (i % 4), ok: true, pj: 1}], u: 1}); save(); 0""")
        fd = ev("(() => { try { return findings(Object.assign(stats('2026-10-08', '2026-10-14'), {recDays: 0}), null, {}, 7).map(f => f.t).join('\\n'); } catch(e) { return 'ERR ' + e.message; } })()")
        ok('13f 没记作业的周：仍有「这段时间还没有记录」和单词这一行', '这段时间还没有记录' in fd and '先说「想出来了」12 次' in fd, fd[:300])

        # ===== 14. 今晚的量背够后只剩重考词：显示的和记分的是同一个词 =====
        def quota(retry_rec):
            return ev("""((rr) => { DB.words = {}; const t = today(), ws = uniqWords().filter(w => !w.u).slice(0, 40);
              for (let i = 0; i < 10; i++) DB.words['zzfill' + i] = {box: 0, hist: [], first: t, due: '2026-12-31', u: 1};
              for (let i = 0; i < wordsTonight() - 1; i++) DB.words[wordKey(ws[i])] = {box: 1, hist: [{d: t, ok: true}], first: '2026-10-01', due: '2026-10-20', u: 5};
              const R = ws[30], Y = ws[31];
              DB.words[wordKey(R)] = Object.assign({first: '2026-10-01', due: t, triesD: t, tries: 1, u: 9}, rr);
              DB.words[wordKey(Y)] = {box: 1, hist: [{d: '2026-10-10', ok: true}], first: '2026-10-10', due: t, u: 2};
              save(); state.tab = 'learn'; state.learn = {view: 'card'}; render();
              return {R: R.w, Y: Y.w, rcn: shortCn(R.cn), q0: wordQueue()[0].w, cur: curWord().w, done: wordsDoneToday(), tonight: wordsTonight()}; })(%s)""" % json.dumps(retry_rec))
        r = quota({'box': 0, 'hist': [{'d': '2026-10-01', 'ok': True}, {'d': T, 'ok': False}]})
        pg.wait_for_timeout(150)
        ok('14 前提：到量、队首是没背的复习词、卡片显示重考词', r['done'] >= r['tonight'] and r['q0'] == r['Y'] and r['cur'] == r['R'], json.dumps(r, ensure_ascii=False))
        yh0 = json.dumps(st(r['Y'])['hist'])
        pg.click('[data-act=wflip][data-pj="0"]'); pg.wait_for_timeout(150)
        sR, sY = st(r['R']), st(r['Y'])
        ok('14b 想不起来记在显示的重考词上', nt(sR['hist'][-1]) == {'d': T, 'ok': False, 'pj': 0} and json.dumps(sY['hist']) == yh0, json.dumps([sR['hist'], sY['hist']]))
        ok('14c 翻面显示的就是这个词', r['R'] in main() and r['Y'] not in main())
        pg.click('[data-act=wnext]'); pg.wait_for_timeout(150)
        # 想出来了没打字 → 其实不对：也记在重考词上
        r = quota({'box': 0, 'hist': [{'d': '2026-10-01', 'ok': True}, {'d': T, 'ok': False}]}); pg.wait_for_timeout(150)
        pg.click('[data-act=wflip][data-pj="1"]'); pg.wait_for_timeout(150)
        ok('14d 想出来了：翻面是重考词', r['R'] in main() and r['Y'] not in main())
        pg.click('[data-act=wmark][data-v="0"]'); pg.wait_for_timeout(150)
        ok('14e 其实不对记在重考词上', st(r['R'])['hist'][-1].get('pj') == 1 and st(r['R']).get('sm') == 1 and json.dumps(st(r['Y'])['hist']) == yh0)
        # 重考词要拼（手滑后），队首复习词不要拼：拦截按显示的词判，手滑也记在它身上
        r = quota({'box': 2, 'slipD': T, 'hist': [{'d': '2026-10-01', 'ok': True}, {'d': '2026-10-05', 'ok': True}, {'d': T, 'ok': False, 'slip': 1}]}); pg.wait_for_timeout(150)
        ok('14f 显示的重考词要拼', '拼出来' in (pg.get_attribute('#w-spell', 'placeholder') or '') and pg.locator('[data-act=wflip][data-pj]').count() == 0)
        pg.click('[data-act=wflip]'); pg.wait_for_timeout(150)
        ok('14g 没打字翻不了面（拦截按显示的词判）', not ev("state.learn.flip"))
        typ(r['R'] + 'q'); pg.click('[data-act=wflip]'); pg.wait_for_timeout(150)
        pg.click('[data-act=wmark][data-v="0"]'); pg.wait_for_timeout(150)
        ok('14h 拼错记在重考词上，复习词不动', st(r['R'])['hist'][-1].get('ty') == 1 and st(r['R'])['box'] == 0 and json.dumps(st(r['Y'])['hist']) == yh0, json.dumps([st(r['R']), st(r['Y'])]))
        r = quota({'box': 3, 'hist': [{'d': '2026-10-01', 'ok': True}, {'d': '2026-10-05', 'ok': True}, {'d': '2026-10-09', 'ok': True}, {'d': T, 'ok': False}]}); pg.wait_for_timeout(150)
        typ(r['R'] + 'q'); pg.click('[data-act=wflip]'); pg.wait_for_timeout(150)
        pg.click('[data-act=wslip]'); pg.wait_for_timeout(150)
        ok('14i 手滑记在重考词上', st(r['R'])['hist'][-1].get('slip') == 1 and json.dumps(st(r['Y'])['hist']) == yh0)

        ok('99 无页面报错', not errs, ' | '.join(errs[:3]))
        b.close()
except Exception:
    traceback.print_exc(); R.append(('exception', False))
finally:
    srv.terminate()
n = sum(1 for _, v in R if v); print(f'{n}/{len(R)} passed')
sys.exit(0 if n == len(R) and R else 1)
