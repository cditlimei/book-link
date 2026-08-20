/* ============================================================
   计划引擎 + 交互
   ============================================================ */
const KEY = 'mathplan_v1';
const BOX_GAP = [1, 2, 4, 7, 15, 30];

/* 小学基础补漏优先队列的候选 */
const P_TOPICS = TOPICS.filter(t => t.stage === 'P').map(t => t.k);
const M_TOPICS = TOPICS.filter(t => t.stage === 'M').map(t => t.k);

/* 开学后 20 周跟课表，按北师大版（2024）七上章序 + 深圳市 2026-2027 校历排的：
   9/1 开学，国庆 10/1–10/7，期末考不早于 2027-01-14，1/23 放寒假。
   mile 是里程碑标记，学校进度不一样时在「计划」页逐周改。 */
const TRACK = [
  { w: 1,  ch: '第一章 丰富的图形世界（立体图形、展开与折叠、三视图）', ks: ['numline'], mile: '开学第一周，本章计算少，重点是把作业习惯立起来' },
  { w: 2,  ch: '2.1 有理数 · 2.2 数轴 · 2.3 绝对值', ks: ['numline', 'abs-calc'] },
  { w: 3,  ch: '2.4 有理数的加法 · 2.5 有理数的减法', ks: ['rat-addsub'], mile: '整个七上最关键的一周，减法改写成加相反数必须练成条件反射' },
  { w: 4,  ch: '有理数加减混合运算', ks: ['rat-addsub', 'paren-nest'] },
  { w: 5,  ch: '2.6 有理数的乘法（国庆假期，进度会慢）', ks: ['rat-muldiv', 'sign-mix'], mile: '国庆 10/1–10/7，假期最容易断档，每天 15 分钟也要碰' },
  { w: 6,  ch: '2.7 有理数的除法', ks: ['rat-muldiv', 'sign-mix'] },
  { w: 7,  ch: '2.8 有理数的乘方 · 科学记数法', ks: ['power', 'power-frac', 'sci'], mile: '(−2)² 和 −2² 的区别，这里错了后面全是连环错' },
  { w: 8,  ch: '2.9 有理数的混合运算 · 第二章回顾', ks: ['rat-mixed', 'neg-frac', 'sign-mix'] },
  { w: 9,  ch: '期中复习（有理数是绝对重点）', ks: ['rat-mixed', 'power', 'sign-mix', 'paren-nest'], mile: '期中考试一般在这一两周，考的基本就是有理数运算' },
  { w: 10, ch: '期中考试周 · 试卷分析', ks: ['rat-mixed', 'neg-frac'], mile: '拿到卷子按错因归类，别只看分数' },
  { w: 11, ch: '3.1 代数式 · 单项式与多项式（系数、次数）', ks: ['monomial'] },
  { w: 12, ch: '3.2 合并同类项', ks: ['like-terms'] },
  { w: 13, ch: '3.3 整式的加减 · 去括号', ks: ['remove-paren', 'paren-nest'] },
  { w: 14, ch: '整式化简求值 · 第三章回顾', ks: ['eval-expr', 'remove-paren'] },
  { w: 15, ch: '第四章 基本平面图形（线段、角、平行垂直）', ks: ['geom'] },
  { w: 16, ch: '5.1 认识方程 · 5.2 解一元一次方程（移项、合并）', ks: ['linear-eq'] },
  { w: 17, ch: '5.3 去括号、去分母解方程', ks: ['linear-eq', 'remove-paren'] },
  { w: 18, ch: '5.4 一元一次方程的应用', ks: ['eq-word'] },
  { w: 19, ch: '第六章 数据的收集与整理 · 期末总复习开始', ks: ['stat', 'rat-mixed', 'linear-eq'], mile: '期末复习两周，回头把错题本清一遍比刷新题有用' },
  { w: 20, ch: '期末复习冲刺（期末考不早于 1/14，1/23 放寒假）', ks: ['rat-mixed', 'linear-eq', 'remove-paren', 'sign-mix'], mile: '期末考试周' }
];

