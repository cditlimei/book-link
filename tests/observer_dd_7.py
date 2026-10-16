# 第 9 章方案第 7 条：兜底（作答记录 / 自动退回 / 家长「练习难度」卡）+ 第 5 条第 0 步（重做卡只记录先看讲解 pk:1）
import subprocess, time, json, socket, sys, traceback
from playwright.sync_api import sync_playwright

def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p
PORT = free_port()
srv = subprocess.Popen(['python3', '-m', 'http.server', str(PORT), '-d', '/home/coder/book-link'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
R = []
def ok(name, cond, extra=''):
    R.append((name, bool(cond))); print(('PASS ' if cond else 'FAIL ') + name, extra if not cond else '')

TODAY = '2026-10-22'
try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Shanghai')
        ctx.clock.install(time=TODAY + 'T20:00:00+08:00')
        ctx.route('https://api.github.com/**', lambda r: r.fulfill(status=404, body='{}'))
        pg = ctx.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        ev = lambda c: pg.evaluate('(c)=>(0,eval)(c)', c)
        pg.goto(f'http://localhost:{PORT}/observer/index.html'); pg.wait_for_timeout(1500)
        for _ in range(40):
            if ev("!!(LIB.words && LIB.words.words && LIB.recite && LIB.recite.items)"): break
            pg.wait_for_timeout(250)
        ok('0 词库和背诵库已加载', ev("!!(LIB.words && LIB.recite)"))
        ok('0b 固定时钟', ev("today()") == TODAY, ev("today()"))
        rc = lambda: ev("RC = {}; 0")
        # 造某个形态的单词记录：days = [(日期, 次数, 对的次数)]，每次一个不同的词
        def mk_word_events(k, days, tag='t'):
            js = []
            for i, (d, n, m) in enumerate(days):
                for j in range(n):
                    js.append(f"DB.words['zz{tag}{i}_{j}'] = {{box:1, first:'{d}', hist:[{{d:'{d}', ok:{'true' if j < m else 'false'}, k:'{k}', ty:1}}], u:now()}};")
            ev(' '.join(js) + ' 0'); rc()
        def clear_words(): ev("for (const k of Object.keys(DB.words)) if (k.startsWith('zz')) delete DB.words[k]; 0"); rc()
        FR = lambda k, t: ev(f"JSON.stringify(featRetreatAt('{k}', '{t}'))")

        # ===== 1. 自动退回边界 =====
        clear_words(); mk_word_events('ear', [('2026-10-17', 4, 0), ('2026-10-18', 4, 0), ('2026-10-19', 3, 0)])
        ok('1 11 次（3 晚全错）不退回', FR('word:ear', '2026-10-20') == 'null')
        clear_words(); mk_word_events('ear', [('2026-10-17', 6, 0), ('2026-10-18', 6, 0)])
        ok('1b 12 次跨 2 晚不退回', FR('word:ear', '2026-10-19') == 'null')
        clear_words(); mk_word_events('ear', [('2026-10-17', 4, 2), ('2026-10-18', 4, 2), ('2026-10-19', 4, 3)])   # 7/12 = 58%
        r = json.loads(FR('word:ear', '2026-10-20') or 'null')
        ok('1c 12 次跨 3 晚、58% → 退回 7 天', r == {'from': '2026-10-20', 'to': '2026-10-26'}, json.dumps(r))
        ok('1d 退回第 7 天仍在退回', FR('word:ear', '2026-10-26') != 'null')
        ok('1e 7 天后再试', FR('word:ear', '2026-10-27') == 'null')
        clear_words(); mk_word_events('ear', [('2026-10-17', 4, 3), ('2026-10-18', 4, 2), ('2026-10-19', 4, 3)])   # 8/12 = 67%
        ok('1f 正确率 67% 不退回', FR('word:ear', '2026-10-20') == 'null')
        clear_words(); mk_word_events('ear', [('2026-10-10', 6, 0), ('2026-10-12', 6, 0), ('2026-10-14', 6, 0)])
        ok('1g 上线日之前的记录不算', FR('word:ear', '2026-10-15') == 'null' and FR('word:ear', '2026-10-18') == 'null')
        # 再试头 3 晚不触发：10-27 再试，10-27/28/29 又全错 → 10-28、10-29、10-30 都不退回（10-30 的窗口里只有 2 晚... 10-31 才退回）
        clear_words(); mk_word_events('ear', [('2026-10-17', 4, 0), ('2026-10-18', 4, 0), ('2026-10-19', 4, 0), ('2026-10-27', 5, 0), ('2026-10-28', 5, 0), ('2026-10-29', 5, 0)])
        ok('1h 第一次退回 10-20~10-26', json.loads(FR('word:ear', '2026-10-20'))['to'] == '2026-10-26')
        ok('1i 再试头 3 晚（10-27~10-29）不触发', all(FR('word:ear', d) == 'null' for d in ['2026-10-27', '2026-10-28', '2026-10-29']))
        r = json.loads(FR('word:ear', '2026-10-30') or 'null')
        ok('1j 头 3 晚过后再触发', r == {'from': '2026-10-30', 'to': '2026-11-05'}, json.dumps(r))
        # 今天的记录不算进窗口（当晚不会中途换题面）
        clear_words(); mk_word_events('ear', [('2026-10-20', 4, 0), ('2026-10-21', 4, 0), ('2026-10-22', 4, 0)])
        ok('1k 今天的作答不参与当天判断', FR('word:ear', '2026-10-22') == 'null')
        # 自评不算客观：只有 pj:1 没打字也没后续拼写的不产生事件
        clear_words(); ev("for (let i = 0; i < 15; i++) DB.words['zzpj' + i] = {box:0, first:'2026-10-18', hist:[{d:'2026-1' + '0-1' + (7 + i % 3), ok:false, pj:1}], u:now()}; 0"); rc()
        ok('2 自评（没拼）不算客观对错', ev("featEvents('wordPj').length") == 0)
        ev("for (let i = 0; i < 15; i++) DB.words['zzpj' + i].hist.push({d:'2026-10-2' + (i % 2), ok:false, ty:1}); 0"); rc()
        ok('2b 说想出来了 → 后来拼的结果算客观', ev("featEvents('wordPj').length") == 15)
        ok('2c 先表态 15 次全错 → 退回', ev("!!featRetreat('wordPj')"))
        # 听讲解自报：不进退回
        ok('2d 听讲解（自报）没有退回键', ev("FEAT_KEYS().includes('tingQA')") is False)

        # ===== 3. 退回后各入口回到旧做法 =====
        # 3a 单词先表态退回 → 不要求拼的卡只有一个「翻面看答案」
        ev("state.tab = 'learn'; state.learn = {view:'card'}; render(); 0"); pg.wait_for_timeout(200)
        cw = ev("(() => { const w = curWord(); return w && !needSpell(w, wState(w)) && wCardForm(w, wState(w)).f === 'cn' ? w.w : null })()")
        ok('3 有一张不要求拼的新词卡', bool(cw), str(cw))
        ok('3b 退回后只有「翻面看答案」', pg.locator('[data-act=wflip][data-pj]').count() == 0 and '翻面看答案' in pg.inner_text('#main'))
        pg.click('[data-act=wflip]'); pg.wait_for_timeout(200)
        hw = pg.locator('details:has(summary:text-is("怎么背")) p').text_content()
        ok('3b2 退回后「怎么背」也说翻面看答案', '再点「翻面看答案」对答案' in hw and '想出来了」或「想不起来' not in hw, hw)
        ok('3c 翻面后自己判（旧流程）', pg.locator('[data-act=wmark][data-v="1"]').count() == 1)
        pg.click('[data-act=wmark][data-v="1"]'); pg.wait_for_timeout(200)
        h = ev(f"DB.words['{cw.lower()}'].hist.slice(-1)[0]")
        ok('3d 旧流程记录没有 pj', 'pj' not in h, json.dumps(h))
        clear_words(); ev("for (const k of Object.keys(DB.words)) delete DB.words[k]; 0"); rc()
        ev("state.learn = {view:'card'}; render(); 0"); pg.wait_for_timeout(200)
        ok('3e 不退回时仍是先表态两个键', pg.locator('[data-act=wflip][data-pj="1"]').count() == 1 and pg.locator('[data-act=wflip][data-pj="0"]').count() == 1)
        hw = pg.locator('details:has(summary:text-is("怎么背")) p').text_content()
        ok('3e2 不退回：「怎么背」照旧', '再点「想出来了」或「想不起来」翻面对答案' in hw and '有时是课文里的原句填空，有时只念发音让你拼' in hw and '填空和听写要先拼出来' in hw, hw)
        RET = "{from:'2026-10-20', to:'2026-10-26'}"
        ev(f"RC['fr|word:cloze|' + today()] = {RET}; RC['fr|word:ear|' + today()] = {RET}; 0")   # render 会清 RC，这里直接拼卡片
        hw = ev("(() => { const d = document.createElement('div'); d.innerHTML = vWordCard(); return [...d.querySelectorAll('details')].find(x => x.querySelector('summary').textContent === '怎么背').querySelector('p').textContent; })()")
        ok('3e3 填空和听音都退回：「怎么背」不再说题面会换', '题面会换' not in hw and '填空' not in hw and '听写' not in hw, hw)
        rc(); ev(f"RC['fr|word:ear|' + today()] = {RET}; 0")   # render 会清 RC，这里直接拼卡片
        hw = ev("(() => { const d = document.createElement('div'); d.innerHTML = vWordCard(); return [...d.querySelectorAll('details')].find(x => x.querySelector('summary').textContent === '怎么背').querySelector('p').textContent; })()")
        ok('3e4 只退回听音：只写原句填空', '有时是课文里的原句填空，最后都要能看中文拼出来。填空要先拼出来' in hw and '念发音' not in hw, hw)
        rc(); ev("render(); 0")
        # 3f 听音拼写退回 → wForm 不出 ear
        ev("wVoiceOK = () => true; 0")
        wk = ev("uniqWords().find(w => !w.u && !wLong(w)).w")
        ev(f"DB.words['{wk.lower()}'] = {{box:1, first:'2026-10-18', due:today(), hist:[{{d:'2026-10-18', ok:true}}], u:now()}}; 0"); rc()
        f0 = ev(f"(w => wForm(w, wState(w)).f)(uniqWords().find(x => x.w === {json.dumps(wk)}))")
        ok('3f 不退回：上次看中文对了 → 这次听写', f0 == 'ear', f0)
        mk_word_events('ear', [('2026-10-18', 4, 0), ('2026-10-19', 4, 0), ('2026-10-20', 4, 0)], 'e')
        f1 = ev(f"(w => wForm(w, wState(w)).f)(uniqWords().find(x => x.w === {json.dumps(wk)}))")
        ok('3g 听写退回 → 换回看中文', f1 == 'cn', f1)
        clear_words()
        # 3h 同类题找错步退回 → 只出正常求解；专项换问法不再要求
        ev("DB.settings.varForm = true; 0")
        ok('3h 不退回：数学同类题会出找错步', ev("nextForm('sx', ['solve'])") == 'finderr')
        ev("DB.items.push({id:'zzv', sid:'sx', d:'2026-10-17', type:'calc', vh:[" + ','.join("{d:'2026-10-1%d', ok:false, f:'finderr'}" % (7 + i % 3) for i in range(12)) + "], hist:[], u:now()}); 0"); rc()
        ok('3i 找错步 12 道全错 → 退回', ev("!!featRetreat('var:finderr')"))
        ok('3j 退回后同类题只出正常求解', all(ev("nextForm('sx', ['solve'])") == 'solve' for _ in range(5)))
        ok('3k 退回后数学专项不加问法要求', ev("kpFormReq({sid:'sx'}, null, 5)") == '')
        ok('3l 英语问法不受数学退回影响', ev("kpFormReq({sid:'yy'}, null, 5)") != '')
        # 专项记录：有 fok 才按题算；老记录（没有 fok）不算
        ev("DB.kps['zz:k'] = {id:'zz:k', sid:'yy', kp:'k', hist:[{d:'2026-10-18', t:1, k:'drill', n:5, ok:3, forms:['trans','fix','make','trans','cloze']}, {d:'2026-10-19', t:2, k:'drill', n:5, ok:3, forms:['trans','fix','make','trans','cloze'], fok:[1,0,1,1,0]}], u:now()}; 0"); rc()
        ok('3m 专项老记录不算、新记录按题算', ev("featEvents('var:trans').length") == 2 and ev("featEvents('var:trans').filter(e => e.ok).length") == 2 and ev("featEvents('var:fix').length") == 1)
        ev("delete DB.kps['zz:k']; DB.items = DB.items.filter(x => x.id !== 'zzv'); DB.settings.varForm = false; 0"); rc()
        # 3n 背诵先背后看退回 → 打开到期篇目是原文，看原文不算偷看，检验进 FSRS 但不记 rv
        S = ev("LIB.recite.items.find(x => x.text && x.mode !== 'title' && !recSegs(x).length && x.text.length >= 2).id")
        ev(f"DB.recite['{S}'] = {{st:'can', box:1, due:today(), rev:recRev(LIB.recite.items.find(x => x.id === '{S}')), hist:[{{d:'2026-10-01', st:'voice', score:96}}], u:now()}};"
           + "for (let i = 0; i < 12; i++) DB.recite['zzr' + i] = {st:'can', box:1, hist:[{d:'2026-10-1' + (7 + i % 3), st:'voice', score:40, rv:1}], u:now()}; 0"); rc()
        ok('3n 背诵 12 次全不到 70 → 退回', ev("!!featRetreat('recHide')"))
        ev(f"state.tab='learn'; state.learn = {{}}; ACT.rpoem({{dataset:{{v:'{S}'}}}}); 0"); pg.wait_for_timeout(200)
        ok('3o 退回：到期篇目直接显示原文', ev("state.learn.pmode") == 'full' and pg.locator('.rvhide').count() == 0 and pg.locator('[data-act=pmode][data-v=hide]').count() == 0)
        ev("ACT.pmode({dataset:{v:'full'}}); 0"); pg.wait_for_timeout(100)
        ok('3p 退回：看原文不算偷看', not ev(f"recPeeked('{S}')"))
        ev("ACT.rcheck({dataset:{v:'type'}}); 0"); pg.wait_for_timeout(200)
        txt = ev(f"LIB.recite.items.find(x => x.id === '{S}').text.join('')")
        pg.fill('#rc-type', txt); pg.click('[data-act=rctype]'); pg.wait_for_timeout(600)
        hh = ev(f"DB.recite['{S}'].hist.filter(e => e.score != null).slice(-1)[0]")
        ok('3q 退回：检验照旧进复习、不记 rv / peek', 'rv' not in hh and 'peek' not in hh and ev(f"DB.recite['{S}'].hist.some(e => e.st === 'rv-ok' && e.d === today())") and ev(f"DB.recite['{S}'].due") > TODAY, json.dumps(hh))
        ev("ACT.rcclose && ACT.rcclose(); state.rcheck = null; 0")
        # ===== 4. 「需要注意」：退回提示排在作息类之后，最多 3 条 =====
        ev("for (const d of ['2026-10-16','2026-10-17','2026-10-18','2026-10-19','2026-10-20','2026-10-21']) { const dd = touchDay(d); dd.subj = dd.subj || {}; dd.subj.sx = {min: 40, intr: 'mid', u: now()}; dd.subj.yy = {min: 20, intr: 'none', u: now()}; } save(); 0"); rc()
        A = ev("JSON.stringify(attentionItems())")
        At = [x[0] for x in json.loads(A)]
        ok('4 退回提示进「需要注意」', any('先退回旧做法' in t for t in At), A)
        i_r = next((i for i, t in enumerate(At) if '先退回旧做法' in t), -1)
        i_w = max([i for i, t in enumerate(At) if '中途停下' in t or '作业时间连续偏长' in t] or [-1])
        ok('4b 排在作息类提醒之后', i_r > i_w >= 0, A)
        ok('4c 总数仍最多 3 条', len(At) <= 3, A)
        ok('4d 提示里列出退回的做法', '背诵先背后看' in At[i_r])
        ok('4e 退回提示排在最后（家长不用动手）', i_r == len(At) - 1, A)
        # 作息类 2 条 + 名著落后：退回提示让位，不挤掉要家长动手的提醒
        ev("window._rb = readBehind; readBehind = () => 30; for (const d of ['2026-10-16','2026-10-17','2026-10-18','2026-10-19','2026-10-20','2026-10-21']) DB.days[d].subj.sx.min = 160; 0"); rc()
        A2 = ev("JSON.stringify(attentionItems())"); At2 = [x[0] for x in json.loads(A2)]
        ok('4f 满 3 条时退回提示让位给名著落后', len(At2) == 3 and any('名著阅读落后' in t for t in At2) and not any('先退回旧做法' in t for t in At2), A2)
        ev("readBehind = window._rb; for (const d of ['2026-10-16','2026-10-17','2026-10-18','2026-10-19','2026-10-20','2026-10-21']) DB.days[d].subj.sx.min = 40; 0"); rc()

        # ===== 5. 家长「练习难度」卡 =====
        mk_word_events('ear', [('2026-10-19', 5, 3), ('2026-10-20', 4, 2)], 'c')
        ev("const t = DB.ting || (DB.ting = {}); t['zzseg'] = {d:'2026-10-19', n:1, h:[{d:'2026-10-19', ok:true, lat:3, t:1}, {d:'2026-10-20', ok:false, lat:5, t:2}], u:now()}; 0"); rc()
        ev("state.tab = 'me'; state.pv = 'review'; state.review = 'week'; state.week = monOf(today()); state.wkMore = true; render(); 0"); pg.wait_for_timeout(300)
        card = pg.locator('details.more .practice')
        ok('5 卡片在「看这周的详细记录」里', card.count() == 1, pg.inner_text('#main')[:400])
        ct = card.inner_text() if card.count() else ''
        ok('5b 听音拼写：先次数后比例并写分母', '单词听音拼写：做了 9 次，拼对 5 次（56%，分母是本周听音拼写的 9 次）' in ct, ct)
        ok('5c 背诵：先次数再比例', '到期复习不看原文背了 4 次，70 分以上 0 次（0%，分母是本周不看原文的复习 4 次）' in ct, ct)
        ok('5d 听讲解标明是自报', '答了 2 次' in ct and '孩子自报' in ct)
        ok('5e 上线两周内标「先不下结论」', '新功能头两周，先不下结论' in ct)
        ok('5f 底部常驻一句', '一个孩子、几周的数据，只看趋势' in ct)
        ok('5g 退回中的做法标出来', '已退回旧做法' in ct and '近 7 天做对不到六成，旧做法用到 10/26，之后再试。' in ct and '已自动退回旧做法' not in ct, ct)
        ok('5g2 正文末尾有句号', '不参与自动退回。' in ct, ct)
        ok('5g3 行标题不断行', ev("[...document.querySelectorAll('.practice b')].every(b => getComputedStyle(b).whiteSpace === 'nowrap' && b.getClientRects().length === 1)"))
        ok('5h 390 宽无横向滚动', ev("document.documentElement.scrollWidth") <= 391)
        pg.screenshot(path='/tmp/claude-1001/-home-coder/2ca55376-0a99-42c6-aa25-aa6e5d9479c8/scratchpad/ch9/i7/practice.png', full_page=True)
        ok('5i 孩子今天页没有「练习难度」', (ev("state.tab = 'today'; render(); 0") or True) and '练习难度' not in pg.inner_text('#main'))

        # ===== 6. 单词用时（只记录，不改评分）=====
        ev("for (const k of Object.keys(DB.words)) delete DB.words[k]; for (const k of Object.keys(DB.recite)) if (k.startsWith('zzr')) delete DB.recite[k]; 0"); rc()
        ev("state.tab = 'learn'; state.learn = {view:'card'}; render(); 0"); pg.wait_for_timeout(200)
        w1 = ev("curWord().w")
        ok('6 卡片显示时开始计时', ev("!!state.learn.wt && state.learn.wt.w === wordKey(curWord())"))
        pg.click('#w-spell'); pg.keyboard.type('x'); pg.keyboard.press('Backspace'); pg.keyboard.type(w1)
        ev("state.learn.wt.t0 -= 7000; 0")
        pg.click('[data-act=wflip][data-pj="1"]'); pg.wait_for_timeout(200)
        h = ev(f"DB.words['{w1.lower()}'].hist.slice(-1)[0]")
        ok('6b 记下 ms / del / spR', isinstance(h.get('ms'), int) and 7000 <= h['ms'] < 60000 and h.get('del') == 1 and isinstance(h.get('spR'), int), json.dumps(h))
        ok('6c 记完清零', ev("state.learn.wt") is None)
        pg.click('[data-act=wnext]'); pg.wait_for_timeout(200)
        w2 = ev("curWord().w"); ev("state.learn.wt.t0 -= 130000; 0")
        pg.click('[data-act=wflip][data-pj="0"]'); pg.wait_for_timeout(200)
        h2 = ev(f"DB.words['{w2.lower()}'].hist.slice(-1)[0]")
        ok('6d 超过 120 秒记 null，没打字 spR=null', 'ms' in h2 and h2['ms'] is None and h2.get('spR') is None and h2.get('del') == 0, json.dumps(h2))
        pg.click('[data-act=wnext]'); pg.wait_for_timeout(200)
        w3 = ev("curWord().w")
        ev("Object.defineProperty(document, 'visibilityState', {get: () => 'hidden', configurable: true}); document.dispatchEvent(new Event('visibilitychange')); delete document.visibilityState; 0")
        pg.wait_for_timeout(100); ev("state.tab = 'learn'; state.learn.view = 'card'; render(); 0"); pg.wait_for_timeout(200)
        if ev("curWord() && curWord().w") == w3 and pg.locator('[data-act=wflip][data-pj="0"]').count():
            pg.click('[data-act=wflip][data-pj="0"]'); pg.wait_for_timeout(200)
            h3 = ev(f"DB.words['{w3.lower()}'].hist.slice(-1)[0]")
            ok('6e 中途切到后台：这张不记用时', 'ms' not in h3 and 'del' not in h3, json.dumps(h3))
        else: ok('6e 中途切到后台：这张不记用时', False, 'card changed')
        ok('6f 用时不改评分', ev("rateOf({d:'x', ok:true, sp:true, ty:1, ms:90000, del:5, spR:80000}) === rateOf({d:'x', ok:true, sp:true, ty:1})") and ev("rateOf({d:'x', ok:true, pj:0, ms:1000}) === rateOf({d:'x', ok:true, pj:0})"))
        ev(f"(w => {{ for (let i = 0; i < 25; i++) markWord(w, i % 2 === 0, {{sp: true, ty: 1, ms: 1000, del: 0, spR: 500}}); }})(uniqWords().find(x => x.w === {json.dumps(w1)})); 0")
        ok('6g 单词 hist 上限 20', ev(f"DB.words['{w1.lower()}'].hist.length") == 20)
        # 早就会了也记用时
        ev("for (const k of Object.keys(DB.words)) delete DB.words[k]; state.learn = {view:'card'}; render(); 0"); pg.wait_for_timeout(200)
        w4 = ev("curWord().w"); pg.fill('#w-spell', w4); pg.click('[data-act=wknown]'); pg.wait_for_timeout(200)
        ok('6h 早就会了也记 ms', 'ms' in ev(f"DB.words['{w4.lower()}'].hist[0]"))
        # 同步合并：两台设备各记一条带用时的，合并后都在
        m = ev("""(() => { const A = JSON.parse(JSON.stringify(DB)), B = JSON.parse(JSON.stringify(DB));
            A.words.zzm = {box:1, hist:[{d:'2026-10-20', ok:true, ms:3000, del:0, spR:null}], u: 1}; B.words.zzm = {box:2, hist:[{d:'2026-10-21', ok:true, ms:4000, del:1, spR:900}], u: 2};
            return mergeDB(A, B).M.words.zzm.hist.length; })()""")
        ok('6i 同步合并：带用时的 hist 取并集', m == 2, str(m))
        ok('6j 老记录（没有新字段）照常回放', ev("(() => { const H = [{d:'2026-10-01', ok:true}, {d:'2026-10-03', ok:false}, {d:'2026-10-04', ok:true, sp:true}]; const a = fsReplay(H, rateOf), b = fsReplay(H.map(h => Object.assign({ms: 5000, del: 1, spR: 1}, h)), rateOf); return JSON.stringify(a) === JSON.stringify(b); })()"))

        # ===== 7. 第 5 条第 0 步：重做卡记 pk，孩子界面不变 =====
        ev("""DB.items.push({id:'zzr1', sid:'sx', d:'2026-10-18', type:'calc', conf:'sure', q:true, src:'拍照批改', stem:'计算 3+4×2', exp:'先算乘法 4×2=8，再加 3，答案 11', hist:[{d:'2026-10-19', ok:false}], box:0, due:today(), u:now()});
              DB.items.push({id:'zzr2', sid:'yy', d:'2026-10-18', type:'calc', conf:'sure', q:true, src:'拍照批改', stem:'改错 He go to school.', exp:'第三人称单数 goes', hist:[{d:'2026-10-19', ok:false}], box:0, due:today(), u:now()});
              DB.items.push({id:'zzr3', sid:'yw', d:'2026-10-18', type:'calc', conf:'sure', q:true, src:'拍照批改', stem:'默写 床前明月光', exp:'疑是地上霜', hist:[{d:'2026-10-19', ok:false}], box:0, due:today(), u:now()}); save(); 0""")
        ev("state.tab = 'errors'; state.errView = 'redo'; setTab('errors'); 0"); pg.wait_for_timeout(300)
        n_cards = pg.locator('.card.redo').count()
        ok('7 重做卡显示', n_cards >= 2, str(n_cards))
        card1 = pg.locator('.card.redo', has=pg.locator('[data-act=redo][data-v=zzr1]'))
        btns_before = card1.locator('button').all_inner_texts()
        ok('7b 讲解折叠和按钮跟以前一样', card1.locator('details summary').inner_text() == '看批改时的讲解' and btns_before == ['做对了', '还是不会'], json.dumps(btns_before, ensure_ascii=False))
        card1.locator('details summary').click(); pg.wait_for_timeout(200)
        ok('7c 展开讲解记在 state，不落库', ev("(state.redoPk || {}).zzr1") == TODAY and 'redoPk' not in ev("Object.keys(DB).join(',')"))
        ev("ACT._lastRedo = null; 0")
        pg.click('[data-act=redo][data-v=zzr1][data-ok="1"]'); pg.wait_for_timeout(300)
        h = ev("DB.items.find(x => x.id === 'zzr1').hist.slice(-1)[0]")
        ok('7d 先看讲解再点做对了 → hist pk:1', h.get('pk') == 1 and h.get('ok') is True, json.dumps(h))
        ok('7e 用过就清掉', 'zzr1' not in (ev("state.redoPk") or {}))
        ok('7f 计分不变（box 照常升）', ev("DB.items.find(x => x.id === 'zzr1').box") == 1)
        ev("ACT._lastRedo = null; 0")
        pg.click('[data-act=redo][data-v=zzr2][data-ok="1"]'); pg.wait_for_timeout(300)
        h = ev("DB.items.find(x => x.id === 'zzr2').hist.slice(-1)[0]")
        ok('7g 没展开 → 没有 pk', 'pk' not in h, json.dumps(h))
        ev("ACT._lastRedo = null; 0")
        pg.locator('.card.redo', has=pg.locator('[data-act=redo][data-v=zzr3]')).locator('details summary').click(); pg.wait_for_timeout(200)
        pg.click('[data-act=redo][data-v=zzr3][data-ok="0"]'); pg.wait_for_timeout(300)
        h = ev("DB.items.find(x => x.id === 'zzr3').hist.slice(-1)[0]")
        ok('7h 还是不会也记 pk', h.get('pk') == 1 and h.get('ok') is False, json.dumps(h))
        ok('7i 重做页没有新增文字', '先看' not in pg.inner_text('#main') and '偷看' not in pg.inner_text('#main'))
        # 拍照错题本卡（ext）：答案折叠同样挂上
        ok('7j 拍照错题本卡的答案折叠也记', ev("extCard({id:'m:zz', sid:'sx', stem:'1+1', answer:'2', src:'x', type:'calc', hist:[]}, subjById('sx')).includes('data-pk=\"m:zz\"')"))
        rc()
        pr = ev("practiceCard(monOf(today()), today())")
        ok('7k 家长卡：重做先看讲解先写次数', '带答案或讲解的重做点「做对了」2 次，其中点之前展开过讲解或答案 1 次（50%，分母是本周带答案的重做做对 2 次）。' in pr, pr[-600:])
        # 7l 最后一关（有 AI）：先看讲解 → 转同类题 → 同类题做对，hist 仍带 pk
        ev("window._ak = AI.key; window._vg = varGen; AI.key = 'x'; varGen = async () => {}; 0")
        ok('7l0 AI 可用', ev("aiReady()"))
        for zid, sb in [('zzf1', 'sx'), ('zzf2', 'yy'), ('zzf3', 'yw'), ('zzf4', 'sx')]:
            ev(f"DB.items.push({{id:'{zid}', sid:'{sb}', d:'2026-10-01', type:'calc', conf:'unsure', q:true, src:'拍照批改', stem:'计算 3+4×2 {zid}', exp:'先算乘法', hist:[{{d:'2026-10-03', ok:true}},{{d:'2026-10-10', ok:true}}], box:2, due:today(), u:now()}}); 0")
        ev("save(); state.variant = null; state.tab = 'errors'; state.errView = 'redo'; setTab('errors'); 0"); pg.wait_for_timeout(300)
        def final_open(zid, peek):
            ev("state.variant = null; render(); 0"); pg.wait_for_timeout(200)
            if peek: ev(f"(state.redoPk = state.redoPk || {{}})['{zid}'] = today(); 0")   # 展开讲解的 toggle 监听见 7c；这里重做配额已用完，直接走 ACT.redo
            ev(f"ACT._lastRedo = null; ACT.redo({{dataset:{{v:'{zid}', ok:'1'}}}}); 0"); pg.wait_for_timeout(200)
            return ev("state.variant && state.variant.final && state.variant.iid") == zid
        last = lambda zid: ev(f"DB.items.find(x => x.id === '{zid}').hist.slice(-1)[0]")
        ok('7l 最后一关转同类题，还没写 hist', final_open('zzf1', True) and ev("state.variant.pk") == 1 and last('zzf1').get('d') != TODAY)
        ev("ACT.vardone({dataset:{ok:'1'}}); 0"); pg.wait_for_timeout(200); h = last('zzf1')
        ok('7m 同类题做对 → hist pk:1 且算掌握', h.get('d') == TODAY and h.get('ok') is True and h.get('pk') == 1 and ev("DB.items.find(x => x.id === 'zzf1').done") is True, json.dumps(h))
        ok('7n 最后一关同类题做错 → 待定记录也带 pk', final_open('zzf2', True) and (ev("ACT.vardone({dataset:{ok:'0'}}); 0") == 0) and last('zzf2').get('pend') is True and last('zzf2').get('pk') == 1, json.dumps(last('zzf2')))
        ok('7o 最后一关自评（出不了题）→ 也带 pk', final_open('zzf3', True) and (ev("ACT.varself(); 0") == 0) and last('zzf3').get('pend') is True and last('zzf3').get('ok') is True and last('zzf3').get('pk') == 1, json.dumps(last('zzf3')))
        ok('7p 最后一关没展开 → 没有 pk', final_open('zzf4', False) and (ev("ACT.vardone({dataset:{ok:'1'}}); 0") == 0) and last('zzf4').get('ok') is True and 'pk' not in last('zzf4'), json.dumps(last('zzf4')))
        ev("AI.key = window._ak; varGen = window._vg; state.variant = null; DB.items = DB.items.filter(x => !x.id.startsWith('zzf')); save(); 0"); rc()

        # ===== 8. 三年数据下计算量 =====
        tm = ev("""(() => { const save0 = DB.words; DB.words = {}; const d0 = '2026-10-16';
            for (let i = 0; i < 1600; i++) { const H = []; for (let j = 0; j < 20; j++) H.push({d: addD(d0, (i * 7 + j * 50) % 1000), ok: j % 3 > 0, k: j % 2 ? 'ear' : 'cloze', ms: 4000, del: 0, spR: 900}); DB.words['zzp' + i] = {box: 1, hist: H, u: 1}; }
            RC = {}; const t0 = performance.now(); for (const k of FEAT_KEYS()) featRetreatAt(k, addD(d0, 1000)); const ms = performance.now() - t0; DB.words = save0; RC = {}; return ms; })()""")
        ok('8 3 年 3.2 万条单词记录，退回判断 < 300ms', tm < 300, '%.0fms' % tm)
        print('    featRetreat 全部做法用时 %.0f ms' % tm)
        ok('9 没有页面报错', not errs, json.dumps(errs, ensure_ascii=False))
        b.close()
except Exception:
    traceback.print_exc(); R.append(('exception', False))
finally:
    srv.terminate()
n = sum(1 for _, c in R if c); print(f'{n}/{len(R)} passed')
sys.exit(0 if n == len(R) and R else 1)
