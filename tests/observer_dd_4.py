# 第 9 章方案第 4 条：单词换问法——课文原句挖空 / 听音拼写 / 看中文拼
# 磨耳朵课文在私有仓库加密，这里用自编的假句子模拟 EAR.idx（测试文件在公开仓库，不放课本原文）
import subprocess, time, json, socket, sys, traceback
from playwright.sync_api import sync_playwright

def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p
PORT = free_port()
srv = subprocess.Popen(['python3', '-m', 'http.server', str(PORT), '-d', '/home/coder/book-link'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
R = []
def ok(name, cond, extra=''):
    R.append((name, bool(cond))); print(('PASS ' if cond else 'FAIL ') + name, extra if not cond else '')

# 浏览器朗读打桩：有英文语音；speak 记下念了什么，__mute 时不触发 onstart（模拟没出声）
STUB = """
window.__said = []; window.__mute = false; window.__noVoices = false;
try {
  speechSynthesis.getVoices = () => window.__noVoices ? [] : [{lang: 'en-US', name: 'stub'}];
  speechSynthesis.speak = u => { window.__said.push(u.text); if (!window.__mute) setTimeout(() => { u.onstart && u.onstart(); }, 30); };
  speechSynthesis.cancel = () => {};
} catch(e) {}
"""
# 自编句子：Unit 1 的 guitar / patient / improve / describe；标题里放 honest、单词跟读里放 trust（两处都不该被收）
EARIDX = {'days': [], 'tracks': [
    {'id': 'u1-reading', 'unit': 1, 'kind': 'reading', 'paras': ['An honest boy.', 'My brother plays the guitar every Sunday afternoon. He wants to improve his English this term.']},
    {'id': 'u1-culture', 'unit': 1, 'kind': 'culture', 'paras': ['Title.', 'Our teacher is patient with every student in the class. Can you describe your best friend in three sentences?']},
    {'id': 'u1-words', 'unit': 1, 'kind': 'words', 'paras': ['Words.', 'You can trust your good friends at school.']},
    {'id': 'u5-reading', 'unit': 5, 'kind': 'reading', 'paras': ['T.', 'We sat in the dark and waited for the show.']},
]}

try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Shanghai')
        ctx.clock.install(time='2026-10-14T20:00:00+08:00')
        ctx.route('https://api.github.com/**', lambda r: r.fulfill(status=404, body='{}'))
        ctx.add_init_script(STUB)
        pg = ctx.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        ev = lambda c: pg.evaluate('(c)=>(0,eval)(c)', c)
        pg.goto(f'http://localhost:{PORT}/observer/index.html'); pg.wait_for_timeout(1500)
        for _ in range(40):
            if ev("!!(LIB.words && LIB.words.words && LIB.words.words.length)"): break
            pg.wait_for_timeout(250)
        ok('0 词库已加载', ev("!!LIB.words"))
        T = ev("today()"); ok('0b 固定时钟', T == '2026-10-14', T)
        ok('0c 现在学到 Unit 1 以后、Unit 5 之前', 1 <= ev("enUnit(today())") < 5, ev("enUnit(today())"))
        ok('0d 打桩语音可用', ev("wVoiceOK()"))
        ev(f"DB.words = {{}}; save(); EAR.idx = {json.dumps(EARIDX)}; EAR.st = 'ok'; WF.ci = null; 0")
        main = lambda: pg.inner_text('#main')
        st = lambda w: ev(f"DB.words[{json.dumps(w.lower())}] || null")
        W = lambda w: f"uniqWords().find(x => x.w === {json.dumps(w)})"
        def seed(words, hist=None, extra=None):
            # 只留这几个词：都到期（今天），历史默认是 10-01 记对一次（没有 k，相当于看中文）
            h = hist if hist is not None else [{'d': '2026-10-01', 'ok': True}]
            m = {w.lower(): dict({'box': 1, 'first': '2026-10-01', 'due': T, 'hist': h, 'u': 1}, **(extra or {})) for w in words}
            ev(f"DB.words = {json.dumps(m)}; save(); state.learn = {{view:'card'}}; state.tab = 'learn'; 0")
        def openc():
            ev("state.tab='learn'; state.learn = Object.assign(state.learn || {}, {view:'card', flip:false, wf:null, wk:null, typed:''}); render(); 0"); pg.wait_for_timeout(150)
        def clickcard():   # 经点击进背单词（听写卡要在点击里念）
            ev("state.tab='learn'; state.learn = {view:'words', book:'hj7a', unit:null}; render(); 0"); pg.wait_for_timeout(100)
            pg.click('[data-act=lv][data-v=card]'); pg.wait_for_timeout(150)
        cur = lambda: ev("curWord() && curWord().w")
        form = lambda w: ev(f"wForm({W(w)}, wState({W(w)}))")

        # ===== 1. 句子索引 =====
        I = ev("(() => { const I = clozeIdx(); return {keys: Object.keys(I.m), n: I.sents.length}; })()")
        ok('1 收到 guitar / improve / patient / describe', all(k in I['keys'] for k in ['guitar', 'improve', 'patient', 'describe']), json.dumps(I))
        ok('1b 标题段（honest）不收', 'honest' not in I['keys'])
        ok('1c 单词跟读（trust）不收', 'trust' not in I['keys'])
        ok('1d 只取原形精确匹配：dark 在 Unit 5 句里有索引但今天不给', 'dark' in I['keys'] and ev(f"clozeOf({W('dark')}, null)") is None)
        ok('1e 课文不写进 words.json 数据', ev("!JSON.stringify(LIB.words).includes('every Sunday afternoon')"))

        # ===== 2. 新词第一轮看中文 =====
        ok('2 新词 → cn', form('guitar')['f'] == 'cn')

        # ===== 3. 复习词（上次看中文记对）→ 课文填空 =====
        seed(['guitar'])
        f = form('guitar'); ok('3 上次看中文对了 → 下一种是填空', f['f'] == 'cloze' and f.get('cs') == 'u1-reading:1:0', json.dumps(f))
        openc()
        ok('3b 卡上有填空句', pg.locator('.wform-cloze').count() == 1 and 'every Sunday afternoon' in main())
        ok('3c 只给首字母，不露整个词', 'guitar' not in pg.inner_text('.wform-cloze') and 'g_____' in pg.inner_text('.wform-cloze').replace(' ', ''), pg.inner_text('.wform-cloze'))
        ok('3d 标「课文填空」，有「对答案 / 想不起来」', '课文填空' in main() and pg.locator('[data-act=wflip]').count() == 1 and pg.locator('[data-act=wnone]').count() == 1)
        ok('3e 390 宽无横向滚动', ev("document.documentElement.scrollWidth") <= 391)
        pg.click('[data-act=wflip]'); pg.wait_for_timeout(150)
        ok('3f 没打字不翻面', not ev("state.learn.flip"))
        exp = ev(f"fsStep(fsReplay(wState({W('guitar')}).hist, rateOf), today(), 3).due")
        pg.fill('#w-spell', 'guitar'); pg.click('[data-act=wflip]'); pg.wait_for_timeout(150)
        ok('3g 拼对：翻面后句子补全', ev("state.learn.flip") and 'guitar' in pg.inner_text('.wform-cloze'))
        pg.click('[data-act=wmark][data-v="1"]'); pg.wait_for_timeout(150)
        s = st('guitar'); h = s['hist'][-1]
        ok('3h 记 k=cloze 和句子编号，不存句子原文', h.get('k') == 'cloze' and h.get('cs') == 'u1-reading:1:0' and 'Sunday' not in json.dumps(s), json.dumps(h))
        ok('3i 填空对了评分 3', ev(f"rateOf({json.dumps(h)})") == 3 and s['due'] == exp, f"{s['due']} vs {exp}")
        ok('3j 下一次换成听写', form('guitar')['f'] == 'ear')

        # ===== 4. 听音拼写 =====
        seed(['guitar'], [{'d': '2026-10-01', 'ok': True}, {'d': '2026-10-05', 'ok': True, 'k': 'cloze', 'cs': 'u1-reading:1:0'}])
        ev("window.__said = []; 0")
        clickcard()
        ok('4 听写卡：进卡就念一遍', ev("window.__said").count('guitar') == 1, json.dumps(ev("window.__said")))
        ok('4b 标「听音拼写」，翻面前不显示中文', '听音拼写' in main() and '吉他' not in main() and pg.locator('.wform-ear').count() == 1)
        ok('4c 390 宽无横向滚动', ev("document.documentElement.scrollWidth") <= 391)
        pg.click('[data-act=wsay]'); pg.wait_for_timeout(100)
        ok('4d 再听一遍', ev("window.__said").count('guitar') == 2)
        pg.wait_for_timeout(1700)
        ok('4e 出声了就不退回', ev("state.learn.wf.f") == 'ear' and not ev("WF.noVoice"))
        pg.fill('#w-spell', 'guitar'); pg.click('[data-act=wflip]'); pg.wait_for_timeout(150)
        ok('4f 翻面后显示中文', '吉他' in main())
        pg.click('[data-act=wmark][data-v="1"]'); pg.wait_for_timeout(150)
        h = st('guitar')['hist'][-1]
        ok('4g 听写拼对：k=ear，评分 4', h.get('k') == 'ear' and h['ok'] and ev(f"rateOf({json.dumps(h)})") == 4, json.dumps(h))
        ok('4h 再下一次回到看中文', form('guitar')['f'] == 'cn')

        # ===== 5. 答错 → 当晚重考用线索更多的那种（上次填空在 14 天前，句子可以再用）=====
        seed(['guitar'], [{'d': '2026-09-20', 'ok': True}, {'d': '2026-09-28', 'ok': True, 'k': 'cloze', 'cs': 'u1-reading:1:0'}])
        clickcard(); pg.fill('#w-spell', 'gitar'); pg.click('[data-act=wflip]'); pg.wait_for_timeout(150)
        ok('5 听写拼错：拼错了 / 看清了', pg.locator('[data-act=wmark][data-v="0"]').count() == 1 and pg.locator('[data-act=wslip]').count() == 1)
        pg.click('[data-act=wmark][data-v="0"]'); pg.wait_for_timeout(150)
        s = st('guitar'); h = s['hist'][-1]
        ok('5b 记 k=ear 错', h.get('k') == 'ear' and h['ok'] is False and s['due'] == T)
        ok('5c 当晚重考换成填空（同一晚同一句可以再用）', form('guitar')['f'] == 'cloze', json.dumps(form('guitar')))
        seed(['guitar'], [{'d': '2026-10-01', 'ok': True}, {'d': T, 'ok': False}])
        ok('5d 看中文错了 → 重考听写', form('guitar')['f'] == 'ear')
        seed(['guitar'], [{'d': '2026-10-01', 'ok': True}, {'d': T, 'ok': False, 'k': 'cloze', 'cs': 'u1-reading:1:0'}])
        ok('5e 填空错了 → 还是填空', form('guitar')['f'] == 'cloze')
        seed(['guitar'], [{'d': '2026-10-01', 'ok': True}, {'d': T, 'ok': False, 'slip': 1, 'k': 'ear'}])
        ok('5f 听写手滑 → 重考填空', form('guitar')['f'] == 'cloze')

        # ===== 6. 想不起来 =====
        seed(['guitar'])
        openc(); pg.click('[data-act=wnone]'); pg.wait_for_timeout(150)
        s = st('guitar'); h = s['hist'][-1]
        ok('6 填空想不起来：记错 + k，翻面只剩下一个', h['ok'] is False and h.get('k') == 'cloze' and 'pj' not in h and pg.locator('[data-act=wnext]').count() == 1, json.dumps(h))
        ok('6b 翻面露出整句', 'guitar' in pg.inner_text('.wform-cloze'))
        ok('6c 必拼轮想不起来按拼错记（ty）', h.get('ty') == 1, json.dumps(h))
        pg.click('[data-act=wnext]'); pg.wait_for_timeout(150)

        # ===== 7. 同音词 =====
        hw = ev("(() => { const a = uniqWords().find(x => x.w === 'week'), b = uniqWords().find(x => x.w === 'weak'); return a && b && a.p && a.p === b.p ? [a.w, b.w] : null; })()")
        ok('7 词库里 week / weak 音标相同', hw is not None)
        if hw:
            seed([hw[0]], [{'d': '2026-10-01', 'ok': True}])
            ok('7a 没有原句的词 → 听写', form(hw[0])['f'] == 'ear')
            clickcard(); n0 = len(st(hw[0])['hist'])
            pg.fill('#w-spell', hw[1]); pg.click('[data-act=wflip]'); pg.wait_for_timeout(150)
            ok('7b 拼成同音词：提示换个写法，不翻面、不判错', not ev("state.learn.flip") and len(st(hw[0])['hist']) == n0 and '另一个写法' in pg.inner_text('body'))
            pg.fill('#w-spell', hw[0]); pg.click('[data-act=wflip]'); pg.wait_for_timeout(150)
            ok('7c 再拼对能翻面', ev("state.learn.flip") and pg.locator('[data-act=wmark][data-v="1"]').count() == 1)
            pg.click('[data-act=wmark][data-v="1"]'); pg.wait_for_timeout(150)

        # ===== 8. 没声音 → 退回看中文 =====
        seed(['guitar'], [{'d': '2026-10-01', 'ok': True}, {'d': '2026-10-05', 'ok': True, 'k': 'cloze', 'cs': 'u1-reading:1:0'}])
        ev("window.__mute = true; WF.noVoice = false; 0")
        clickcard()
        ok('8 先出听写卡', pg.locator('.wform-ear').count() == 1)
        pg.fill('#w-spell', 'gui'); pg.wait_for_timeout(1700)
        ok('8b 1.5 秒没出声 → 改成看中文，打的字还在', pg.locator('.wform-ear').count() == 0 and '吉他' in main() and pg.input_value('#w-spell') == 'gui')
        ok('8b2 重绘后光标还在输入框里', ev("document.activeElement && document.activeElement.id") == 'w-spell' and ev("$('#w-spell').selectionStart") == 3)
        ok('8b3 提示和卡上说法一致（表态卡说「想」不说「拼」）', '看中文想英文' in pg.inner_text('#toast') and '心里想' in main(), pg.inner_text('#toast'))
        ok('8c 这次会话不再出听写', ev("WF.noVoice") and form('guitar')['f'] != 'ear')
        ok('8c2 退回后是第 3 条的表态卡', pg.locator('[data-act=wflip][data-pj="1"]').count() == 1)
        pg.fill('#w-spell', 'guitar'); pg.click('[data-act=wflip][data-pj="1"]'); pg.wait_for_timeout(150)
        h = st('guitar')['hist'][-1]
        ok('8d 退回的这张不记 k', 'k' not in h and h['ok'], json.dumps(h))
        pg.click('[data-act=wnext]'); pg.wait_for_timeout(150)
        ev("window.__mute = false; WF.noVoice = false; window.__noVoices = true; 0")
        seed(['guitar'], [{'d': '2026-10-01', 'ok': True}, {'d': '2026-10-05', 'ok': True, 'k': 'cloze', 'cs': 'u1-reading:1:0'}])
        ok('8e 没有英文语音 → 不出听写（填空之后看中文）', form('guitar')['f'] == 'cn')
        ev("window.__noVoices = false; 0")

        # ===== 9. 不参加的情况 =====
        seed(['guitar'])
        ev("EAR.idx = null; 0")
        ok('9 没有磨耳朵数据 → 不出填空（听写）', form('guitar')['f'] == 'ear')
        ev(f"EAR.idx = {json.dumps(EARIDX)}; 0")
        uw = ev("(uniqWords().find(x => x.u) || {}).w")
        if uw: seed([uw]); ok('9b 只要求认识的词 → cn', form(uw)['f'] == 'cn', uw)
        seed(['turn to somebody for help']); ok('9c 长短语 → cn', form('turn to somebody for help')['f'] == 'cn')
        seed(['guitar'], [{'d': '2026-10-01', 'ok': True}, {'d': '2026-10-08', 'ok': True, 'k': 'cloze', 'cs': 'u1-reading:1:0'}, {'d': '2026-10-10', 'ok': True}])
        f = form('guitar')
        ok('9d 同一句 14 天内不再用 → 跳过填空', f['f'] != 'cloze', json.dumps(f))
        seed(['guitar'], [{'d': '2026-09-20', 'ok': True, 'k': 'cloze', 'cs': 'u1-reading:1:0'}, {'d': '2026-10-10', 'ok': True}])
        ok('9e 超过 14 天可以再用', form('guitar')['f'] == 'cloze')
        seed(['patient'])
        ev("DB.words = Object.assign(DB.words, {}); 0")
        ok('9f patient 句里其他课本词没背过的不超过 1 个 → 有填空', form('patient')['f'] == 'cloze', json.dumps(form('patient')))
        seed(['guitar'])
        ev("DB.days[today()] = {subj: {sx: {min: 100}}, u: 1}; 0")
        ok('9g 作业重的晚上 → cn', ev("heavyNight()") and form('guitar')['f'] == 'cn')
        ev("delete DB.days[today()]; 0")
        ok('9h 去掉作业后恢复', form('guitar')['f'] == 'cloze')

        # ===== 10. 掌握前最后一次要看中文拼对 =====
        fsBig = {'s': 400, 'df': 3, 'r': 6, 'l': 0, 'st': 2, 'lr': '2026-07-01', 'due': T}
        seed(['guitar'], [{'d': '2026-07-01', 'ok': True}, {'d': '2026-09-01', 'ok': True, 'k': 'cloze', 'cs': 'x'}], {'box': 5, 'fs': fsBig})
        ev(f"state.learn.wf = {{w:'guitar', d: today(), f:'ear'}}; markWord({W('guitar')}, true, {{sp:true, ty:1, k:'ear'}}); 0")
        s = st('guitar')
        ok('10 听写对了且间隔够掌握：不算掌握，置 fin', s.get('fin') == 1 and not s.get('done') and s['due'], json.dumps({k: s.get(k) for k in ['fin', 'done', 'due']}))
        ok('10b fin 后一律看中文', form('guitar')['f'] == 'cn')
        ev(f"markWord({W('guitar')}, true, {{sp:true, ty:1}}); 0")
        s = st('guitar')
        ok('10c 看中文拼对 → 掌握，清 fin', s.get('done') is True and not s.get('fin'), json.dumps({k: s.get(k) for k in ['fin', 'done', 'due']}))
        seed(['guitar'], [{'d': '2026-09-01', 'ok': True}], {'fin': 1})
        ev(f"markWord({W('guitar')}, false, {{ty:1}}); 0")
        ok('10d 看中文错了清 fin', not st('guitar').get('fin'))

        # ===== 11. 老记录回放不变、同步合并带上新字段 =====
        ok('11 老记录评分不变', ev("[{d:'x',ok:true},{d:'x',ok:true,sp:true},{d:'x',ok:false}].map(rateOf).join()") == '3,4,1')
        mg = ev("""(() => { const a = {box:1, u:5, hist:[{d:'2026-10-13', ok:true, k:'cloze', cs:'u1-reading:1:0'}]}, b = {box:2, u:9, hist:[{d:'2026-10-14', ok:true, k:'ear'}]};
          return mergeRec(a, b, false).v.hist; })()""")
        ok('11b 合并后两台设备的 k / cs 都在', len(mg) == 2 and mg[0].get('cs') and mg[1].get('k') == 'ear', json.dumps(mg))

        # ===== 12. 第 3 条的拼写流程没被打断：必拼的看中文卡仍是「翻面看答案」 =====
        ev("EAR.idx = null; window.__noVoices = true; 0")
        seed(['guitar'], [{'d': '2026-10-01', 'ok': True}, {'d': '2026-10-05', 'ok': True}], {'box': 2})
        openc()
        ok('12 无填空无听写时必拼卡仍是翻面看答案', '翻面看答案' in main() and pg.locator('[data-act=wnone]').count() == 0)
        ev("window.__noVoices = false; 0")

        # ===== 13. 审查修复：挖空句不露答案、缩写不断句、填空句居中、说明对得上按钮、家长统计 =====
        IDX2 = {'days': [], 'tracks': [{'id': 'fx', 'unit': 1, 'kind': 'reading', 'paras': ['T.',
            'Our club meets on Friday and their club meets on Monday. The club is open to every student here. '
            'A part of the parts box is broken today. We need one part for the model plane. '
            'Classes end at 4:25 p.m. every day at our school. Lunch starts at 12:00 p.m. Then we all play games outside.']}]}
        ev(f"EAR.idx = {json.dumps(IDX2)}; EAR.st = 'ok'; WF.ci = null; 0")
        I2 = ev("(() => { const I = clozeIdx(); const g = k => (I.m[k] || []).map(x => x.s); return {club: g('club'), part: g('part'), end: g('end'), sents: I.sents.map(x => x.s)}; })()")
        ok('13 同一句出现两次的词不挖（只收 The club is open…）', I2['club'] == ['The club is open to every student here.'], json.dumps(I2['club']))
        ok('13b 句中有同根变形（parts）的不挖', I2['part'] == ['We need one part for the model plane.'], json.dumps(I2['part']))
        ok('13c p.m. 不断句：整句收进来', I2['end'] == ['Classes end at 4:25 p.m. every day at our school.'] and 'Lunch starts at 12:00 p.m.' in I2['sents'], json.dumps(I2['sents']))
        ok('13d 没有以单个字母加句点结尾的残句', not any(__import__('re').search(r'(^|\s)[A-Za-z]\.$', x) for x in I2['sents']))
        ev(f"EAR.idx = {json.dumps(EARIDX)}; WF.ci = null; window.__noVoices = false; 0")
        seed(['guitar']); openc()
        ok('13e 填空句居中', pg.locator('.wform-cloze').count() == 1 and ev("getComputedStyle($('.wform-cloze')).textAlign") == 'center')
        ok('13f 「怎么背」说明写了填空和听写要先拼再点对答案', '再点「对答案」' in pg.inner_html('#main'))
        ev("DB.words = {zz: {box: 0, hist: [{d: today(), ok: false, pj: 1}, {d: today(), ok: false, k: 'cloze', ty: 1}, {d: today(), ok: true, sp: true, ty: 1}]}}; 0")
        ps = ev("wordPjStat(addD(today(), -13), today())")
        ok('13g 家长统计：说想出来了之后的必拼轮想不起来算一次没拼对', ps['k'] == 1 and ps['m'] == 0, json.dumps(ps))

        ok('99 无页面报错', not errs, '; '.join(errs[:3]))
        b.close()
except Exception:
    traceback.print_exc(); R.append(('exception', False))
finally:
    srv.terminate()
n = sum(1 for _, c in R if c); print(f'{n}/{len(R)} passed'); sys.exit(0 if n == len(R) and R else 1)