/* ---------- 日期工具（全部本地时区） ---------- */
const pad = n => (n < 10 ? '0' : '') + n;
function ds(d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
function today() { return ds(new Date()); }
function parseD(s) { const p = s.split('-'); return new Date(+p[0], +p[1] - 1, +p[2]); }
function addDays(s, n) { const d = parseD(s); d.setDate(d.getDate() + n); return ds(d); }
function dayDiff(a, b) { return Math.round((parseD(b) - parseD(a)) / 86400000); }
function cnDate(s) { const d = parseD(s); return (d.getMonth() + 1) + '月' + d.getDate() + '日 周' + '日一二三四五六'[d.getDay()]; }

/* ---------- 存档 ---------- */
let DB = null;
function fresh() {
  return {
    ver: 1,
    profile: { name: '', kickoff: '2026-08-29', schoolStart: '2026-09-01', dailyMin: 25 },
    diag: { done: false, date: '', scores: {} },
    queue: [],
    mastery: {},
    wrong: [],
    logs: {},
    trackOverride: {},
    facts: [],
    boss: {}
  };
}
function load() {
  try { const s = localStorage.getItem(KEY); DB = s ? JSON.parse(s) : fresh(); }
  catch (e) { DB = fresh(); }
  if (!DB.ver) DB = fresh();
  ['diag', 'mastery', 'logs', 'trackOverride'].forEach(k => { if (!DB[k]) DB[k] = {}; });
  if (!DB.wrong) DB.wrong = [];
  if (!DB.queue) DB.queue = [];
  if (!DB.facts) DB.facts = [];
  if (!DB.boss) DB.boss = {};
  if (!DB.profile) DB.profile = fresh().profile;
  save();
}
/* 存不进去时降级到内存，并在页面顶部挂一条常驻警告，避免白做一晚上 */
let STORE_OK = true;
function save() {
  try {
    localStorage.setItem(KEY, JSON.stringify(DB));
    if (!STORE_OK) { STORE_OK = true; const w = document.getElementById('warnbar'); if (w) w.remove(); }
  } catch (e) {
    STORE_OK = false;
    if (!document.getElementById('warnbar')) {
      const b = document.createElement('div');
      b.id = 'warnbar'; b.className = 'warnbar';
      b.innerHTML = '这个浏览器存不住进度（隐私模式或本地文件限制）。今天做的题只在当前页面里，<b>关掉就没了</b>——练完先去「设置 → 导出进度文件」。';
      document.body.insertBefore(b, document.body.firstChild);
    }
  }
}

/* ---------- 掌握度 ---------- */
function mst(k) { const m = DB.mastery[k]; if (!m || !m.total) return null; return m.right / m.total; }
function mstN(k) { const m = DB.mastery[k]; return m ? m.total : 0; }
function bump(k, ok) {
  const m = DB.mastery[k] || (DB.mastery[k] = { right: 0, total: 0, r20: [] });
  if (!m.r20) m.r20 = [];
  m.total++; if (ok) m.right++;
  m.r20.push(ok ? 1 : 0); if (m.r20.length > 20) m.r20.shift();
}
/* 按近况选难度档：>90% 升到 3 档，<60% 降到 1 档，中间维持 2 档。
   目标把正确率稳在 85% 附近（Wilson et al. 2019 的最优学习区）。*/
function pickLv(k) {
  const m = DB.mastery[k];
  if (!m || !m.r20 || m.r20.length < 6) return 2;
  const win = m.r20.slice(-10);
  const r = win.reduce((a, b) => a + b, 0) / win.length;
  const all = m.total ? m.right / m.total : 0;
  /* 降档只看近况，反应要快；升档还要看累计，因为近 10 题连对可能只是
     碰上简单题，累计才 55% 就跳最难档会直接把他砸崩。升保守、降灵敏。 */
  if (r < 0.6) return 1;
  if (r >= 0.9 && all >= 0.75 && m.total >= 15) return 3;
  return 2;
}
/* 近 20 题正确率，用于判断是否出队 */
function recent(k) { const m = DB.mastery[k]; if (!m || !m.r20 || m.r20.length < 8) return null; return m.r20.reduce((a, b) => a + b, 0) / m.r20.length; }

/* ---------- 补漏队列 ---------- */
function buildQueue() {
  const rows = P_TOPICS.map(k => {
    const s = DB.diag.scores[k];
    const rate = s && s.total ? s.right / s.total : 0.5;
    return { k, rate, pri: TMAP[k].pri };
  });
  rows.sort((a, b) => (a.rate - b.rate) || (a.pri - b.pri));
  DB.queue = rows.filter(r => r.rate < 0.85).map(r => r.k);
  if (!DB.queue.length) DB.queue = rows.slice(0, 3).map(r => r.k);
}
function refreshQueue() {
  /* 近 20 题正确率 ≥ 0.85 且累计 ≥ 20 题 → 出队（毕业） */
  DB.queue = DB.queue.filter(k => !(mstN(k) >= 20 && (recent(k) || 0) >= 0.85));
  if (!DB.queue.length) {
    const left = P_TOPICS.map(k => ({ k, r: mst(k) === null ? 0.5 : mst(k), p: TMAP[k].pri }))
      .sort((a, b) => (a.r - b.r) || (a.p - b.p));
    DB.queue = left.slice(0, 2).map(x => x.k);
  }
}

/* ---------- 当前处于第几周 ---------- */
function weekInfo() {
  const t = today(), ks = DB.profile.kickoff, ss = DB.profile.schoolStart;
  if (dayDiff(t, ks) > 0) return { phase: 'pre', label: '还没到启动日（' + cnDate(ks) + '）', w: 0 };
  if (dayDiff(t, ss) > 0) return { phase: 'kick', label: '开学前破冰第 ' + (dayDiff(ks, t) + 1) + ' 天', w: 0 };
  const w = Math.floor(dayDiff(ss, t) / 7) + 1;
  const lab = w <= 20 ? '开学第 ' + w + ' 周' : '开学第 ' + w + ' 周（一学期跟课表已走完，现在按期末复习内容循环）';
  return { phase: 'term', label: lab, w: Math.min(w, 20) };
}
function trackOf(w) {
  if (DB.trackOverride[w]) { const o = DB.trackOverride[w]; return { w, ch: o.ch, ks: o.ks }; }
  return TRACK[Math.min(Math.max(w, 1), 20) - 1];
}

/* ---------- 今日任务 ---------- */
function dueWrongs() { const t = today(); return DB.wrong.filter(w => w.due <= t); }

function buildToday() {
  const t = today();
  if (DB.logs[t] && DB.logs[t].qs) return DB.logs[t];
  const wi = weekInfo();
  const min = DB.profile.dailyMin;
  const scale = min <= 15 ? 0.6 : min >= 40 ? 1.4 : 1;
  const nWarm = Math.round(10 * scale), nFocus = Math.round(6 * scale), nTrack = Math.round(6 * scale);

  refreshQueue();
  const focusK = DB.queue[0] || P_TOPICS[0];
  const focus2 = DB.queue[1];

  /* 破冰期：还没开学，跟课部分改成有理数预习 */
  let trackKs, trackCh;
  if (wi.phase === 'term') { const tr = trackOf(wi.w); trackKs = tr.ks; trackCh = tr.ch; }
  else { trackKs = ['numline', 'rat-addsub']; trackCh = '开学预习：数轴、相反数、绝对值、有理数加减'; }

  const wst = wi.phase === 'term' ? (wi.w >= 7 ? 3 : 2) : 2;
  const nFrac = Math.max(2, Math.round(nWarm * 0.4));
  const warm = [];
  for (let i = 0; i < nWarm; i++) warm.push(warmupQ(wst, i < nFrac ? 'frac' : 'neg'));

  const fq = [];
  const half = focus2 ? Math.ceil(nFocus / 2) : nFocus;
  genMany(focusK, half, pickLv(focusK)).forEach(q => fq.push(q));
  if (focus2) genMany(focus2, nFocus - half, pickLv(focus2)).forEach(q => fq.push(q));

  const tq = [];
  /* 跟课段开头先放一对梯子题：小学锚点 → 只多一个负号的初一题 */
  const bk = trackKs.filter(k => typeof BRIDGE !== 'undefined' && BRIDGE[k]);
  const br = bk.length ? genBridge(pick(bk)) : null;
  if (br) { tq.push(br[0]); tq.push(br[1]); }
  for (let i = 0; i < nTrack; i++) { const kk = trackKs[i % trackKs.length]; tq.push(genQ(kk, pickLv(kk))); }

  const rv = dueWrongs().slice(0, Math.round(6 * scale));

  /* 开工前拍一张掌握度快照，晚上用来算「今天变强了什么」 */
  const snap = {};
  Object.keys(DB.mastery).forEach(k => { const m = DB.mastery[k]; snap[k] = { right: m.right, total: m.total }; });

  const log = {
    date: t, week: wi.w, phase: wi.phase, trackCh, focusK, focus2,
    lv: { focus: pickLv(focusK), track: pickLv(trackKs[0]) },
    qs: { warm, focus: fq, track: tq, review: rv },
    res: { warm: [], focus: [], track: [], review: [] },
    wrongToday: [], snap: snap, factsToday: [], mini: false,
    wrongCountAtStart: DB.wrong.length, startedAt: Date.now(), done: false
  };
  DB.logs[t] = log; save();
  return log;
}

/* 状态不好的日子：5 题保命版。断档一天比做半小时崩掉更伤，
   参照她英语计划里那条经验——落课不补课、改时段。 */
function buildMini() {
  const t = today();
  refreshQueue();
  const fk = DB.queue[0] || P_TOPICS[0];
  const rv = dueWrongs().slice(0, 3);
  const need = 5 - rv.length;
  const log = {
    date: t, week: weekInfo().w, phase: weekInfo().phase, trackCh: '迷你模式', focusK: fk, focus2: null,
    qs: { warm: [], focus: genMany(fk, need, 1), track: [], review: rv },
    res: { warm: [], focus: [], track: [], review: [] },
    wrongToday: [], snap: {}, factsToday: [], mini: true,
    wrongCountAtStart: DB.wrong.length, startedAt: Date.now(), done: false
  };
  Object.keys(DB.mastery).forEach(k => { const m = DB.mastery[k]; log.snap[k] = { right: m.right, total: m.total }; });
  DB.logs[t] = log; save();
  return log;
}

/* ---------- 判定与记账 ---------- */
function judge(q, input) {
  if (q.type === 'choice') return input === q.ans;
  return eqVal(input, q.ans);
}
function recordAnswer(part, q, input, ok) {
  const log = DB.logs[today()];
  log.res[part].push({ qid: q.qid, ok, input });
  if (part === 'warm') { save(); return; }

  if (!q.topic) { save(); return; }   /* 梯子题的小学锚点，不计入初一掌握度 */
  bump(q.topic, ok);

  if (part === 'review') {
    const w = DB.wrong.find(x => x.qid === q.qid);
    if (w) {
      w.times = (w.times || 0) + 1;
      if (ok) {
        w.box = Math.min((w.box || 0) + 1, BOX_GAP.length - 1);
        w.due = addDays(today(), BOX_GAP[w.box]);
        if (w.box >= 3) { DB.wrong = DB.wrong.filter(x => x.qid !== w.qid); }
      } else { w.box = 0; w.due = addDays(today(), 1); }
    }
  } else if (!ok) {
    const rec = {
      qid: q.qid, topic: q.topic, tname: q.tname, ask: q.ask, q: q.q, ans: q.ans,
      type: q.type, opts: q.opts || null, sol: q.sol, box: 0,
      due: addDays(today(), 1), addedAt: today(), times: 0
    };
    DB.wrong.push(rec);
    log.wrongToday.push(rec);
  }
  save();
}

/* ---------- 诊断 ---------- */
function buildDiag() {
  const list = [];
  P_TOPICS.forEach(k => list.push(genQ(k)));
  /* 影响初一最深的几项各多测一题，样本太小判不准 */
  ['frac-add', 'frac-muldiv', 'decimal', 'simple-eq', 'calc-order'].forEach(k => list.push(genQ(k)));
  ['numline', 'rat-addsub', 'power'].forEach(k => list.push(genQ(k)));
  return list;
}
function finishDiag(qs, res) {
  const sc = {};
  qs.forEach((q, i) => {
    const s = sc[q.topic] || (sc[q.topic] = { right: 0, total: 0 });
    s.total++; if (res[i]) s.right++;
  });
  DB.diag = { done: true, date: today(), scores: sc };
  Object.keys(sc).forEach(k => { const m = DB.mastery[k] || (DB.mastery[k] = { right: 0, total: 0, r20: [] });
    m.total += sc[k].total; m.right += sc[k].right; });
  buildQueue();
  /* 诊断错题直接进错题本 */
  qs.forEach((q, i) => { if (!res[i]) DB.wrong.push({
    qid: q.qid, topic: q.topic, tname: q.tname, ask: q.ask, q: q.q, ans: q.ans,
    type: q.type, opts: q.opts || null, sol: q.sol, box: 0, due: addDays(today(), 1), addedAt: today(), times: 0 }); });
  delete DB.logs[today()];
  save();
}

/* 今天变强了什么：只跟他自己的过去比，不跟及格线比。
   数学自我效能感是焦虑影响成绩的中介，所以每天必须让他看见「我在变好」。*/
function gains() {
  const log = DB.logs[today()];
  if (!log) return [];
  const out = [];
  Object.keys(DB.mastery).forEach(k => {
    const now = DB.mastery[k], was = log.snap[k];
    if (!now || !now.total) return;
    const addN = now.total - (was ? was.total : 0);
    if (addN <= 0) return;
    const addR = now.right - (was ? was.right : 0);
    if (!was || !was.total) {
      if (addR > 0) out.push({ big: addR + '/' + addN, txt: '第一次练「' + TMAP[k].name + '」就做对 ' + addR + ' 道' });
      return;
    }
    const before = was.right / was.total, after = now.right / now.total;
    if (after - before >= 0.02) out.push({ big: '+' + Math.round((after - before) * 100) + '%', txt: TMAP[k].name + ' 从 ' + Math.round(before * 100) + '% 提到 ' + Math.round(after * 100) + '%' });
    else if (addR === addN && addN >= 2) out.push({ big: addN + '/' + addN, txt: TMAP[k].name + ' 今天全对' });
  });
  const gradN = (log.wrongCountAtStart || 0) + (log.wrongToday || []).length - DB.wrong.length;
  if (gradN > 0) out.push({ big: gradN + ' 道', txt: '错题毕业，从错题本里划掉了' });
  const rv = (log.res.review || []);
  if (rv.length && rv.filter(r => r.ok).length) out.push({ big: rv.filter(r => r.ok).length + '/' + rv.length, txt: '之前错过的题，今天做对了' });
  out.sort((a, b) => (b.txt.indexOf('第一次') >= 0 ? 1 : 0) - (a.txt.indexOf('第一次') >= 0 ? 1 : 0));
  return out.slice(0, 4);
}
/* 该知识点当前连对数，用于给真实的反馈而不是空话 */
function streakOf(k) {
  const m = DB.mastery[k]; if (!m || !m.r20) return 0;
  let n = 0; for (let i = m.r20.length - 1; i >= 0; i--) { if (m.r20[i]) n++; else break; }
  return n;
}

function weekReport() {
  let total = 0, right = 0, days = 0;
  for (let i = 0; i < 7; i++) {
    const d = addDays(today(), -i), l = DB.logs[d];
    if (!l) continue;
    let n = 0;
    ['warm', 'focus', 'track', 'review'].forEach(p => { (l.res[p] || []).forEach(r => { n++; total++; if (r.ok) right++; }); });
    if (n) days++;
  }
  return { total, right, days, rate: total ? Math.round(right / total * 100) : 0 };
}

/* ============================================================
   给 Claude 看的进度摘要
   页面没有后端，数据只在本机 localStorage，外部读不到。
   所以生成一段紧凑纯文本，家长一键复制、粘给 Claude 就能调计划。
   刻意不含姓名、学校、设备信息。
   ============================================================ */
function buildBrief() {
  const L = [];
  const wi = weekInfo();
  L.push('【数学补漏 app 进度摘要】生成于 ' + today() + '（' + wi.label + '）');
  L.push('每天设定 ' + DB.profile.dailyMin + ' 分钟，启动日 ' + DB.profile.kickoff + '，开学 ' + DB.profile.schoolStart);

  if (!DB.diag.done) { L.push('诊断：还没做'); }
  else {
    const rows = Object.keys(DB.diag.scores).map(k => { const s = DB.diag.scores[k]; return { k, r: s.right / s.total, s }; }).sort((a, b) => a.r - b.r);
    const fmt = r => TMAP[r.k].name + ' ' + r.s.right + '/' + r.s.total;
    const multi = rows.filter(r => r.s.total >= 2), single = rows.filter(r => r.s.total < 2);
    const bad = multi.filter(r => r.r < 0.5), mid = multi.filter(r => r.r >= 0.5 && r.r < 0.85), good = multi.filter(r => r.r >= 0.85);
    L.push('');
    L.push('== 入学诊断（' + DB.diag.date + '，共 ' + rows.reduce((a, r) => a + r.s.total, 0) + ' 题）==');
    L.push('要补：' + (bad.length ? bad.map(fmt).join('；') : '无'));
    L.push('夹生：' + (mid.length ? mid.map(fmt).join('；') : '无'));
    L.push('已稳：' + (good.length ? good.map(fmt).join('；') : '无'));
    if (single.length) {
      const sg = single.filter(r => r.r >= 1), sb = single.filter(r => r.r < 1);
      L.push('只测了 1 题、判不准（对：' + (sg.length ? sg.map(r => TMAP[r.k].name).join('、') : '无')
        + ' ／ 错：' + (sb.length ? sb.map(r => TMAP[r.k].name).join('、') : '无') + '）');
    }
  }

  L.push('');
  L.push('== 当前补漏队列（按顺序攻）==');
  L.push(DB.queue.length ? DB.queue.map((k, i) => (i + 1) + '.' + TMAP[k].name).join('  ') : '（空）');

  const mrows = TOPICS.filter(t => mstN(t.k) >= 8).map(t => ({ k: t.k, n: mstN(t.k), r: Math.round(mst(t.k) * 100), lv: pickLv(t.k) })).sort((a, b) => a.r - b.r);
  if (mrows.length) {
    L.push('');
    L.push('== 累计练过 ≥8 题的知识点（正确率 / 题数 / 当前难度档）==');
    mrows.forEach(x => L.push('  ' + TMAP[x.k].name + '  ' + x.r + '%  ' + x.n + ' 题  L' + x.lv + (TMAP[x.k].stage === 'P' ? '  [小学]' : '')));
  }

  L.push('');
  const grp = {}; DB.wrong.forEach(w => grp[w.topic] = (grp[w.topic] || 0) + 1);
  const gk = Object.keys(grp).sort((a, b) => grp[b] - grp[a]);
  L.push('== 错题本 ==');
  L.push('共 ' + DB.wrong.length + ' 道，今天到期 ' + dueWrongs().length + ' 道' + (gk.length ? '；最集中：' + gk.slice(0, 4).map(k => TMAP[k].name + ' ' + grp[k] + ' 道').join('，') : ''));

  L.push('');
  L.push('== 最近 14 天练习 ==');
  const days = [];
  for (let i = 13; i >= 0; i--) {
    const d = addDays(today(), -i), lg = DB.logs[d];
    let n = 0, r = 0;
    if (lg) ['warm', 'focus', 'track', 'review'].forEach(pp => (lg.res[pp] || []).forEach(x => { n++; if (x.ok) r++; }));
    if (n) days.push(d.slice(5) + ' ' + r + '/' + n + (lg.mini ? '(迷你)' : ''));
  }
  L.push(days.length ? days.join('  ') : '（还没有练习记录）');
  const w7 = weekReport();
  L.push('近 7 天：练了 ' + w7.days + ' 天，' + w7.total + ' 题，正确率 ' + w7.rate + '%');

  L.push('');
  L.push('== 其他 ==');
  L.push('已解锁数学史彩蛋 ' + DB.facts.length + '/24；完成周挑战 ' + Object.keys(DB.boss).length + ' 次');
  const ov = Object.keys(DB.trackOverride);
  if (ov.length) L.push('家长手改过的跟课周：' + ov.map(w => 'W' + w + '=' + DB.trackOverride[w].ch).join('；'));
  L.push('');
  L.push('（请据此判断：补漏优先级要不要重排、难度档是否合适、跟课表要不要调）');
  return L.join('\n');
}

/* 复制到剪贴板，失败就摊开让人手选 */
function copyBrief(host) {
  const txt = buildBrief();
  const done = () => { const t = el('div', 'sub', '已复制。粘到和 Claude 的对话里就行。'); host.appendChild(t); };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(txt).then(done).catch(() => showBrief(host, txt));
  } else showBrief(host, txt);
}
function showBrief(host, txt) {
  const old = host.querySelector('.briefbox'); if (old) old.remove();
  const ta = el('textarea', 'briefbox'); ta.value = txt || buildBrief(); ta.rows = 16; ta.readOnly = true;
  host.appendChild(ta);
  ta.focus(); ta.select();
  host.appendChild(el('div', 'sub', '自动复制没成功。长按上面的框全选复制，粘给 Claude。'));
}

