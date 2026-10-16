# 第 9 章方案第 6 条：同类题和专项换问法（数学找错步 / 英语四种问法轮换），默认关闭的家长开关 + aiSelfTest 两步检查
# 不真调智谱：ctx.route 拦 open.bigmodel.cn，按系统提示词分辨是哪种请求，返回打桩内容，并把每次请求的提示词记下来做断言
import subprocess, time, json, socket, sys, traceback
from playwright.sync_api import sync_playwright

def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p
PORT = free_port()
srv = subprocess.Popen(['python3', '-m', 'http.server', str(PORT), '-d', '/home/coder/book-link'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
R = []
def ok(name, cond, extra=''):
    R.append((name, bool(cond))); print(('PASS ' if cond else 'FAIL ') + name, extra if not cond else '')

FINDERR_Q = '解方程 3(x-2)=x+4。\n第1步：去括号，得 3x-2=x+4\n第2步：移项，得 3x-x=4+2\n第3步：合并同类项，得 2x=6\n第4步：系数化为 1，得 x=3\n这段解答错在第几步？把这一步改对，再写出正确答案。'
MODE = {'finderr': 'good', 'drill': [], 'verify': False, 'judge': True}
LOG = []   # 每次请求的 system 内容（没有 system 就记 user）

def ai_reply(sys_txt, user_txt):
    if '只回复两个字' in user_txt: return '你好'
    if '图里写的算式' in user_txt: return '{"text":"37 + 48 = 85"}'
    if '出一道和下面同类的题' in sys_txt: return '解方程 3(x+2)=2x-1'
    if '题目给了一份分步解答，说其中有一步是错的' in sys_txt:
        return json.dumps({'err': MODE['verify'], 'step': 2 if MODE['verify'] else 0})
    if '出一道「同类题」' in sys_txt:
        if '"bad"' in sys_txt:
            if MODE['finderr'] == 'good': return json.dumps({'q': FINDERR_Q, 'bad': 1}, ensure_ascii=False)
            if MODE['finderr'] == 'rawnl': return '{"q": "' + FINDERR_Q.replace('\n', '\r\n') + '", "bad": 1}'   # 模型真实形状：字符串里直接换行，不转义
            if MODE['finderr'] == 'nostep': return json.dumps({'q': FINDERR_Q, 'bad': 7}, ensure_ascii=False)
            return '这道题是：' + FINDERR_Q   # 不是 JSON
        if '出成翻译题' in sys_txt: return '把这句话翻译成英文：他每天早上七点起床。'
        if '出成改错题' in sys_txt: return 'He go to school by bus every day.'
        if '出成造句题' in sys_txt: return '用 be good at 写一句话，说说你的朋友。'
        if '出成语境填空题' in sys_txt: return 'My sister ____ (like) music. She sings every day.'
        return '解方程 4(x+1)=2x+10'
    if '判断学生这道题做得对不对' in sys_txt:
        return json.dumps({'ok': MODE['judge'], 'hint': '第 1 步找得准，改得对'}, ensure_ascii=False)
    if '的专项练习' in sys_txt:
        d = MODE['drill']
        out = d.pop(0) if d else [{'q': '计算 %d+%d' % (i, i + 1)} for i in range(5)]
        return out if isinstance(out, str) else json.dumps(out, ensure_ascii=False)   # 字符串：原样返回（模拟带字面换行的回包）
    return '好的'

def handle(route):
    req = route.request
    try: body = json.loads(req.post_data or '{}')
    except Exception: body = {}
    msgs = body.get('messages') or []
    def txt(m):
        c = m.get('content')
        if isinstance(c, list): return ' '.join(x.get('text', '') for x in c if isinstance(x, dict))
        return c or ''
    sys_txt = ' '.join(txt(m) for m in msgs if m.get('role') == 'system')
    user_txt = ' '.join(txt(m) for m in msgs if m.get('role') == 'user')
    LOG.append(sys_txt or user_txt)
    content = ai_reply(sys_txt, user_txt)
    route.fulfill(status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'},
                  body=json.dumps({'choices': [{'message': {'content': content}}]}, ensure_ascii=False))

try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Shanghai')
        ctx.clock.install(time='2026-10-14T20:00:00+08:00')
        ctx.route('https://api.github.com/**', lambda r: r.fulfill(status=404, body='{}'))
        ctx.route('https://open.bigmodel.cn/**', handle)
        pg = ctx.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        ev = lambda c: pg.evaluate('(c)=>(0,eval)(c)', c)
        pg.goto(f'http://localhost:{PORT}/observer/index.html'); pg.wait_for_timeout(1500)
        for _ in range(60):
            if ev("!!LIB.kp"): break
            pg.wait_for_timeout(250)
        T = ev("today()"); ok('0 固定时钟', T == '2026-10-14', T)
        ok('0b 知识点表已加载', ev("!!LIB.kp && kpList('sx').length > 0 && kpList('yy').length > 0"))
        ev("AI = {key: 'test-key'}; 0")
        ok('0c AI 已就绪（打桩密钥）', ev("aiReady()"))

        def item(iid, sid, vh, **kw):
            it = dict({'id': iid, 'd': '2026-10-10', 'sid': sid, 'type': 'calc', 'tag': '去括号', 'stem': '解方程 2(x-1)=3x+4', 'conf': None,
                       'box': 1, 'due': T, 'hist': [], 'done': False, 'u': 1, 'vh': vh}, **kw)
            ev(f"(() => {{ DB.items = DB.items.filter(x => x.id !== {json.dumps(iid)}); DB.items.push({json.dumps(it, ensure_ascii=False)}); save(); }})()")
        def var(iid, extra=''):
            LOG.clear()
            ev(f"state.variant = {{iid: {json.dumps(iid)}{extra}}}; varGen(); 0")
            for _ in range(40):
                if not ev("state.variant && state.variant.busy"): break
                pg.wait_for_timeout(100)
            return ev("(() => { const V = state.variant; return {f: V.f === undefined ? '__undef' : V.f, q: V.q, bad: V.bad || 0, err: V.err || ''}; })()")
        def check(ans='第 1 步错了，应是 3x-6=x+4，x=5'):
            pg.fill('#var-ans', ans); pg.click('[data-act=varcheck]')
            for _ in range(40):
                if not ev("state.variant.busy"): break
                pg.wait_for_timeout(100)
        lastvh = lambda iid: ev(f"(findItem({json.dumps(iid)}).vh || []).slice(-1)[0] || null")
        main = lambda: pg.inner_text('#main')
        wiz = lambda: pg.inner_text('#wiz')

        # ===== 1. 默认关：行为与以前一致 =====
        ok('1 默认没有 varForm 字段，开关为关', ev("DB.settings.varForm === undefined && !varFormOn()"))
        item('t1', 'sx', [{'d': '2026-10-11', 'ok': True}])
        V = var('t1')
        ok('1b 关着：第二次练也不带问法（V.f 不存在）', V['f'] == '__undef' and V['q'] == '解方程 4(x+1)=2x+10', json.dumps(V, ensure_ascii=False))
        ok('1c 关着：出题提示词就是原来那句', len(LOG) == 1 and '只输出题目本身，不要答案、不要提示、不要解析' in LOG[0] and '找错步' not in LOG[0] and '"bad"' not in LOG[0])
        ok('1d 关着：没有「这次：」题头，原说明还在', '这次：' not in wiz() and '和原题考的是同一个地方，换了数字' in wiz())
        check('x = 3')
        h = lastvh('t1')
        ok('1e 关着：vh 记录只有 d/ok，不加 f', h is not None and sorted(h.keys()) == ['d', 'ok'], json.dumps(h))
        ev("state.variant = null; render(); 0")
        # 专项（关）
        KP = ev("kpList('sx')[0].id")
        def drill(sid, kp, n, step='drill', mode=None, extra=''):
            LOG.clear()
            ev(f"state.kpx = {{key: {json.dumps(sid + ':' + kp)}, sid: {json.dumps(sid)}, id: {json.dumps(kp)}, step: {json.dumps(step)}, mode: {json.dumps(mode)}, msgs: [], type: 'calc', stuck: '去括号漏乘'{extra}}}; kpDrillGen(state.kpx, {n}); 0")
            for _ in range(40):
                if not ev("state.kpx && state.kpx.busy"): break
                pg.wait_for_timeout(100)
            return ev("state.kpx.qs.map(q => q.f === undefined ? '__undef' : q.f)")
        def finish():
            ev("(() => { const X = state.kpx; X.qs.forEach(q => { q.res = {ok: true, hint: ''}; }); kpFinish(X); })(); 0")
            return ev(f"(DB.kps[state.kpx.key].hist || []).slice(-1)[0]")
        ev(f"delete DB.kps['sx:{KP}']; 0")
        fs = drill('sx', KP, 5)
        ok('1f 关着：专项提示词不带问法要求', len(LOG) == 1 and '问法：' not in LOG[0] and '只输出 JSON 数组：[{"q":"题目"}]' in LOG[0] and '每道 3 分钟内能做完' in LOG[0])
        ok('1g 关着：专项题目没有 f', fs == ['__undef'] * 5, json.dumps(fs))
        hh = finish()
        ok('1h 关着：drill 记录没有 forms', hh['k'] == 'drill' and 'forms' not in hh, json.dumps(hh))
        ok('1i 关着：kpx 没有 formOn', not ev("state.kpx.formOn"))
        ev("state.kpx = null; render(); 0")

        # ===== 2. 家长开关 =====
        ev("document.querySelector('#main').innerHTML = aiCard(); 0")
        ok('2 AI 卡片里有换问法开关，默认「关」选中', pg.locator('[data-act=varform][data-v="0"].on').count() == 1 and pg.locator('[data-act=varform][data-v="1"]').count() == 1)
        ok('2b 开关旁写明先过两步自检', '出找错步题' in main() and '全对的解答不判错' in main())
        pg.click('[data-act=varform][data-v="1"]'); pg.wait_for_timeout(150)
        ok('2c 点「开」：settings.varForm=true 且带 fu', ev("DB.settings.varForm === true && !!(DB.settings.fu && DB.settings.fu.varForm)"))

        # ===== 3. 同类题（开）=====
        item('t2', 'sx', [])
        V = var('t2')
        ok('3 开：这道题第一次练同类题 → 正常求解', V['f'] == 'solve' and '找错步' not in LOG[0], json.dumps(V, ensure_ascii=False))
        check('x = -6'); h = lastvh('t2')
        ok('3b 开：vh 记 f=solve', h.get('f') == 'solve', json.dumps(h))
        ev("state.variant = null; 0")
        item('t3', 'sx', [{'d': '2026-10-11', 'ok': False}])   # 老记录没有 f
        V = var('t3')
        ok('3c 第二次练（上次正常求解）→ 找错步', V['f'] == 'finderr' and V['bad'] == 1 and V['q'] == FINDERR_Q, json.dumps(V, ensure_ascii=False))
        ok('3d 找错步提示词要求标出错步（bad）', len(LOG) == 1 and '"bad"' in LOG[0] and '恰好有一步是错的' in LOG[0])
        ev("render(); 0"); pg.wait_for_timeout(100)
        ok('3e 题头小字「这次：找错步」', pg.locator('.varform').count() == 1 and '这次：找错步' in pg.inner_text('.varform'))
        ok('3e2 找错步输入框提示和专项一致（不带具体步号）', pg.get_attribute('#var-ans', 'placeholder') == '第几步错了，改成什么，答案是……', pg.get_attribute('#var-ans', 'placeholder'))
        ok('3f 错步编号不显示给孩子（只在 V.bad）', '"bad"' not in wiz() and '错在第 1 步' not in wiz())
        ok('3g 390 宽无横向滚动', ev("document.documentElement.scrollWidth") <= 391)
        check(); h = lastvh('t3')
        ok('3h vh 记 f=finderr', h.get('f') == 'finderr' and h['ok'] is True, json.dumps(h))
        ok('3i 判题提示词没动（仍是「具体的肯定」那句）', '做对时写一句具体的肯定' in LOG[-1])
        V = var('t3', ", gen: 1")   # 同一题再来：上次找错步 → 正常求解
        ok('3j 上次找错步 → 这次正常求解', V['f'] == 'solve', json.dumps(V, ensure_ascii=False))
        ev("state.variant = null; 0")
        # 最后一关 / 批改后第一道
        item('t4', 'sx', [{'d': '2026-10-11', 'ok': True}])
        V = var('t4', ", final: true")
        ok('3k 最后一关一律正常求解', V['f'] == 'solve' and '"bad"' not in LOG[0])
        V = var('t4', ", from: 'grade'")
        ok('3l 批改后第一道正常求解', V['f'] == 'solve')
        V = var('t4', ", from: 'grade', gen: 1")
        ok('3m 批改页「再来一道」可以换问法', V['f'] == 'finderr', json.dumps(V, ensure_ascii=False))
        ev("state.variant = null; 0")
        # 只有混合练习记录 → 当第一次
        item('t5', 'sx', [{'d': '2026-10-11', 'ok': True, 'mix': True}])
        ok('3n 只有混合练习记录 → 当第一次，正常求解', var('t5')['f'] == 'solve')
        # 找错步格式不对 → 退回正常求解
        for m in ['nostep', 'text']:
            MODE['finderr'] = m
            item('t3', 'sx', [{'d': '2026-10-11', 'ok': False}])
            V = var('t3')
            ok(f'3o 找错步回包不合格（{m}）→ 退回正常求解再出一道', V['f'] == 'solve' and V['q'] == '解方程 4(x+1)=2x+10' and len(LOG) == 2 and not V['err'], json.dumps(V, ensure_ascii=False))
        MODE['finderr'] = 'rawnl'
        item('t3', 'sx', [{'d': '2026-10-11', 'ok': False}])
        V = var('t3')
        ok('3o2 找错步回包字符串里直接换行（不转义）→ 照样认出找错步', V['f'] == 'finderr' and V['bad'] == 1 and V['q'] == FINDERR_Q and len(LOG) == 1, json.dumps(V, ensure_ascii=False))
        ok('3o3 找错步提示词注明换行写成 \\n', '换行写成 \\n' in LOG[0])
        MODE['finderr'] = 'good'
        ev("state.variant = null; 0")
        # 英语轮换
        item('e1', 'yy', [{'d': '2026-10-11', 'ok': True, 'f': 'fix'}], tag='一般现在时', stem='He go to school.')
        seen = set()
        for _ in range(12):
            V = var('e1'); seen.add(V['f'])
        ok('3p 英语：避开上次的「改错」，只在翻译/造句/填空里轮换', seen <= {'trans', 'make', 'cloze'} and len(seen) >= 2, json.dumps(sorted(seen)))
        V = var('e1')
        hw = {'trans': '出成翻译题', 'make': '出成造句题', 'cloze': '出成语境填空题'}[V['f']]
        ok('3q 英语提示词对应所选问法', hw in LOG[0] and '"bad"' not in LOG[0])
        ev("render(); 0"); pg.wait_for_timeout(100)
        ok('3r 英语题头写「这次：…」', '这次：' + ev("FORM_N[state.variant.f]") in wiz())
        ok('3s nextForm：数学两种交替，英语不重复上一次', ev("nextForm('sx', ['solve']) === 'finderr' && nextForm('sx', ['finderr']) === 'solve' && Array.from({length: 30}, () => nextForm('yy', ['cloze'])).every(f => f !== 'cloze' && FORMS.yy.includes(f))"))
        ev("state.variant = null; 0")
        # 不轮换的科目
        for sid in ['ls', 'yw', 'sw']:
            item('o-' + sid, sid, [{'d': '2026-10-11', 'ok': True}], type='concept')
            V = var('o-' + sid)
            ok(f'3t {sid} 不轮换：正常求解、提示词不变', V['f'] == 'solve' and '只输出题目本身' in LOG[0] and '出成' not in LOG[0])
        ev("state.variant = null; render(); 0")

        # ===== 4. 专项（开）=====
        ev(f"delete DB.kps['sx:{KP}']; 0")
        MODE['drill'] = [[{'q': '计算 1+2', 'f': 'solve'}, {'q': FINDERR_Q, 'f': 'finderr'}, {'q': '计算 3+4', 'f': 'solve'}, {'q': '计算 5+6', 'f': 'solve'}, {'q': '计算 7+8', 'f': 'bogus'}]]
        fs = drill('sx', KP, 5)
        ok('4 开：专项提示词要求至少 2 种问法、找错步最多 1 道', len(LOG) == 1 and '至少用 2 种不同的问法' in LOG[0] and '「找错步」最多 1 道' in LOG[0], LOG[0][-300:] if LOG else '')
        ok('4b 每道带 f，不认识的问法当 solve', fs == ['solve', 'finderr', 'solve', 'solve', 'solve'], json.dumps(fs))
        ok('4c 找错步题保留完整解答（不被 400 字截断规则误伤）', ev("state.kpx.qs[1].q") == FINDERR_Q)
        ev("state.kpx.qi = 1; state.tab = 'learn'; render(); 0"); pg.wait_for_timeout(100)
        ok('4d 题头「这次：找错步」', '这次：找错步' in wiz(), wiz()[:200])
        ok('4d2 题头接着写怎么做（FORM_TIP）', '这次：找错步。先读懂这段解答' in wiz(), wiz()[:200])
        ok('4e 390 宽无横向滚动', ev("document.documentElement.scrollWidth") <= 391)
        hh = finish()
        ok('4f drill 记录带 forms', hh.get('forms') == ['solve', 'finderr', 'solve', 'solve', 'solve'], json.dumps(hh))
        ok('4g 过关线不变：5 道对 4 道', ev("kpNeed(5)") == 4 and hh['n'] == 5)
        # 违规：两道找错步 → 重出一次
        MODE['drill'] = [[{'q': 'a1', 'f': 'finderr'}, {'q': 'a2', 'f': 'finderr'}, {'q': 'a3', 'f': 'solve'}, {'q': 'a4', 'f': 'solve'}, {'q': 'a5', 'f': 'solve'}],
                         [{'q': 'b1', 'f': 'finderr'}, {'q': 'b2', 'f': 'solve'}, {'q': 'b3', 'f': 'solve'}, {'q': 'b4', 'f': 'solve'}, {'q': 'b5', 'f': 'solve'}]]
        fs = drill('sx', KP, 5)
        ok('4h 找错步超过 1 道：重出一次，用第二批', len(LOG) == 2 and ev("state.kpx.qs[0].q") == 'b1', f'{len(LOG)} {json.dumps(fs)}')
        MODE['drill'] = [[{'q': 'c%d' % i, 'f': 'solve'} for i in range(5)], [{'q': 'd%d' % i, 'f': 'solve'} for i in range(5)]]
        fs = drill('sx', KP, 5)
        ok('4i 只有一种问法：最多重出一次，还不行照用', len(LOG) == 2 and len(fs) == 5)
        # 回包字符串里直接换行（模型真实输出）：5 道照样出来
        raw = '[' + ', '.join('{"q": "%s", "f": "%s"}' % (q.replace('\n', '\n'), f) for q, f in [('计算 1+2', 'solve'), (FINDERR_Q, 'finderr'), ('计算 3+4\n写出步骤', 'solve'), ('计算 5+6', 'solve'), ('计算 7+8', 'solve')]) + ']'
        MODE['drill'] = [raw]
        fs = drill('sx', KP, 5)
        ok('4i2 专项回包含字面换行 → 5 道都出来', len(LOG) == 1 and fs == ['solve', 'finderr', 'solve', 'solve', 'solve'] and ev("state.kpx.qs[1].q") == FINDERR_Q and not ev("state.kpx.err"), json.dumps(fs))
        ok('4i3 专项提示词注明换行写成 \\n', '要换行就写成 \\n' in LOG[0])
        # 违规判断放在剔除「和原题太像」之后
        item('kpold', 'sx', [], kp=KP, stem='在数轴上画出 -3 和 5，并计算 (-3)+5 的值')   # 给这个知识点挂一道有题面的原题
        OLD = ev(f"kpCtx({{sid: 'sx', id: {json.dumps(KP)}}}).k.its.map(i => i.stem || '').filter(Boolean)")
        if OLD:
            MODE['drill'] = [[{'q': OLD[0], 'f': 'finderr'}] + [{'q': 'e%d' % i, 'f': 'solve'} for i in range(5)],
                             [{'q': 'g1', 'f': 'finderr'}] + [{'q': 'g%d' % i, 'f': 'solve'} for i in range(2, 6)]]
            fs = drill('sx', KP, 5)
            ok('4i4 唯一一道找错步因和原题太像被剔掉 → 剩下全是正常求解，重出一次', len(LOG) == 2 and ev("state.kpx.qs[0].q") == 'g1', f'{len(LOG)} {json.dumps(fs)}')
        else:
            ok('4i4 准备原题题面失败', False)
        # 到了当晚 AI 时长就不再重出
        ev("window._tm = DB.settings.tutorMin; DB.settings.tutorMin = -1; 0")
        MODE['drill'] = [[{'q': 'h%d' % i, 'f': 'solve'} for i in range(5)], [{'q': 'i%d' % i, 'f': 'solve'} for i in range(5)]]
        fs = drill('sx', KP, 5, extra=', t0: Date.now() - 1000')
        ok('4i5 第一次出题后已到时长上限 → 不重出', len(LOG) == 1 and ev("state.kpx.limit === true") and len(fs) == 5, f'{len(LOG)}')
        ev("DB.settings.tutorMin = window._tm; if (DB.settings.tutorMin === undefined) delete DB.settings.tutorMin; 0")
        ev("state.kpx = null; 0")
        # 回查：用上一轮没用过的问法
        ev(f"DB.kps['sx:{KP}'] = {{id: 'sx:{KP}', sid: 'sx', kp: '{KP}', hist: [{{d: '2026-10-07', t: 1, k: 'drill', n: 5, ok: 5, type: 'calc', forms: ['solve','solve','solve','solve','solve']}}], u: 1}}; 0")
        MODE['drill'] = [[{'q': FINDERR_Q, 'f': 'solve'}]]
        fs = drill('sx', KP, 1, step='check', mode='check')
        ok('4j 回查：上一轮全是正常求解 → 这次找错步', fs == ['finderr'] and '这道题用「找错步」' in LOG[0], json.dumps(fs))
        hh = finish()
        ok('4k check 记录带 forms', hh['k'] == 'check' and hh.get('forms') == ['finderr'], json.dumps(hh))
        ev(f"DB.kps['sx:{KP}'].hist.push({{d: '2026-10-14', t: 9e15, k: 'drill', n: 5, ok: 5, forms: ['finderr','solve','solve','solve','solve']}}); 0")
        ok('4l 回查：上一轮两种都用过 → 避开最后一道的问法', ev(f"nextForm('sx', kpLastForms(kpState('sx', '{KP}')))") == 'finderr')
        ev(f"DB.kps['sx:{KP}'].hist.push({{d: '2026-10-14', t: 9e15 + 1, k: 'drill', n: 5, ok: 5}}); 0")
        ok('4m 回查：最近一轮是关着时练的（没有 forms）→ 往前找有 forms 的那轮', ev(f"kpLastForms(kpState('sx', '{KP}'))") == ['finderr', 'solve', 'solve', 'solve', 'solve'])
        # 英语专项、语文不轮换
        KPY = ev("kpList('yy')[0].id")
        MODE['drill'] = [[{'q': 'y1', 'f': 'trans'}, {'q': 'y2', 'f': 'fix'}, {'q': 'y3', 'f': 'cloze'}, {'q': 'y4', 'f': 'make'}, {'q': 'y5', 'f': 'trans'}]]
        fs = drill('yy', KPY, 5)
        ok('4n 英语专项：四种问法都在提示词里，改错最多 1 道', all(w in LOG[0] for w in ['trans=翻译', 'fix=改错', 'make=造句', 'cloze=语境填空', '「改错」最多 1 道']) and fs == ['trans', 'fix', 'cloze', 'make', 'trans'])
        # 英语漏标或标了不认识的问法 → 记 unk，不算一种问法（不会被当成 solve 凑够 2 种）
        MODE['drill'] = [[{'q': 'u1', 'f': 'trans'}, {'q': 'u2'}, {'q': 'u3', 'f': 'solve'}, {'q': 'u4'}, {'q': 'u5'}],
                         [{'q': 'w1', 'f': 'trans'}, {'q': 'w2'}, {'q': 'w3'}, {'q': 'w4'}, {'q': 'w5'}]]
        fs = drill('yy', KPY, 5)
        ok('4n2 英语没标问法记 unk，只有 1 种合法问法 → 重出一次', len(LOG) == 2 and fs == ['trans', 'unk', 'unk', 'unk', 'unk'], f'{len(LOG)} {json.dumps(fs)}')
        ok('4n3 kpFormsOk 只数合法问法', ev("!kpFormsOk([{f:'trans'},{f:'unk'},{f:'unk'}], 3, 'yy') && kpFormsOk([{f:'trans'},{f:'unk'},{f:'make'}], 3, 'yy') && !kpFormsOk([{f:'trans'},{f:'solve'}], 2, 'yy')"))
        ev("state.kpx.qi = 1; state.tab = 'learn'; render(); 0"); pg.wait_for_timeout(100)
        ok('4n4 unk 题头不出现「这次：」也没有 undefined', '这次：' not in wiz() and 'undefined' not in wiz(), wiz()[:200])
        hh = finish()
        ok('4n5 英语 drill 记录里没有 solve', 'solve' not in (hh.get('forms') or []) and hh.get('forms') == ['trans', 'unk', 'unk', 'unk', 'unk'], json.dumps(hh))
        if ev("kpList('yw').length > 0"):
            KPW = ev("kpList('yw')[0].id"); MODE['drill'] = []
            fs = drill('yw', KPW, 5)
            ok('4o 语文专项不轮换：提示词不变、没有 f', '问法：' not in LOG[0] and fs == ['__undef'] * 5)
        else:
            ok('4o 语文知识点表为空（跳过）', True)
        ev("state.kpx = null; render(); 0")

        # ===== 5. aiSelfTest 两步 =====
        def selftest():
            ev("aiSelfTest(); 0")
            for _ in range(60):
                if ev("state.aiTest && state.aiTest.length >= 6 && !state.aiTest.some(r => r.st === '…')"): break
                pg.wait_for_timeout(100)
            return ev("state.aiTest.map(r => [r.name, r.st, r.msg || ''])")
        rows = selftest()
        names = [r[0] for r in rows]
        ok('5 自检多了两步', '出找错步题（标出错在哪一步）' in names and '全对的解答不判错（找错步）' in names, json.dumps(names, ensure_ascii=False))
        st = {r[0]: r for r in rows}
        ok('5b 打桩正常时两步都过', st['出找错步题（标出错在哪一步）'][1] == 'ok' and st['全对的解答不判错（找错步）'][1] == 'ok' and '第 1 步' in st['出找错步题（标出错在哪一步）'][2], json.dumps(rows, ensure_ascii=False))
        ok('5c 原有三步照旧通过', all(st[n][1] == 'ok' for n in ['文字对话（AI 老师）', '看图识别（拍照错题、成绩单）', '出同类题']))
        vreq = [l for l in LOG if '题目给了一份分步解答' in l]
        ok('5d 第二步给的是一份全对的解答', len(vreq) >= 1)
        MODE['verify'] = True
        rows = selftest(); st = {r[0]: r for r in rows}
        ok('5e 模型把全对的解答判成有错 → 第二步不过', st['全对的解答不判错（找错步）'][1] == 'bad' and '先别打开' in st['全对的解答不判错（找错步）'][2])
        MODE['verify'] = False; MODE['finderr'] = 'nostep'
        rows = selftest(); st = {r[0]: r for r in rows}
        ok('5f 出的找错步题标的步骤不在题里 → 第一步不过', st['出找错步题（标出错在哪一步）'][1] == 'bad')
        MODE['finderr'] = 'text'
        rows = selftest(); st = {r[0]: r for r in rows}
        ok('5g 回包不是 JSON → 第一步不过', st['出找错步题（标出错在哪一步）'][1] == 'bad')
        MODE['finderr'] = 'good'
        ev("document.querySelector('#main').innerHTML = aiCard(); 0")
        ok('5h 自检结果显示在 AI 卡片里', '出找错步题' in main() and '全对的解答不判错' in main())

        # ===== 6. 同步合并 / 老数据 =====
        m = ev("""(() => { const L = migrate(JSON.parse(JSON.stringify(fresh()))), Rr = JSON.parse(JSON.stringify(DB));
          const a = mergeDB(L, Rr).M.settings.varForm, b = mergeDB(Rr, L).M.settings.varForm;
          const old = migrate({settings: {u: 5}, items: []});
          const it = findItem('t3'), x = JSON.parse(JSON.stringify(it)), y = JSON.parse(JSON.stringify(it)); y.vh = y.vh.concat([{d: '2026-10-14', ok: false, f: 'solve'}]); y.u = x.u + 10;
          const L2 = JSON.parse(JSON.stringify(DB)), R2 = JSON.parse(JSON.stringify(DB)); L2.items = [x]; R2.items = [y];
          const mi = mergeDB(L2, R2).M.items.find(z => z.id === 't3');
          return {a, b, old: old.settings.varForm === undefined, oldOn: (() => { const s = DB.settings; DB.settings = old.settings; const v = varFormOn(); DB.settings = s; return v; })(), mf: mi.vh.slice(-1)[0].f}; })()""")
        ok('6 另一台设备开了开关：合并后两边都是开', m['a'] is True and m['b'] is True, json.dumps(m))
        ok('6b 老数据没有 varForm：迁移后仍是关', m['old'] and m['oldOn'] is False)
        ok('6c vh 里的 f 随错题记录合并保留', m['mf'] == 'solve')
        ev("setSetting('varForm', false); save(); 0")
        ok('6d 再关上：varFormOn 为假，同类题回到老样子', not ev("varFormOn()") and var('t3')['f'] == '__undef')
        ev("state.variant = null; render(); 0")
        ok('7 页面没有报错', not errs, json.dumps(errs[:3], ensure_ascii=False))
        b.close()
except Exception:
    traceback.print_exc(); R.append(('exception', False))
finally:
    srv.terminate()
n = sum(1 for _, c in R if c); print(f'\n{n}/{len(R)} passed')
sys.exit(0 if R and n == len(R) else 1)
