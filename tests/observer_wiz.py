import subprocess, time, json, traceback
from playwright.sync_api import sync_playwright
PORT=18931
srv = subprocess.Popen(['python3','-m','http.server',str(PORT),'-d','/home/coder/book-link/observer'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
R=[]
def ok(name, cond, extra=''):
    R.append((name, bool(cond), extra)); print(('PASS ' if cond else 'FAIL ')+name, extra)
try:
  with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width':390,'height':844})
    errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    ev = lambda c: pg.evaluate('(c)=>(0,eval)(c)', c)
    def shot(n): pg.screenshot(path=f'shot_{n}.png')
    def click(sel): pg.click(sel); pg.wait_for_timeout(250)
    def wiz(): return ev("state.wiz && ({i:state.wiz.i, step:state.wiz.step, list:state.wiz.list.map(x=>subjById(x).name)})")
    def rec(sid): return ev(f"(dayObj(state.date)||{{subj:{{}}}}).subj['{sid}']||null")
    pg.goto(f'http://localhost:{PORT}/index.html'); pg.wait_for_timeout(1500)

    # ===== 1. 从首页点「记今天的作业」进向导（真实点击而非 eval） =====
    click('[data-act=wizstart]')
    ok('1 首页点入向导 → 选科页', wiz() and wiz()['step']=='pick', str(wiz()))
    # 选科：点 4 科（语数英道法），用真实点击
    ids = ev("state.wiz.list.slice(0,4)")
    names = ev("state.wiz.list.slice(0,4).map(x=>subjById(x).name)")
    cur = ev("state.wiz.pick")
    for sid in ids:
        if sid not in cur: click(f'[data-act=wizpick][data-v="{sid}"]')
    for sid in ev("state.wiz.pick"):
        if sid not in ids: click(f'[data-act=wizpick][data-v="{sid}"]')
    ok('2 选科切换', ev("state.wiz.pick.length")==4, pg.inner_text('[data-act=wizpicked]'))
    click('[data-act=wizpicked]')
    w=wiz(); ok('3 确认选科 → 第一科 min', w['step']=='min' and w['i']==0 and w['list']==names, str(w))
    others = ev("state.wiz.all.filter(x=>!state.wiz.list.includes(x))")
    ok('3b 没选的科记为没作业', all((rec(s) or {}).get('none') for s in others))

    # ===== 2. 第一科没写，跳过 =====
    ok('4 空白时按钮文案', '先跳过' in pg.inner_text('[data-act=wiznext]'))
    ok('4b 第一科无「上一步」? 有（可回选科）', pg.locator('[data-act=wizback]').count()==1)
    click('[data-act=wiznext]')
    w=wiz(); ok('5 跳过 → 第二科', w['i']==1 and w['step']=='min', pg.inner_text('#toast'))
    ok('5b 跳过的科目仍是未填', not ev(f"filledRec(rec(state.date,'{ids[0]}'))"))

    # ===== 3. 上一步回到第一科，再跳过 =====
    click('[data-act=wizback]'); ok('6 上一步回第一科', wiz()['i']==0)
    click('[data-act=wiznext]'); ok('6b 再跳过回第二科', wiz()['i']==1)

    # ===== 4. 第二科：填 30 分钟 + 中途停了 → 卡点页 =====
    click('[data-act=wizmin][data-v="30"]')
    ok('7 点 30 分钟记录', rec(ids[1]) and rec(ids[1]).get('min')==30 and pg.locator('[data-act=wizmin][data-v="30"].on').count()==1)
    click('[data-act=wizintr][data-v="mid"]')
    ok('8 中途停了记录', rec(ids[1]).get('intr')=='mid' and wiz()['step']=='min')
    click('[data-act=wiznext]')
    ok('9 停过 → 卡点页', wiz()['step']=='stuck', str(wiz()))
    pg.fill('#w-stuck', '第三题不会'); pg.dispatch_event('#w-stuck','change'); pg.wait_for_timeout(200)
    click('[data-act=wizback]'); ok('10 卡点页上一步回 min', wiz()['step']=='min')
    click('[data-act=wiznext]'); click('[data-act=wiznext]')
    w=wiz(); ok('11 卡点页下一科 → 第三科', w['i']==2 and w['step']=='min', str(w))
    ok('11b 卡点文字保存', (rec(ids[1]).get('stuck') or '')=='第三题不会', str(rec(ids[1]).get('stuck')))

    # ===== 5. 第三科：手填分钟 + 记 2 道错题 → 错因页 =====
    pg.click('.wiz details.more summary'); pg.wait_for_timeout(200)
    pg.fill('#w-min','37'); click('[data-act=wizmanual]')
    ok('12 手填 37 分钟', rec(ids[2]).get('min')==37 and pg.locator('[data-act=wizmin][data-v="keep"].on').count()==1)
    tk = ev("ET[0].k"); tk2 = ev("ET[1].k")
    click(f'[data-act=wizerr][data-t="{tk}"][data-v="1"]'); click(f'[data-act=wizerr][data-t="{tk2}"][data-v="1"]')
    ok('13 记 2 道错题', ev(f"itemsOn(state.date,'{ids[2]}').length")==2)
    click(f'[data-act=wizerr][data-t="{tk2}"][data-v="-1"]'); click(f'[data-act=wizerr][data-t="{tk2}"][data-v="1"]')
    ok('13b 减一道再加回', ev(f"itemsOn(state.date,'{ids[2]}').length")==2)
    click('[data-act=wiznext]')
    ok('14 有错题 → 错在哪页', wiz()['step']=='detail', str(wiz()))
    shot('detail')
    chips = pg.locator('.chip[data-act=setsub]')
    if chips.count(): chips.first.click(); pg.wait_for_timeout(200)
    ok('15 选具体问题', ev(f"itemsOn(state.date,'{ids[2]}').some(it=>it.sub)"), f'chips={chips.count()}')
    click('[data-act=wizconf2][data-v="sure"]')
    ok('16 把握=有把握 两道都标', ev(f"itemsOn(state.date,'{ids[2]}').every(it=>it.conf==='sure')"))
    click('[data-act=wizback]'); ok('17 错在哪页上一步回 min', wiz()['step']=='min')
    click('[data-act=wiznext]'); click('[data-act=wiznext]')
    w=wiz(); ok('18 错在哪页下一科 → 第四科', w['i']==3, str(w))

    # ===== 6. 第四科：其余没作业按钮 / 今天没有 X 作业 =====
    ok('19 最后一科空白按钮文案', pg.inner_text('[data-act=wiznext]')=='还没写，先跳过', pg.inner_text('[data-act=wiznext]'))
    click(f'[data-act=wizmin][data-v="none"]')
    ok('20 今天没有这科作业', rec(ids[3]).get('none')==True, str(wiz()))
    w=wiz(); ok('20b 点没作业后自动到汇总页', w['i']==4, str(w))
    ok('21 汇总标题提示 1 科没填', '还有 1 科没填' in pg.inner_text('.wiz-q'), pg.inner_text('.wiz-q'))
    rows = pg.locator('.wiz-sum').all_inner_texts(); ok('21b 汇总行文案', '没填' in rows[0] and '30 分钟' in rows[1] and '记了 2 道题' in rows[2] and '没作业' in rows[3], ' | '.join(rows))
    shot('summary1')

    # ===== 7. 关闭向导，首页显示接着填，重开直达未填科 =====
    click('[data-act=wizclose]'); ok('22 关闭向导', ev("state.wiz")==None)
    txt = pg.inner_text('body'); ok('22b 首页显示 6/7 科+接着记还有 1 科', '6/7 科' in txt and '还有 1 科' in txt, [l for l in txt.split('\n') if '科' in l][:3])
    click('[data-act=wizstart]')
    w=wiz(); ok('23 重开直达第一科(未填)，没作业的道法不进列表', w['i']==0 and w['step']=='min' and w['list']==names[:3], str(w))
    click('[data-act=wizmin][data-v="20"]'); click('[data-act=wiznext]')
    w=wiz(); ok('24 补填语文 20 分钟 → 跳过已填的数学英语直达汇总', w['i']==3, str(w))
    ok('25 全填完汇总', '填完了' in pg.inner_text('.wiz-q'), pg.inner_text('.wiz-q'))
    shot('summary2')
    click('[data-act=wizclose]')
    txt = pg.inner_text('body'); ok('26 首页 7/7 科', '7/7 科' in txt)

    # ===== 8. 跟上周一样 + 其余 N 科没作业（换到明天的日期测，用今天数据当「上周」） =====
    ev("DB.days[addD(state.date,-7)] = JSON.parse(JSON.stringify(DB.days[state.date])); save()")
    ev("state.wiz=null; render()")
    ev("delete DB.days[state.date]; DB.items = DB.items.filter(it=>it.d!==state.date); save(); render()")
    click('[data-act=wizstart]')
    ok('27 有上周记录时显示「跟上周一样」', pg.locator('[data-act=wizsame]').count()==1)
    click('[data-act=wizsame]')
    w=wiz(); ok('28 跟上周一样 → 直接汇总(没有需手填的)', w['i']==len(w['list']), str(w)+' '+pg.inner_text('#toast'))
    ok('28b 上周数据复制', rec(ids[1]).get('min')==30 and rec(ids[2]).get('min')==37 and rec(ids[0]).get('min')==20)
    click('[data-act=wizclose]')
    # wizrest：清掉，填第一科后其余按钮出现
    ev("delete DB.days[state.date]; save(); render()")
    click('[data-act=wizstart]')
    for sid in ev("state.wiz.pick"):
        if sid not in ids: click(f'[data-act=wizpick][data-v="{sid}"]')
    for sid in ids:
        if sid not in ev("state.wiz.pick"): click(f'[data-act=wizpick][data-v="{sid}"]')
    click('[data-act=wizpicked]')
    ok('29 第一科时没有「其余没作业」', pg.locator('[data-act=wizrest]').count()==0)
    click('[data-act=wizmin][data-v="15"]'); click('[data-act=wiznext]')
    ok('30 第二科出现「其余 3 科没作业」', pg.locator('[data-act=wizrest]').count()==1, pg.locator('[data-act=wizrest]').all_inner_texts())
    click('[data-act=wizrest]')
    ok('31 其余记为没作业 → 汇总填完', '填完了' in pg.inner_text('.wiz-q') and all(rec(s).get('none') for s in ids[1:]))
    # 汇总页点一科回去改
    click('.wiz-sum[data-v="2"]'); ok('32 汇总页点第三科回去', wiz()['i']==2 and wiz()['step']=='min')
    click('[data-act=wizmin][data-v="10"]'); ok('32b 没作业改为 10 分钟', rec(ids[2]).get('min')==10 and not rec(ids[2]).get('none'))
    click('[data-act=wiznext]')
    ok('33 改完一下就回到汇总（第四科已记没作业不再经过）', ev("state.wiz.i")==4, str(wiz()))
    # 选科页「今天都没作业」
    click('[data-act=wizclose]'); ev("delete DB.days[state.date]; save(); render()")
    click('[data-act=wizstart]')
    for sid in ev("state.wiz.pick"): click(f'[data-act=wizpick][data-v="{sid}"]')
    ok('34 一科不选按钮文案', '今天都没作业' in pg.inner_text('[data-act=wizpicked]'))
    click('[data-act=wizpicked]')
    ok('35 全没作业 → 汇总「今天都没作业」', '今天都没作业' in pg.inner_text('.wiz-q'), pg.inner_text('.wiz-q'))
    ok('36 无页面 JS 错误', not errs, errs[:3])
    b.close()
except Exception:
    traceback.print_exc()
finally:
    srv.terminate()
print('\n%d/%d passed' % (sum(1 for r in R if r[1]), len(R)))