/* ============================================================
   UI
   ============================================================ */
const $ = s => document.querySelector(s);
const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html !== undefined) e.innerHTML = html; return e; };
function sup(s) { return ('' + s).replace(/\^(-?\d+)/g, '<sup>$1</sup>'); }
function esc(s) { return ('' + s).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }

let TAB = 'today';
function go(tab) { TAB = tab; render(); window.scrollTo(0, 0); }

function render() {
  document.querySelectorAll('.tab').forEach(b => b.classList.toggle('on', b.dataset.t === TAB));
  const m = $('#main'); m.innerHTML = '';
  if (TAB === 'today') viewToday(m);
  else if (TAB === 'diag') viewDiag(m);
  else if (TAB === 'plan') viewPlan(m);
  else if (TAB === 'wrong') viewWrong(m);
  else if (TAB === 'parent') viewParent(m);
  else if (TAB === 'data') viewData(m);
  else if (TAB === 'set') viewSet(m);
}

/* ---------- 通用：做题器 ---------- */
function runner(host, qs, opt) {
  /* opt: {title, onDone(res), onEach(q,ok,input,i), showSol} */
  let i = 0; const res = [];
  const box = el('div', 'card');
  host.appendChild(box);
  const bar = el('div', 'pbar'); const fill = el('i'); bar.appendChild(fill);
  const head = el('div', 'qhead');
  box.appendChild(head); box.appendChild(bar);
  const body = el('div'); box.appendChild(body);

  function step() {
    if (i >= qs.length) {
      box.innerHTML = '';
      box.appendChild(el('div', 'done', '<b>这一组做完了</b><div class="sub">正确 ' + res.filter(Boolean).length + ' / ' + qs.length + '</div>'));
      if (opt.fact !== false) {
        const lg = DB.logs[today()];
        if (lg && (lg.factsToday || []).length < 2) {
          const ks = qs.map(x => x.topic).filter(Boolean);
          const f = pickFact(ks, DB.facts);
          if (f) {
            DB.facts.push(f.id); if (DB.facts.length > 200) DB.facts.shift();
            lg.factsToday.push(f.id); save();
            box.appendChild(el('div', 'fact', '<div class="ftag">数学冷知识 · 解锁</div><b>' + esc(f.t) + '</b><p>' + esc(f.b) + '</p>'));
          }
        }
      }
      if (opt.onDone) opt.onDone(res);
      return;
    }
    const q = qs[i];
    head.innerHTML = '<span>' + opt.title + '</span><span class="cnt">' + (i + 1) + ' / ' + qs.length + '</span>';
    fill.style.width = (i / qs.length * 100) + '%';
    body.innerHTML = '';
    if (q.tname) body.appendChild(el('div', 'tag', q.tname));
    body.appendChild(el('div', 'qtext', sup(esc(q.q))));

    let cur = '';
    const fb = el('div', 'fb');

    function submit(val) {
      const ok = judge(q, val);
      res[i] = ok;
      if (opt.onEach) opt.onEach(q, ok, val, i);
      fb.className = 'fb ' + (ok ? 'ok' : 'no');
      let head;
      if (ok) {
        const st = q.topic ? streakOf(q.topic) : 0;
        head = '✓ 对了' + (st >= 3 ? ' · 这个知识点连对 ' + st + ' 题了' : '');
      } else {
        head = '✗ 这次不对 —— 已经放进错题本，明天再考你一次';
      }
      let h = '<div class="fbhead">' + head + '</div>';
      if (!ok) h += '<div class="right">正确答案：<b>' + sup(esc(q.ans)) + '</b></div>';
      if (opt.showSol !== false && q.sol) h += '<ol class="sol">' + q.sol.map(s => '<li>' + sup(esc(s)) + '</li>').join('') + '</ol>';
      h += '<button class="btn next">下一题 →</button>';
      fb.innerHTML = h;
      fb.querySelector('.next').onclick = () => { i++; step(); };
      body.querySelectorAll('button,input').forEach(b => b.disabled = true);
      fb.querySelector('.next').disabled = false;
      fb.scrollIntoView({ block: 'nearest' });
    }

    if (q.type === 'choice') {
      const wrap = el('div', 'opts');
      q.opts.forEach(o => { const b = el('button', 'opt', sup(esc(o))); b.onclick = () => { wrap.querySelectorAll('.opt').forEach(x => x.classList.remove('sel')); b.classList.add('sel'); submit(o); }; wrap.appendChild(b); });
      body.appendChild(wrap);
    } else {
      const inp = el('input', 'ans'); inp.setAttribute('inputmode', 'none'); inp.readOnly = true;
      inp.placeholder = '答案（分数写成 3/4）';
      body.appendChild(inp);
      const kb = el('div', 'kb');
      const keys = ['7', '8', '9', '/', '4', '5', '6', '-', '1', '2', '3', '.', '0', '⌫', '清空', '确定'];
      keys.forEach(k => {
        const b = el('button', 'k' + (k === '确定' ? ' go' : (k === '⌫' || k === '清空' ? ' fn' : '')), k);
        b.onclick = () => {
          if (k === '⌫') cur = cur.slice(0, -1);
          else if (k === '清空') cur = '';
          else if (k === '确定') { if (!cur.trim()) return; submit(cur); return; }
          else cur += k;
          inp.value = cur;
        };
        kb.appendChild(b);
      });
      body.appendChild(kb);
      const skip = el('button', 'btn ghost', '不会，看解析');
      skip.onclick = () => submit('###');
      body.appendChild(skip);
    }
    body.appendChild(fb);
  }
  step();
}

/* ---------- 今日 ---------- */
function viewToday(m) {
  if (!DB.diag.done) {
    m.appendChild(el('div', 'card hero', '<h2>先做一次入学诊断</h2><p>21 道题，覆盖小学 13 个知识点 + 初一 3 个前置点，大约 20 分钟。做完才知道漏在哪，计划才有意义。中间可以停，成绩会存在这台设备上。</p><button class="btn big" onclick="go(\'diag\')">开始诊断 →</button>'));
    return;
  }
  const wi = weekInfo();
  const log = buildToday();
  const parts = [
    { k: 'warm', name: '① 口算热身', sub: '限时不限对，练手速', qs: log.qs.warm },
    { k: 'focus', name: '② 补漏主攻', sub: TMAP[log.focusK].name + (log.focus2 ? ' + ' + TMAP[log.focus2].name : ''), qs: log.qs.focus },
    { k: 'track', name: '③ 跟课练习', sub: log.trackCh, qs: log.qs.track },
    { k: 'review', name: '④ 错题重做', sub: log.qs.review.length ? '到期错题 ' + log.qs.review.length + ' 道' : '今天没有到期错题', qs: log.qs.review }
  ];
  const hdr = el('div', 'card');
  const lvTxt = log.mini ? '迷你模式' : ({ 1: '题目已自动调简单一档', 2: '', 3: '题目已自动调难一档' })[log.lv ? log.lv.focus : 2] || '';
  hdr.innerHTML = '<div class="row"><div><h2>' + cnDate(today()) + '</h2><div class="sub">' + wi.label + ' · 本周跟课：' + esc(log.trackCh)
    + (lvTxt ? '<br><span class="lvtag">' + lvTxt + '</span>' : '') + '</div></div></div>';
  m.appendChild(hdr);

  /* 今天变强了什么——放在最上面，先看到进步再看到任务 */
  const gs = gains();
  const anyDone = ['warm', 'focus', 'track', 'review'].some(k => (log.res[k] || []).length);
  if (gs.length) {
    const gc = el('div', 'card gain');
    gc.innerHTML = '<b>今天你变强了这些</b>' + gs.map(g => '<div class="grow"><i>' + esc(g.big) + '</i><span>' + esc(g.txt) + '</span></div>').join('');
    m.appendChild(gc);
  } else if (anyDone) {
    m.appendChild(el('div', 'card gain', '<b>今天守住了</b><div class="sub">没有退步。基础题稳住不掉，本来就是这个阶段该拿到的东西。</div>'));
  }

  parts.forEach(p => {
    const doneN = log.res[p.k].length, totN = p.qs.length;
    const c = el('div', 'card task' + (totN === 0 ? ' dim' : (doneN >= totN ? ' fin' : '')));
    const rightN = log.res[p.k].filter(r => r.ok).length;
    c.innerHTML = '<div class="row"><div><b>' + p.name + '</b><div class="sub">' + esc(p.sub) + '</div></div>'
      + '<div class="prog">' + (totN === 0 ? '—' : doneN + '/' + totN + (doneN >= totN ? ' ✓ 对 ' + rightN : '')) + '</div></div>';
    if (totN > 0 && doneN < totN) {
      const b = el('button', 'btn', doneN ? '继续做' : '开始');
      b.onclick = () => {
        m.innerHTML = '';
        const back = el('button', 'btn ghost', '← 回今日'); back.onclick = () => go('today'); m.appendChild(back);
        runner(m, p.qs.slice(doneN), {
          title: p.name,
          onEach: (q, ok, val) => recordAnswer(p.k, q, val, ok),
          onDone: () => { const b2 = el('button', 'btn big', '回到今日任务'); b2.onclick = () => go('today'); m.appendChild(b2); }
        });
      };
      c.appendChild(b);
    }
    m.appendChild(c);
  });

  /* 本周挑战：3 道最难档的题，攻下来解锁一条彩蛋。用内容当奖励，不用积分 */
  if (!log.mini && wi.phase === 'term') {
    const bkey = 'W' + wi.w;
    const doneB = DB.boss[bkey];
    const bc = el('div', 'card boss' + (doneB ? ' fin' : ''));
    bc.innerHTML = '<div class="row"><div><b>本周挑战 · ' + bkey + '</b><div class="sub">'
      + (doneB ? '这周的挑战已经攻下来了，下周一有新的。' : '3 道本周内容里最难档的题。不计入正确率，做不出来不影响任何东西。') + '</div></div></div>';
    if (!doneB) {
      const bb = el('button', 'btn', '来一把');
      bb.onclick = () => {
        const tr = trackOf(wi.w);
        const bqs = tr.ks.slice(0, 3).concat(tr.ks, tr.ks).slice(0, 3).map(k => genQ(k, 3));
        m.innerHTML = '';
        const back = el('button', 'btn ghost', '← 回今日'); back.onclick = () => go('today'); m.appendChild(back);
        runner(m, bqs, {
          title: '本周挑战', fact: false,
          onDone: res => {
            DB.boss[bkey] = { date: today(), right: res.filter(Boolean).length };
            const f = pickFact(tr.ks, DB.facts);
            if (f) { DB.facts.push(f.id); m.appendChild(el('div', 'card fact', '<div class="ftag">挑战奖励 · 解锁一条冷知识</div><b>' + esc(f.t) + '</b><p>' + esc(f.b) + '</p>')); }
            save();
            const b2 = el('button', 'btn big', '回到今日任务'); b2.onclick = () => go('today'); m.appendChild(b2);
          }
        });
      };
      bc.appendChild(bb);
    }
    m.appendChild(bc);
  }

  /* 状态不好的日子：不硬撑，也不断档 */
  if (!log.mini && !anyDone) {
    const mc = el('div', 'card');
    mc.innerHTML = '<b>今天状态不好？</b><div class="sub">换成 5 题的迷你版。断一天比硬撑到崩掉更难补回来。</div>';
    const mb = el('button', 'btn ghost', '换成 5 题');
    mb.onclick = () => { if (confirm('今天改成 5 题迷你版？')) { buildMini(); go('today'); } };
    mc.appendChild(mb);
    m.appendChild(mc);
  }

  if (log.wrongToday.length) {
    const c = el('div', 'card note');
    c.innerHTML = '<b>今天错了 ' + log.wrongToday.length + ' 道</b><div class="sub">去「家长」页拿今晚讲哪 2 道</div>';
    const b = el('button', 'btn', '看家长清单'); b.onclick = () => go('parent'); c.appendChild(b);
    m.appendChild(c);
  }
}

/* ---------- 诊断 ---------- */
let DIAGQS = null, DIAGRES = null;
function viewDiag(m) {
  if (DB.diag.done && !DIAGQS) {
    const c = el('div', 'card');
    let h = '<h2>诊断结果 · ' + DB.diag.date + '</h2><table class="tb"><tr><th>知识点</th><th>正确</th><th>判断</th></tr>';
    const rows = Object.keys(DB.diag.scores).map(k => { const s = DB.diag.scores[k]; return { k, r: s.right / s.total, s }; }).sort((a, b) => a.r - b.r);
    rows.forEach(r => {
      const lv = r.s.total < 2 ? ['只测 1 题', ''] : r.r >= 0.85 ? ['稳', 'g'] : r.r >= 0.5 ? ['夹生', 'w'] : ['要补', 'b'];
      h += '<tr><td>' + TMAP[r.k].name + '<span class="st">' + (TMAP[r.k].stage === 'P' ? '小学' : '七上') + '</span></td><td>' + r.s.right + '/' + r.s.total + '</td><td><span class="pill ' + lv[1] + '">' + lv[0] + '</span></td></tr>';
    });
    h += '</table>';
    c.innerHTML = h;
    m.appendChild(c);
    const c2 = el('div', 'card');
    c2.innerHTML = '<b>当前补漏队列</b><div class="sub">按「影响初一的程度 × 掌握度」排序，做到近 20 题正确率 85% 自动毕业出队</div><ol class="q">'
      + DB.queue.map(k => '<li>' + TMAP[k].name + '</li>').join('') + '</ol>';
    m.appendChild(c2);
    const c3 = el('div', 'card note');
    c3.innerHTML = '<b>把结果发给 Claude</b><div class="sub">这个页面没有后端，成绩只存在这台设备上，外面读不到。'
      + '点下面按钮复制一段摘要（不含姓名学校），粘到对话里，他就能判断补漏顺序要不要重排、难度合不合适。</div>';
    const cb = el('button', 'btn', '复制进度摘要');
    cb.onclick = () => copyBrief(c3);
    const cb2 = el('button', 'btn ghost', '直接看这段文字');
    cb2.onclick = () => showBrief(c3);
    c3.appendChild(cb); c3.appendChild(cb2);
    m.appendChild(c3);

    const b = el('button', 'btn ghost', '重做诊断（会清空队列，保留错题本）');
    b.onclick = () => { if (confirm('重做诊断？')) { DIAGQS = buildDiag(); DIAGRES = []; render(); } };
    m.appendChild(b);
    return;
  }
  if (!DIAGQS) { DIAGQS = buildDiag(); DIAGRES = []; }
  runner(m, DIAGQS, {
    title: '入学诊断', showSol: true,
    onEach: (q, ok, v, i) => { DIAGRES[i] = ok; },
    onDone: res => {
      finishDiag(DIAGQS, res); DIAGQS = null;
      const b = el('button', 'btn big', '看结果和计划'); b.onclick = () => { go('diag'); }; m.appendChild(b);
    }
  });
}

/* ---------- 计划 ---------- */
function viewPlan(m) {
  const wi = weekInfo();
  const c = el('div', 'card');
  const dMid = dayDiff(today(), addDays(DB.profile.schoolStart, 9 * 7));   /* 期中约在 W10 */
  const dFin = dayDiff(today(), '2027-01-14');                             /* 深圳规定期末不早于此日 */
  c.innerHTML = '<h2>学习计划</h2><div class="sub">' + wi.label + '。启动日 ' + DB.profile.kickoff + '，开学 ' + DB.profile.schoolStart
    + '。每天四段：口算热身 → 补漏主攻 → 跟课练习（开头一对搭桥题）→ 到期错题重做。</div>'
    + '<div class="miles">'
    + '<div><b>' + (dMid > 0 ? dMid + ' 天' : '已过') + '</b><span>到期中（约 11 月初）</span></div>'
    + '<div><b>' + (dFin > 0 ? dFin + ' 天' : '已过') + '</b><span>到期末（不早于 1/14）</span></div>'
    + '<div><b>' + Math.max(0, Math.ceil(dFin / 7)) + ' 周</b><span>剩余可用周数</span></div>'
    + '</div>';
  m.appendChild(c);

  const k = el('div', 'card');
  k.innerHTML = '<b>8/29 – 8/31 破冰三天</b><div class="sub">他 29 号才从老家回深圳，开学前只有这三天，目标不是学完，是开学第一节课能听懂。</div><ol class="q">'
    + '<li>第 1 天：做完入学诊断（21 题），当晚家长陪着过 2 道错题</li>'
    + '<li>第 2 天：主攻诊断里最差的那个小学知识点 + 预习数轴/相反数/绝对值</li>'
    + '<li>第 3 天：昨天错题重做 + 预习有理数加减，把「减号改写成加相反数」练成肌肉记忆</li>'
    + '</ol><div class="sub">目的不是学完，是开学第一节课能听懂，先把「我能听懂」这个感觉拿回来。</div>';
  m.appendChild(k);

  const t = el('div', 'card');
  let h = '<b>一学期 20 周跟课表</b><div class="sub">按北师大版（2024）七上章序 + 深圳市 2026–2027 校历排的。'
    + '以学校实际进度为准，不一样就点「改」。</div><div class="scrollx"><table class="tb"><tr><th>周</th><th>日期</th><th>跟课内容</th><th></th></tr>';
  for (let w = 1; w <= 20; w++) {
    const tr = trackOf(w);
    const d0 = addDays(DB.profile.schoolStart, (w - 1) * 7);
    const dd = d0.slice(5).replace('-', '/') + '–' + addDays(d0, 6).slice(5).replace('-', '/');
    h += '<tr' + (w === wi.w && wi.phase === 'term' ? ' class="now"' : '') + '><td>W' + w + '</td><td class="nw">' + dd + '</td><td>' + esc(tr.ch)
      + (tr.mile ? '<div class="mile">' + esc(tr.mile) + '</div>' : '')
      + '</td><td><button class="mini" data-w="' + w + '">改</button></td></tr>';
  }
  h += '</table></div>';
  t.innerHTML = h;
  t.querySelectorAll('.mini').forEach(b => b.onclick = () => {
    const w = +b.dataset.w, tr = trackOf(w);
    const ch = prompt('第 ' + w + ' 周学校在讲什么？（只改显示文字）', tr.ch);
    if (ch === null) return;
    const opts = M_TOPICS.map((x, i) => (i + 1) + '=' + TMAP[x].name).join('  ');
    const pickStr = prompt('这周练哪些知识点？填编号，逗号分隔\n' + opts, tr.ks.map(x => M_TOPICS.indexOf(x) + 1).join(','));
    if (pickStr === null) return;
    const ks = pickStr.split(/[,，\s]+/).map(x => M_TOPICS[+x - 1]).filter(Boolean);
    DB.trackOverride[w] = { ch, ks: ks.length ? ks : tr.ks };
    delete DB.logs[today()];
    save(); render();
  });
  m.appendChild(t);

  const g = el('div', 'card');
  g.innerHTML = '<b>阶段目标（对齐考试节点）</b><ol class="q">'
    + '<li><b>开学第 4 周末</b>（9 月底）：有理数加减单独测 10 题错不超过 2 题；口算热身正确率 ≥ 80%</li>'
    + '<li><b>国庆假期</b>（10/1–10/7）：一天不断，每天 15 分钟也算。断档一周开学回来就跟不上乘除</li>'
    + '<li><b>期中前</b>（第 9 周）：(−2)² 和 −2² 连续 10 题不错；补漏队列清掉 3 个小学知识点</li>'
    + '<li><b>第 14 周</b>（整式学完）：去括号变号 10 题对 8 道；错题本存量降到 30 道以内</li>'
    + '<li><b>期末前</b>（1 月上旬）：含分母的一元一次方程 10 题对 7 道；错题本降到 20 道以内</li>'
    + '</ol><div class="sub">及格线不是目标。他现在丢分的大头是运算规则，不是难题——'
    + '把「会做的题不丢分」做到了，分数自己会上来。</div>';
  m.appendChild(g);
}

/* ---------- 错题本 ---------- */
function viewWrong(m) {
  const t = today();
  const due = DB.wrong.filter(w => w.due <= t);
  const c = el('div', 'card');
  c.innerHTML = '<h2>错题本</h2><div class="sub">共 ' + DB.wrong.length + ' 道，今天到期 ' + due.length + ' 道。答对一次隔 1 天再考，连续对 3 轮就毕业移出。</div>';
  m.appendChild(c);
  if (due.length) {
    const b = el('button', 'btn big', '重做今天到期的 ' + due.length + ' 道');
    b.onclick = () => {
      m.innerHTML = '';
      const back = el('button', 'btn ghost', '← 返回'); back.onclick = () => go('wrong'); m.appendChild(back);
      buildToday();
      runner(m, due, { title: '错题重做', onEach: (q, ok, v) => recordAnswer('review', q, v, ok), onDone: () => { const b2 = el('button', 'btn big', '完成'); b2.onclick = () => go('wrong'); m.appendChild(b2); } });
    };
    m.appendChild(b);
  }
  const grp = {};
  DB.wrong.forEach(w => (grp[w.topic] = grp[w.topic] || []).push(w));
  Object.keys(grp).sort((a, b) => grp[b].length - grp[a].length).forEach(k => {
    const c2 = el('div', 'card');
    let h = '<b>' + TMAP[k].name + '</b> <span class="pill b">' + grp[k].length + ' 道</span>';
    grp[k].forEach(w => { h += '<div class="wq"><div class="wqq">' + sup(esc(w.q)) + '</div><div class="wqa">答案 ' + sup(esc(w.ans)) + ' · 下次重考 ' + w.due + '</div></div>'; });
    c2.innerHTML = h;
    m.appendChild(c2);
  });
  if (!DB.wrong.length) m.appendChild(el('div', 'card dim', '错题本是空的。'));
}

/* ---------- 家长 ---------- */
function viewParent(m) {
  const t = today();
  const log = DB.logs[t];
  const c = el('div', 'card');
  c.innerHTML = '<h2>今晚这 10 分钟怎么用</h2><div class="sub">别通篇讲。挑下面 2 道，让他讲给你听，你只负责问问题。</div>';
  m.appendChild(c);

  let wt = (log && log.wrongToday) ? log.wrongToday.slice() : [];
  if (!wt.length) wt = DB.wrong.filter(w => w.addedAt === t);
  if (!wt.length) {
    m.appendChild(el('div', 'card dim', '今天还没有错题记录。等他做完今日任务再来看。'));
  } else {
    const cnt = {}; wt.forEach(w => cnt[w.topic] = (cnt[w.topic] || 0) + 1);
    wt.sort((a, b) => cnt[b.topic] - cnt[a.topic]);
    const seen = new Set(); const chosen = [];
    wt.forEach(w => { if (chosen.length < 2 && !seen.has(w.topic)) { seen.add(w.topic); chosen.push(w); } });
    if (chosen.length < 2 && wt.length > 1) chosen.push(wt.find(w => !chosen.includes(w)));
    chosen.filter(Boolean).forEach((w, i) => {
      const c2 = el('div', 'card');
      c2.innerHTML = '<div class="tag">第 ' + (i + 1) + ' 道 · ' + TMAP[w.topic].name + '</div>'
        + '<div class="qtext">' + sup(esc(w.q)) + '</div>'
        + '<div class="kv"><span>正确答案</span><b>' + sup(esc(w.ans)) + '</b></div>'
        + '<div class="pask"><b>你问这句</b><div>' + esc(w.ask) + '</div></div>'
        + '<details><summary>讲解思路（他讲不出来你再看）</summary><ol class="sol">' + w.sol.map(s => '<li>' + sup(esc(s)) + '</li>').join('') + '</ol></details>';
      m.appendChild(c2);
    });
  }

  const tip = el('div', 'card note');
  tip.innerHTML = '<b>三条底线</b><ol class="q">'
    + '<li>不说「这么简单都不会」。他现在的问题是小学没打牢，不是不聪明。</li>'
    + '<li>只讲 2 道。讲多了他记不住，也会把 10 分钟拖成 40 分钟然后崩。</li>'
    + '<li>让他讲、你听。他能把步骤说顺就算过关，说不出来的地方才是真漏洞。</li>'
    + '<li>表扬要落在具体动作上：「你这次符号定对了」「你先算括号了」。别说「你真聪明」——'
    + '夸天赋会让他下次遇到难题就认定「我不是这块料」，夸具体做对的步骤才顶用。</li></ol>';
  m.appendChild(tip);

  const cq = el('div', 'card note');
  cq.innerHTML = '<b>卡住了想问 Claude</b><div class="sub">连续两周没进步、或者不知道该不该调计划的时候，复制这段摘要发给他。</div>';
  const cqb = el('button', 'btn ghost', '复制进度摘要');
  cqb.onclick = () => copyBrief(cq);
  cq.appendChild(cqb);
  m.appendChild(cq);

  const w7 = weekReport();
  const wr = el('div', 'card');
  wr.innerHTML = '<b>最近 7 天</b><div class="sub">练了 ' + w7.days + ' 天，共 ' + w7.total + ' 题，正确率 ' + w7.rate + '%。'
    + (w7.days < 4 ? '天数偏少——先保住每天都碰一下，比某天做很多有用。' : '节奏没问题，保持。') + '</div>';
  m.appendChild(wr);
}

/* ---------- 数据 ---------- */
function viewData(m) {
  const c = el('div', 'card');
  c.innerHTML = '<h2>最近 14 天</h2>';
  const rows = [];
  for (let i = 13; i >= 0; i--) {
    const d = addDays(today(), -i), l = DB.logs[d];
    let n = 0, r = 0;
    if (l) ['warm', 'focus', 'track', 'review'].forEach(p => (l.res[p] || []).forEach(x => { n++; if (x.ok) r++; }));
    rows.push({ d, n, r });
  }
  let h = '<div class="chart">';
  rows.forEach(x => {
    const pct = x.n ? Math.round(x.r / x.n * 100) : 0;
    h += '<div class="bar" title="' + x.d + ' ' + x.r + '/' + x.n + '"><i style="height:' + (x.n ? Math.max(pct, 4) : 0) + '%"></i><span>' + x.d.slice(5).replace('-', '/') + '</span></div>';
  });
  h += '</div><div class="sub">柱高 = 当天正确率，没柱子 = 那天没练。</div>';
  c.innerHTML += h;
  m.appendChild(c);

  const c2 = el('div', 'card');
  let h2 = '<b>各知识点掌握度</b><div class="sub">按累计做题正确率，做满 8 题才显示判断</div><table class="tb"><tr><th>知识点</th><th>题数</th><th>正确率</th><th></th></tr>';
  TOPICS.forEach(t => {
    const n = mstN(t.k); if (!n) return;
    const r = Math.round(mst(t.k) * 100);
    const lv = n < 8 ? ['样本少', ''] : r >= 85 ? ['稳', 'g'] : r >= 60 ? ['夹生', 'w'] : ['要补', 'b'];
    h2 += '<tr><td>' + t.name + '<span class="st">' + (t.stage === 'P' ? '小学' : '七上') + '</span></td><td>' + n + '</td><td>' + r + '%</td><td><span class="pill ' + lv[1] + '">' + lv[0] + '</span></td></tr>';
  });
  h2 += '</table>';
  c2.innerHTML = h2;
  m.appendChild(c2);
}

/* ---------- 设置 ---------- */
function viewSet(m) {
  const c = el('div', 'card');
  c.innerHTML = '<h2>设置</h2>'
    + '<div class="kv"><span>启动日</span><input id="s-kick" value="' + DB.profile.kickoff + '"></div>'
    + '<div class="kv"><span>开学日</span><input id="s-ss" value="' + DB.profile.schoolStart + '"></div>'
    + '<div class="kv"><span>每天分钟</span><input id="s-min" value="' + DB.profile.dailyMin + '"></div>';
  const b = el('button', 'btn', '保存');
  b.onclick = () => {
    DB.profile.kickoff = $('#s-kick').value.trim();
    DB.profile.schoolStart = $('#s-ss').value.trim();
    DB.profile.dailyMin = Math.max(10, Math.min(90, +$('#s-min').value || 25));
    delete DB.logs[today()];
    save(); alert('已保存，今日任务会按新时长重新生成'); go('today');
  };
  c.appendChild(b);
  m.appendChild(c);

  const c2 = el('div', 'card');
  c2.innerHTML = '<b>进度备份</b><div class="sub">数据只存在这台设备的浏览器里。换设备、清缓存前先导出。</div>';
  const b1 = el('button', 'btn', '导出进度文件');
  b1.onclick = () => {
    const blob = new Blob([JSON.stringify(DB)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = 'math-progress-' + today() + '.json';
    document.body.appendChild(a); a.click(); a.remove();
  };
  const b2 = el('button', 'btn ghost', '复制进度到剪贴板');
  b2.onclick = () => { const s = JSON.stringify(DB); navigator.clipboard ? navigator.clipboard.writeText(s).then(() => alert('已复制')) : prompt('手动复制：', s); };
  const inp = el('input', 'file'); inp.type = 'file'; inp.accept = '.json';
  inp.onchange = e => { const f = e.target.files[0]; if (!f) return; const r = new FileReader();
    r.onload = () => { try { const d = JSON.parse(r.result); if (!d.ver) throw new Error('格式不对'); DB = d; save(); alert('已导入'); go('today'); } catch (err) { alert('导入失败：' + err.message); } };
    r.readAsText(f); };
  const b0 = el('button', 'btn', '复制进度摘要（给 Claude 看）');
  b0.onclick = () => copyBrief(c2);
  c2.appendChild(b0);
  c2.appendChild(b1); c2.appendChild(b2);
  c2.appendChild(el('div', 'sub', '导入备份：'));
  c2.appendChild(inp);
  m.appendChild(c2);

  const c3 = el('div', 'card');
  const b3 = el('button', 'btn ghost danger', '清空全部数据');
  b3.onclick = () => { if (confirm('全部清空，不可恢复。确定？')) { localStorage.removeItem(KEY); load(); go('today'); } };
  c3.appendChild(b3);
  m.appendChild(c3);
}

/* ---------- 启动 ---------- */
load();
document.querySelectorAll('.tab').forEach(b => b.onclick = () => go(b.dataset.t));
render();
