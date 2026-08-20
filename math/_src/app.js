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
  const old = host.querySelector('.brief'); if (old) old.remove();
  const ta = el('textarea', 'brief'); ta.value = txt || buildBrief(); ta.rows = 16; ta.readOnly = true;
  host.appendChild(ta);
  ta.focus(); ta.select();
  host.appendChild(el('div', 'sub', '自动复制没成功。长按上面的框全选复制，粘给 Claude。'));
}


/* ============================================================
   界面层
   两套视图，分得很干净：
     孩子看到 今天 / 重练 / 收藏 —— 只有正向信息和行动
     家长区在右上角，放诊断分档、20 周计划、今晚讲哪 2 题、
     进度摘要、设置、清空。可选 4 位 PIN。
   孩子不该看到「你要补 6 项」的清单，也不该能把每天分钟数
   调成 10 或者一键清空自己的记录。
   ============================================================ */
const $ = s => document.querySelector(s);
const el = (t, c, h) => { const e = document.createElement(t); if (c) e.className = c; if (h !== undefined) e.innerHTML = h; return e; };
function esc(s) { return ('' + s).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }
/* 所有要显示的数学文本都过这里：上标 + 半角负号统一成数学负号。
   生成器里散落的 -7/60、= -12 混着题干的 −，看着很脏。
   判定走 parseVal，两种负号都吃，所以这层纯显示、不影响对错。 */
function sup(s) {
  return ('' + s)
    .replace(/\^(-?\d+)/g, '<sup>$1</sup>')
    .replace(/(^|[\s=(（+×÷,，：|])-(\d)/g, '$1−$2');
}
function ans(s) { return sup(esc(s)); }
/* 题干形态：纯表达式给大等宽，长文字题给正常行文，中间态压字号。
   一行放不下会折成「= ?」孤零零一行，很难看，所以按长度分三档。 */
function qClass(q) {
  q = q || '';
  const cn = q.replace(/[\s\d+\-−×÷=?()（）。，、：/²³|]/g, '').length;
  if (cn > 8) return 'q long';
  return q.length > 16 ? 'q mid' : 'q';
}

const KID_TABS = [
  { k: 'today', ic: '◉', n: '今天' },
  { k: 'redo', ic: '◐', n: '重练' },
  { k: 'coll', ic: '◇', n: '收藏' }
];
const P_TABS = [
  { k: 'p-plan', n: '计划' }, { k: 'p-diag', n: '诊断' }, { k: 'p-tonight', n: '今晚' },
  { k: 'p-data', n: '数据' }, { k: 'p-set', n: '设置' }
];

let VIEW = 'today';
let PARENT_OK = false;        /* 本次会话是否已通过 PIN */
function isParent(v) { return (v || VIEW).indexOf('p-') === 0; }

function go(v) {
  if (isParent(v) && DB.profile.pin && !PARENT_OK) { VIEW = 'p-lock'; render(); return; }
  VIEW = v; render();
  window.scrollTo(0, 0);
}

function render() {
  document.body.classList.toggle('parent', isParent() || VIEW === 'p-lock');
  const main = $('#main'); main.innerHTML = ''; main.className = '';
  renderTop();
  renderTabs();
  const V = {
    today: viewToday, redo: viewRedo, coll: viewColl,
    'p-lock': viewLock, 'p-plan': viewPlan, 'p-diag': viewDiag,
    'p-tonight': viewTonight, 'p-data': viewData, 'p-set': viewSet
  };
  (V[VIEW] || viewToday)(main);
}

function renderTop() {
  const t = $('#top');
  if (isParent() || VIEW === 'p-lock') {
    t.innerHTML = '<div><span class="d">家长区</span><span class="w">孩子看到的是另一套界面</span></div>';
    const b = el('button', 'pbtn', '回孩子视图'); b.onclick = () => { go('today'); }; t.appendChild(b);
    return;
  }
  const wi = weekInfo();
  const dd = parseD(today());
  t.innerHTML = '<div><span class="d">' + (dd.getMonth() + 1) + '<i>月</i>' + dd.getDate() + '<i>日</i></span>'
    + '<span class="w">' + '周' + '日一二三四五六'[dd.getDay()] + ' · ' + esc(wi.label) + '</span></div>';
  const b = el('button', 'pbtn', '家长'); b.onclick = () => go('p-plan'); t.appendChild(b);
}

function renderTabs() {
  const n = $('#tabs'); n.innerHTML = ''; n.className = 'tabs';
  if (VIEW === 'doing' || VIEW === 'p-lock') { n.className = 'tabs hide'; return; }
  const list = isParent() ? P_TABS : KID_TABS;
  list.forEach(t => {
    const b = el('button', VIEW === t.k ? 'on' : '', (t.ic ? '<b>' + t.ic + '</b>' : '') + t.n);
    b.onclick = () => go(t.k); n.appendChild(b);
  });
}

/* ============================================================
   做题
   题目居中放大、键盘钉在拇指区、答对答错都给强反馈
   ============================================================ */
function runner(qs, opt) {
  VIEW = 'doing'; renderTabs();
  const main = $('#main'); main.innerHTML = ''; main.className = 'full';
  document.body.classList.remove('parent');
  $('#top').innerHTML = '';
  const bk = el('button', 'pbtn', '× 退出'); bk.onclick = () => go(opt.backTo || 'today');
  $('#top').innerHTML = '<div><span class="d">' + esc(opt.title) + '</span></div>';
  $('#top').appendChild(bk);

  let i = 0; const res = [];
  const wrap = el('div', 'qwrap'); main.appendChild(wrap);
  const dots = el('div', 'dots'); wrap.appendChild(dots);
  const body = el('div', 'qbody'); wrap.appendChild(body);
  const padSlot = el('div'); wrap.appendChild(padSlot);

  function paintDots(judged) {
    dots.innerHTML = '';
    qs.forEach((q, n) => {
      let c = '';
      if (n < i || (n === i && judged !== undefined)) c = res[n] ? 'ok' : 'no';
      else if (n === i) c = 'cur';
      dots.appendChild(el('i', c));
    });
    if (judged !== undefined && dots.children[i]) dots.children[i].classList.add('pulse');
  }

  function step() {
    if (i >= qs.length) return finish();
    const q = qs[i];
    paintDots();
    body.innerHTML = ''; padSlot.innerHTML = '';
    body.className = 'qbody fadein';

    if (q.tname) body.appendChild(el('div', 'tag' + (q.bridge === 'p' ? '' : (q.topic ? ' plain' : '')), esc(q.tname)));
    body.appendChild(el('div', qClass(q.q), sup(esc(q.q))));

    let cur = '';
    const fb = el('div', 'fb');

    function submit(val) {
      const ok = judge(q, val);
      res[i] = ok;
      if (opt.onEach) opt.onEach(q, ok, val, i);
      paintDots(ok);
      fb.className = 'fb ' + (ok ? 'ok' : 'no') + ' fadein';
      let h;
      if (ok) {
        const st = q.topic ? streakOf(q.topic) : 0;
        h = '<div class="h"><span class="mk">✓</span>' + (st >= 3 ? '连对 ' + st + ' 题' : '对了') + '</div>';
      } else {
        h = '<div class="h"><span class="mk">→</span>进错题本了，明天再考你一次</div>'
          + '<div class="ra">答案 <b>' + ans(q.ans) + '</b></div>';
      }
      if (opt.showSol !== false && q.sol) h += '<ol class="sol">' + q.sol.map(x => '<li>' + sup(esc(x)) + '</li>').join('') + '</ol>';
      fb.innerHTML = h;
      const nx = el('button', 'go', i + 1 >= qs.length ? '这组做完了 →' : '下一题 →');
      nx.onclick = () => { i++; step(); };
      fb.appendChild(nx);
      padSlot.innerHTML = '';
      const hn = body.querySelector('.hint'); if (hn) hn.remove();
      const sl = body.querySelector('.slot'); if (sl && !ok) sl.style.borderColor = 'var(--signal)';
      body.querySelectorAll('.opt').forEach(b => b.disabled = true);
      body.appendChild(fb);
      nx.scrollIntoView({ block: 'nearest' });
    }

    if (q.type === 'choice') {
      const w = el('div', 'opts');
      q.opts.forEach(o => { const b = el('button', 'opt', sup(esc(o))); b.onclick = () => submit(o); w.appendChild(b); });
      body.appendChild(w);
    } else {
      const slot = el('div', 'slot', '<span class="caret"></span>');
      body.appendChild(slot);
      body.appendChild(el('div', 'hint', q.type === 'frac' ? '分数写成 3/4，约到最简；负号用 −' : '用下面的键盘输入'));
      const pad = el('div', 'pad');
      [['7'], ['8'], ['9'], ['/'], ['4'], ['5'], ['6'], ['−'], ['1'], ['2'], ['3'], ['.'],
       ['0'], ['删', 'fn'], ['清空', 'fn'], ['确定', 'ok']].forEach(k => {
        const b = el('button', k[1] || '', k[0]);
        b.onclick = () => {
          if (k[0] === '删') cur = cur.slice(0, -1);
          else if (k[0] === '清空') cur = '';
          else if (k[0] === '确定') { if (cur.trim()) submit(cur); return; }
          else cur += (k[0] === '−' ? '-' : k[0]);
          slot.className = 'slot' + (cur ? ' has' : '');
          slot.innerHTML = cur ? esc(cur.replace(/-/g, '−')) : '<span class="caret"></span>';
        };
        pad.appendChild(b);
      });
      padSlot.appendChild(pad);
      const sk = el('button', 'skip', '不会做，直接看解析');
      sk.onclick = () => submit('###');
      padSlot.appendChild(sk);
    }
  }

  function finish() {
    body.innerHTML = ''; padSlot.innerHTML = ''; paintDots();
    const n = res.filter(Boolean).length;
    const c = el('div', 'card fadein');
    c.innerHTML = '<div class="eyebrow">这一组做完了</div><h2 class="mono" style="font-size:30px">' + n + ' / ' + qs.length + '</div>';
    body.appendChild(c);
    if (opt.fact !== false) {
      const lg = DB.logs[today()];
      if (lg && (lg.factsToday || []).length < 2) {
        const f = pickFact(qs.map(x => x.topic).filter(Boolean), DB.facts);
        if (f) {
          DB.facts.push(f.id); if (DB.facts.length > 300) DB.facts.shift();
          lg.factsToday.push(f.id); save();
          body.appendChild(factCard(f, '解锁一张收藏卡'));
        }
      }
    }
    if (opt.onDone) opt.onDone(res, body);
    const b = el('button', 'go', '回到今天');
    b.onclick = () => go(opt.backTo || 'today');
    body.appendChild(b);
  }
  step();
}
function factCard(f, label) {
  return el('div', 'fdetail fadein', '<div class="eyebrow">' + esc(label) + '</div><h3>' + esc(f.t) + '</h3><p>' + esc(f.b) + '</p>');
}

/* ============================================================
   孩子视图 · 今天
   ============================================================ */
const SEG = [
  { k: 'warm', n: '热身', full: '口算热身' },
  { k: 'focus', n: '补漏', full: '补漏主攻' },
  { k: 'track', n: '跟课', full: '跟课练习' },
  { k: 'review', n: '重练', full: '错题重练' }
];

function viewToday(m) {
  if (!DB.diag.done) return viewFirst(m);
  const wi = weekInfo();
  const log = buildToday();

  /* 本周在哪一站 */
  if (wi.phase === 'term') {
    const c = el('div', 'weekbar');
    let h = '<div class="route mini">';
    for (let w = 1; w <= 20; w++) h += '<div class="stop ' + (w < wi.w ? 'done' : w === wi.w ? 'now' : '') + '"><i></i></div>';
    h += '</div><div class="wt">学校在讲 · ' + esc(log.trackCh) + '</div>';
    c.innerHTML = h;
    m.appendChild(c);
  }

  /* 今天四站 */
  const segs = SEG.map(s => ({ s, qs: log.qs[s.k] || [], done: (log.res[s.k] || []).length }));
  const live = segs.filter(x => x.qs.length);
  const curIdx = live.findIndex(x => x.done < x.qs.length);
  const c2 = el('div', 'card');
  let h2 = '<div class="eyebrow">今天' + '零一二三四五'[live.length] + '站</div><div class="route">';
  live.forEach((x, n) => {
    const st = x.done >= x.qs.length ? 'done' : (n === curIdx ? 'now' : '');
    const right = (log.res[x.s.k] || []).filter(r => r.ok).length;
    h2 += '<div class="stop ' + st + '"><i></i><b>' + x.s.n + '</b><em>'
      + (x.done >= x.qs.length ? '对 ' + right : x.done + '/' + x.qs.length) + '</em></div>';
  });
  h2 += '</div>';
  c2.innerHTML = h2;
  m.appendChild(c2);

  /* 当前站 = 唯一的行动 */
  if (curIdx >= 0) {
    const x = live[curIdx];
    const left = x.qs.length - x.done;
    const nc = el('div', 'nowcard');
    const detail = x.s.k === 'focus' ? TMAP[log.focusK].name + (log.focus2 ? ' + ' + TMAP[log.focus2].name : '')
      : x.s.k === 'track' ? log.trackCh
      : x.s.k === 'review' ? '之前做错的题，回来再考一次'
      : '先用小学题热手，再进负数';
    nc.innerHTML = '<div class="k">现在这一站</div><h2>' + x.s.full + '</h2>'
      + '<div class="sub">' + esc(detail) + '</div>'
      + '<div class="meta">' + left + ' 道 · 约 ' + Math.max(2, Math.round(left * 0.7)) + ' 分钟</div>';
    const b = el('button', 'go', x.done ? '接着做' : '开始');
    b.onclick = () => runner(x.qs.slice(x.done), {
      title: x.s.full, backTo: 'today',
      onEach: (q, ok, v) => recordAnswer(x.s.k, q, v, ok)
    });
    nc.appendChild(b);
    m.appendChild(nc);
  } else {
    m.appendChild(el('div', 'card', '<div class="eyebrow">今天的四站都过了</div><div class="sub">'
      + '明天这个时候再来。想多练可以去「重练」翻错题，或者去「收藏」看还差几张卡。</div>'));
  }

  /* 进步 */
  const gs = gains();
  const anyDone = live.some(x => x.done);
  if (gs.length) {
    const g = el('div', 'gains');
    g.innerHTML = '<div class="eyebrow">今天你变强了</div>'
      + gs.map(x => '<div class="grow"><i>' + esc(x.big) + '</i><span>' + esc(x.txt) + '</span></div>').join('');
    m.appendChild(g);
  } else if (anyDone) {
    m.appendChild(el('div', 'gains', '<div class="eyebrow">今天守住了</div>'
      + '<div class="sub">没有退步。基础题稳住不掉，本来就是这个阶段该拿到的东西。</div>'));
  }

  /* 本周挑战 */
  if (!log.mini && wi.phase === 'term') {
    const bkey = 'W' + wi.w, doneB = DB.boss[bkey];
    const bc = el('div', 'card');
    bc.innerHTML = '<div class="eyebrow">本周挑战 · ' + bkey + '</div>'
      + '<div class="sub">' + (doneB ? '这周的攻下来了，下周一有新的。' : '3 道本周内容里最难的。不算正确率，做不出来不影响任何东西。') + '</div>';
    if (!doneB) {
      const bb = el('button', 'go sec', '来一把');
      bb.onclick = () => {
        const tr = trackOf(wi.w);
        const ks = tr.ks.concat(tr.ks, tr.ks).slice(0, 3);
        runner(ks.map(k => genQ(k, 3)), {
          title: '本周挑战', backTo: 'today', fact: false,
          onDone: (res, host) => {
            DB.boss[bkey] = { date: today(), right: res.filter(Boolean).length };
            const f = pickFact(tr.ks, DB.facts);
            if (f) { DB.facts.push(f.id); host.appendChild(factCard(f, '挑战奖励 · 解锁一张卡')); }
            save();
          }
        });
      };
      bc.appendChild(bb);
    }
    m.appendChild(bc);
  }

  /* 状态不好 */
  if (!log.mini && !anyDone) {
    const mc = el('div', 'card');
    mc.innerHTML = '<div class="eyebrow">今天不太想做</div><div class="sub">换成 5 题的迷你版。'
      + '断一天比硬撑到崩掉更难补回来。</div>';
    const mb = el('button', 'go sec', '换成 5 题');
    mb.onclick = () => { buildMini(); go('today'); };
    mc.appendChild(mb);
    m.appendChild(mc);
  }
}

/* 第一次打开 */
function viewFirst(m) {
  const c = el('div', 'card');
  c.innerHTML = '<div class="eyebrow">开始之前</div>'
    + '<h2 style="font-size:24px;line-height:1.4">先摸清底子在哪，<br>再决定每天练什么</h2>'
    + '<div class="sub" style="margin-top:12px">21 道题，小学 13 个知识点加初一 3 个前置点，大约 20 分钟。'
    + '做完才知道该补哪里。中间可以停，进度存在这台设备上。</div>';
  const b = el('button', 'go', '开始 21 题');
  b.onclick = () => startDiag();
  c.appendChild(b);
  m.appendChild(c);
  m.appendChild(el('div', 'card', '<div class="eyebrow">这个 app 怎么用</div>'
    + '<div class="route" style="margin:6px 0 14px">'
    + '<div class="stop done"><i></i><b>热身</b></div><div class="stop done"><i></i><b>补漏</b></div>'
    + '<div class="stop now"><i></i><b>跟课</b></div><div class="stop"><i></i><b>重练</b></div></div>'
    + '<div class="sub">每天四站，一站一站过。做错的题会自己排到后面的日子再考你一次，'
    + '答对三轮就从错题本毕业。</div>'));
}
let DIAGQS = null;
function startDiag() {
  DIAGQS = buildDiag();
  runner(DIAGQS, {
    title: '摸底 21 题', backTo: 'today', fact: false,
    onDone: (res, host) => {
      finishDiag(DIAGQS, res); DIAGQS = null;
      host.appendChild(el('div', 'card', '<div class="eyebrow">摸完了</div>'
        + '<div class="sub">明天开始每天四站。详细结果在「家长」里，你不用管。</div>'));
    }
  });
}

/* ============================================================
   孩子视图 · 重练
   ============================================================ */
function viewRedo(m) {
  const t = today();
  const due = DB.wrong.filter(w => w.due <= t);
  if (!DB.wrong.length) {
    m.appendChild(el('div', 'empty', '<span class="mk">◌</span>错题本是空的。'));
    return;
  }
  const c = el('div', 'card');
  c.innerHTML = '<div class="eyebrow">错题本</div><h2 class="mono" style="font-size:28px">' + DB.wrong.length + ' 道</h2>'
    + '<div class="sub" style="margin-top:6px">今天该重考 ' + due.length + ' 道。答对一次隔几天再考，连对三轮就毕业。</div>';
  if (due.length) {
    const b = el('button', 'go', '重考今天到期的 ' + due.length + ' 道');
    b.onclick = () => { buildToday(); runner(due.slice(), { title: '错题重练', backTo: 'redo',
      onEach: (q, ok, v) => recordAnswer('review', q, v, ok) }); };
    c.appendChild(b);
  }
  m.appendChild(c);

  const grp = {};
  DB.wrong.forEach(w => (grp[w.topic] = grp[w.topic] || []).push(w));
  Object.keys(grp).sort((a, b) => grp[b].length - grp[a].length).forEach(k => {
    const c2 = el('div', 'card');
    let h = '<div class="eyebrow">' + esc(TMAP[k].name) + ' · ' + grp[k].length + ' 道</div>';
    grp[k].slice(0, 6).forEach(w => { h += '<div class="wq"><div class="t">' + sup(esc(w.q)) + '</div><div class="a">'
      + ans(w.ans) + ' · ' + w.due + ' 重考</div></div>'; });
    if (grp[k].length > 6) h += '<div class="sub" style="margin-top:10px">还有 ' + (grp[k].length - 6) + ' 道</div>';
    c2.innerHTML = h;
    m.appendChild(c2);
  });
}

/* ============================================================
   孩子视图 · 收藏（数学史卡片墙）
   收集感本身就是奖励，不需要积分
   ============================================================ */
let FOPEN = null;
function viewColl(m) {
  const got = FACTS.filter(f => DB.facts.indexOf(f.id) >= 0);
  const c = el('div', 'card');
  c.innerHTML = '<div class="eyebrow">数学冷知识收藏</div>'
    + '<h2 class="mono" style="font-size:30px;letter-spacing:-.03em">' + got.length + '<span style="color:var(--ink3)">/' + FACTS.length + '</span></h2>'
    + '<div class="sub" style="margin-top:6px">每天做完两站解锁一张，打赢本周挑战多得一张。'
    + '都是真事——你学的那些规则，是这些人想出来的。</div>';
  m.appendChild(c);
  if (FOPEN) {
    const f = FACTS.filter(x => x.id === FOPEN)[0];
    if (f) m.appendChild(factCard(f, '收藏卡 ' + f.id.toUpperCase()));
  }
  const wall = el('div', 'coll');
  FACTS.forEach((f, n) => {
    const has = DB.facts.indexOf(f.id) >= 0;
    const via = TMAP[f.ks[0]] ? TMAP[f.ks[0]].name : '';
    const b = el('button', 'fc' + (has ? '' : ' lock'),
      '<div class="n">' + String(n + 1).padStart(2, '0') + '</div><div class="t">'
      + (has ? esc(f.t) : '练「' + esc(via) + '」时开') + '</div>');
    if (has) b.onclick = () => { FOPEN = (FOPEN === f.id ? null : f.id); render(); };
    wall.appendChild(b);
  });
  m.appendChild(wall);
}

/* ============================================================
   家长区
   ============================================================ */
let PINBUF = '';
function viewLock(m) {
  PINBUF = '';
  const c = el('div', 'card');
  c.innerHTML = '<div class="eyebrow">家长区</div><h2>输入 4 位密码</h2>'
    + '<div class="sub" style="margin-top:6px">这里有完整的诊断结果和设置，不适合让他自己改。</div>'
    + '<div class="pin" id="pindots"><i></i><i></i><i></i><i></i></div>';
  const pad = el('div', 'pad');
  ['1','2','3','4','5','6','7','8','9','','0','删'].forEach(k => {
    if (!k) { pad.appendChild(el('div')); return; }
    const b = el('button', k === '删' ? 'fn' : '', k);
    b.onclick = () => {
      if (k === '删') PINBUF = PINBUF.slice(0, -1);
      else if (PINBUF.length < 4) PINBUF += k;
      const ds = document.querySelectorAll('#pindots i');
      ds.forEach((d, n) => d.className = n < PINBUF.length ? 'on' : '');
      if (PINBUF.length === 4) {
        if (PINBUF === DB.profile.pin) { PARENT_OK = true; go('p-plan'); }
        else { PINBUF = ''; ds.forEach(d => d.className = ''); const w = $('#pinmsg'); if (w) w.textContent = '不对，再试一次'; }
      }
    };
    pad.appendChild(b);
  });
  c.appendChild(pad);
  c.appendChild(el('div', 'sub', '<span id="pinmsg"></span>'));
  m.appendChild(c);
  const b2 = el('button', 'go sec', '忘了密码 · 回孩子视图');
  b2.onclick = () => go('today');
  m.appendChild(b2);
}

function pbanner(m, txt) { m.appendChild(el('div', 'pbanner', txt)); }

function viewPlan(m) {
  const wi = weekInfo();
  pbanner(m, '孩子那边只看得到「今天做什么」和进步，看不到下面这些分档和设置。');

  const c = el('div', 'card');
  const dMid = dayDiff(today(), addDays(DB.profile.schoolStart, 9 * 7));
  const dFin = dayDiff(today(), '2027-01-14');
  c.innerHTML = '<div class="eyebrow">当前进度</div><h2>' + esc(wi.label) + '</h2>'
    + '<div class="sub">启动日 ' + DB.profile.kickoff + '，开学 ' + DB.profile.schoolStart
    + '，每天 ' + DB.profile.dailyMin + ' 分钟</div>'
    + '<div class="miles">'
    + '<div><b>' + (dMid > 0 ? dMid : 0) + '</b><span>天到期中（约 11 月初）</span></div>'
    + '<div><b>' + (dFin > 0 ? dFin : 0) + '</b><span>天到期末（不早于 1/14）</span></div>'
    + '<div><b>' + Math.max(0, Math.ceil(dFin / 7)) + '</b><span>周还能用</span></div></div>';
  m.appendChild(c);

  const k = el('div', 'card');
  k.innerHTML = '<div class="eyebrow">8/29 – 8/31 破冰三天</div>'
    + '<div class="sub">他 29 号才从老家回深圳，开学前只有这三天。目标不是学完，是开学第一节课能听懂。</div>'
    + '<ol class="q2"><li>第 1 天：做完摸底 21 题，当晚陪他过 2 道错题</li>'
    + '<li>第 2 天：主攻摸底里最差的那个小学知识点 + 预习数轴、相反数、绝对值</li>'
    + '<li>第 3 天：昨天错题重做 + 预习有理数加减，把「减号改写成加相反数」练成条件反射</li></ol>';
  m.appendChild(k);

  const t = el('div', 'card');
  let h = '<div class="eyebrow">一学期 20 周跟课表</div>'
    + '<div class="sub">按北师大版（2024）七上章序 + 深圳市 2026–2027 校历排的。学校进度不一样就点「改」。</div>'
    + '<div style="overflow-x:auto"><table class="tb"><tr><th>周</th><th>日期</th><th>跟课内容</th><th></th></tr>';
  for (let w = 1; w <= 20; w++) {
    const tr = trackOf(w);
    const d0 = addDays(DB.profile.schoolStart, (w - 1) * 7);
    const dd = d0.slice(5).replace('-', '/') + '–' + addDays(d0, 6).slice(5).replace('-', '/');
    h += '<tr' + (w === wi.w && wi.phase === 'term' ? ' class="now"' : '') + '><td class="nw">W' + w
      + '</td><td class="nw">' + dd + '</td><td>' + esc(tr.ch)
      + (tr.mile ? '<div class="mile">' + esc(tr.mile) + '</div>' : '')
      + '</td><td><button class="pill" data-w="' + w + '">改</button></td></tr>';
  }
  h += '</table></div>';
  t.innerHTML = h;
  t.querySelectorAll('button[data-w]').forEach(b => b.onclick = () => {
    const w = +b.dataset.w, tr = trackOf(w);
    const ch = prompt('第 ' + w + ' 周学校在讲什么？', tr.ch);
    if (ch === null) return;
    const opts = M_TOPICS.map((x, n) => (n + 1) + '=' + TMAP[x].name).join('  ');
    const ps = prompt('这周练哪些知识点？填编号，逗号分隔\n' + opts, tr.ks.map(x => M_TOPICS.indexOf(x) + 1).join(','));
    if (ps === null) return;
    const ks = ps.split(/[,，\s]+/).map(x => M_TOPICS[+x - 1]).filter(Boolean);
    DB.trackOverride[w] = { ch: ch, ks: ks.length ? ks : tr.ks };
    delete DB.logs[today()]; save(); render();
  });
  m.appendChild(t);

  const g = el('div', 'card');
  g.innerHTML = '<div class="eyebrow">阶段目标</div><ol class="q2">'
    + '<li><b>开学第 4 周末</b>（9 月底）：有理数加减单测 10 题错不超过 2 题；热身正确率 ≥ 80%</li>'
    + '<li><b>国庆 10/1–10/7</b>：一天不断，每天 15 分钟也算。断一周回来就跟不上乘除</li>'
    + '<li><b>期中前</b>（第 9 周）：(−2)² 和 −2² 连对 10 题；补漏队列清掉 3 个小学知识点</li>'
    + '<li><b>第 14 周</b>（整式学完）：去括号变号 10 题对 8 道；错题本降到 30 道内</li>'
    + '<li><b>期末前</b>（1 月上旬）：含分母的一元一次方程 10 题对 7 道；错题本降到 20 道内</li>'
    + '</ol><div class="sub" style="margin-top:12px">及格线不是目标。他丢分的大头是运算规则不是难题，'
    + '把「会做的题不丢分」做到了，分数自己会上来。</div>';
  m.appendChild(g);
}

function viewDiag(m) {
  if (!DB.diag.done) {
    m.appendChild(el('div', 'empty', '<span class="mk">◌</span>还没做摸底。让他在孩子视图里点「开始 21 题」。'));
    return;
  }
  pbanner(m, '这页只在家长区。孩子看到「你要补 6 项」的清单只会更确认「我不行」。');
  const rows = Object.keys(DB.diag.scores).map(k => { const s = DB.diag.scores[k]; return { k: k, r: s.right / s.total, s: s }; }).sort((a, b) => a.r - b.r);
  const c = el('div', 'card');
  let h = '<div class="eyebrow">摸底结果 · ' + DB.diag.date + '</div><table class="tb"><tr><th>知识点</th><th>对</th><th>判断</th></tr>';
  rows.forEach(r => {
    const lv = r.s.total < 2 ? ['只测 1 题', ''] : r.r >= 0.85 ? ['稳', 'g'] : r.r >= 0.5 ? ['夹生', 'w'] : ['要补', 'b'];
    h += '<tr><td>' + esc(TMAP[r.k].name) + '<div class="sub" style="font-size:12px">'
      + (TMAP[r.k].stage === 'P' ? '小学' : '七上') + '</div></td><td class="nw">' + r.s.right + '/' + r.s.total
      + '</td><td><span class="pill ' + lv[1] + '">' + lv[0] + '</span></td></tr>';
  });
  h += '</table>';
  c.innerHTML = h;
  m.appendChild(c);

  const c2 = el('div', 'card');
  c2.innerHTML = '<div class="eyebrow">补漏队列</div>'
    + '<div class="sub">按「影响初一的程度 × 掌握度」排。近 20 题正确率到 85% 就自动毕业出队。</div>'
    + '<ol class="q2">' + DB.queue.map(k => '<li>' + esc(TMAP[k].name) + '</li>').join('') + '</ol>';
  m.appendChild(c2);

  const c3 = el('div', 'card');
  c3.innerHTML = '<div class="eyebrow">发给 Claude 调计划</div>'
    + '<div class="sub">这个页面没有后端，成绩只在这台设备上，外面读不到。复制一段摘要（不含姓名学校）粘给他，'
    + '他能判断补漏顺序要不要重排、难度合不合适。</div>';
  const b1 = el('button', 'go', '复制进度摘要'); b1.onclick = () => copyBrief(c3);
  const b2 = el('button', 'go sec', '直接看这段文字'); b2.onclick = () => showBrief(c3);
  c3.appendChild(b1); c3.appendChild(b2);
  m.appendChild(c3);

  const b = el('button', 'btn', '重做摸底（清空队列，保留错题本）');
  b.onclick = () => { if (confirm('重做摸底？')) { go('today'); startDiag(); } };
  m.appendChild(b);
}

function viewTonight(m) {
  const t = today(), log = DB.logs[t];
  const c = el('div', 'card');
  c.innerHTML = '<div class="eyebrow">今晚这 10 分钟</div><h2>挑 2 道，让他讲给你听</h2>'
    + '<div class="sub" style="margin-top:6px">你只负责问问题，不用讲。</div>';
  m.appendChild(c);

  let wt = (log && log.wrongToday) ? log.wrongToday.slice() : [];
  if (!wt.length) wt = DB.wrong.filter(w => w.addedAt === t);
  if (!wt.length) {
    m.appendChild(el('div', 'empty', '<span class="mk">◌</span>今天还没有错题记录。等他做完再来。'));
  } else {
    const cnt = {}; wt.forEach(w => cnt[w.topic] = (cnt[w.topic] || 0) + 1);
    wt.sort((a, b) => cnt[b.topic] - cnt[a.topic]);
    const seen = {}, chosen = [];
    wt.forEach(w => { if (chosen.length < 2 && !seen[w.topic]) { seen[w.topic] = 1; chosen.push(w); } });
    if (chosen.length < 2) wt.forEach(w => { if (chosen.length < 2 && chosen.indexOf(w) < 0) chosen.push(w); });
    chosen.forEach((w, n) => {
      const c2 = el('div', 'card');
      c2.innerHTML = '<div class="eyebrow">第 ' + (n + 1) + ' 道 · ' + esc(TMAP[w.topic].name) + '</div>'
        + '<div class="' + qClass(w.q) + '" style="font-size:' + (qClass(w.q) === 'q long' ? '16.5px' : '22px') + ';text-align:left">' + sup(esc(w.q)) + '</div>'
        + '<div class="sub" style="margin-top:10px">答案 <b class="mono">' + ans(w.ans) + '</b></div>'
        + '<div class="pask"><div class="k">你问这句</div>' + esc(w.ask) + '</div>'
        + '<details><summary>讲解思路（他讲不出来你再看）</summary><ol class="sol">'
        + w.sol.map(x => '<li>' + sup(esc(x)) + '</li>').join('') + '</ol></details>';
      m.appendChild(c2);
    });
  }

  const tip = el('div', 'card');
  tip.innerHTML = '<div class="eyebrow">四条底线</div><ol class="q2">'
    + '<li>不说「这么简单都不会」。他的问题是小学没打牢，不是不聪明。</li>'
    + '<li>只讲 2 道。讲多了记不住，还会把 10 分钟拖成 40 分钟然后崩。</li>'
    + '<li>让他讲、你听。他能把步骤说顺就算过关，说不出来的地方才是真漏洞。</li>'
    + '<li>表扬落在具体动作上：「你这次符号定对了」「你先算括号了」。别说「你真聪明」——'
    + '夸天赋会让他下次遇到难题就认定自己不是这块料。</li></ol>';
  m.appendChild(tip);

  const w7 = weekReport();
  m.appendChild(el('div', 'card', '<div class="eyebrow">最近 7 天</div>'
    + '<div class="sub">练了 ' + w7.days + ' 天，' + w7.total + ' 题，正确率 ' + w7.rate + '%。'
    + (w7.days < 4 ? '天数偏少——先保住每天都碰一下，比某天做很多有用。' : '节奏没问题，保持。') + '</div>'));

  const cq = el('div', 'card');
  cq.innerHTML = '<div class="eyebrow">卡住了想问 Claude</div>'
    + '<div class="sub">连续两周没进步、或者不确定该不该调计划的时候，复制这段发给他。</div>';
  const cb = el('button', 'go sec', '复制进度摘要'); cb.onclick = () => copyBrief(cq);
  cq.appendChild(cb);
  m.appendChild(cq);
}

function viewData(m) {
  const rows = [];
  for (let i = 13; i >= 0; i--) {
    const d = addDays(today(), -i), l = DB.logs[d];
    let n = 0, r = 0;
    if (l) ['warm', 'focus', 'track', 'review'].forEach(p => (l.res[p] || []).forEach(x => { n++; if (x.ok) r++; }));
    rows.push({ d: d, n: n, r: r });
  }
  const c = el('div', 'card');
  let h = '<div class="eyebrow">最近 14 天正确率</div><div class="chart">';
  rows.forEach(x => {
    const pct = x.n ? Math.round(x.r / x.n * 100) : 0;
    h += '<div class="bar" title="' + x.d + ' ' + x.r + '/' + x.n + '"><i style="height:'
      + (x.n ? Math.max(pct, 4) : 0) + '%"></i><b>' + x.d.slice(5).replace('-', '/') + '</b></div>';
  });
  h += '</div><div class="sub">没有柱子 = 那天没练。</div>';
  c.innerHTML = h;
  m.appendChild(c);

  const c2 = el('div', 'card');
  let h2 = '<div class="eyebrow">各知识点掌握度</div><table class="tb"><tr><th>知识点</th><th>题</th><th>正确率</th><th>难度</th><th></th></tr>';
  TOPICS.forEach(t => {
    const n = mstN(t.k); if (!n) return;
    const r = Math.round(mst(t.k) * 100);
    const lv = n < 8 ? ['样本少', ''] : r >= 85 ? ['稳', 'g'] : r >= 60 ? ['夹生', 'w'] : ['要补', 'b'];
    h2 += '<tr><td>' + esc(t.name) + '<div class="sub" style="font-size:12px">' + (t.stage === 'P' ? '小学' : '七上')
      + '</div></td><td class="nw">' + n + '</td><td class="nw">' + r + '%</td><td class="nw">L' + pickLv(t.k)
      + '</td><td><span class="pill ' + lv[1] + '">' + lv[0] + '</span></td></tr>';
  });
  h2 += '</table><div class="sub" style="margin-top:12px">难度档自动调：近 10 题低于 60% 降到 L1，'
    + '到 90% 且累计 ≥75%、做过 ≥15 题才升 L3。升保守降灵敏，避免把他砸崩。</div>';
  c2.innerHTML = h2;
  m.appendChild(c2);
}

function viewSet(m) {
  const c = el('div', 'card');
  c.innerHTML = '<div class="eyebrow">时间与节奏</div>'
    + '<div class="kv"><span>启动日</span><input id="s-kick" value="' + DB.profile.kickoff + '"></div>'
    + '<div class="kv"><span>开学日</span><input id="s-ss" value="' + DB.profile.schoolStart + '"></div>'
    + '<div class="kv"><span>每天分钟</span><input id="s-min" value="' + DB.profile.dailyMin + '"></div>';
  const b = el('button', 'go', '保存');
  b.onclick = () => {
    DB.profile.kickoff = $('#s-kick').value.trim();
    DB.profile.schoolStart = $('#s-ss').value.trim();
    DB.profile.dailyMin = Math.max(10, Math.min(90, +$('#s-min').value || 25));
    delete DB.logs[today()]; save(); render();
  };
  c.appendChild(b);
  m.appendChild(c);

  const cp = el('div', 'card');
  cp.innerHTML = '<div class="eyebrow">家长区密码</div>'
    + '<div class="sub">' + (DB.profile.pin ? '已设置。' : '没设置，他自己也能点进这里改分钟数或者清空记录。')
    + '</div><div class="kv"><span>4 位数字</span><input id="s-pin" value="' + (DB.profile.pin || '') + '" maxlength="4"></div>';
  const pb = el('button', 'go sec', DB.profile.pin ? '更新密码' : '设置密码');
  pb.onclick = () => {
    const v = $('#s-pin').value.trim();
    if (v && !/^\d{4}$/.test(v)) { alert('要 4 位数字'); return; }
    DB.profile.pin = v || null; PARENT_OK = true; save(); render();
  };
  cp.appendChild(pb);
  m.appendChild(cp);

  const c2 = el('div', 'card');
  c2.innerHTML = '<div class="eyebrow">进度备份</div>'
    + '<div class="sub">数据只在这台设备的浏览器里。换设备、清缓存之前先导出。</div>';
  const b0 = el('button', 'go', '复制进度摘要（给 Claude 看）'); b0.onclick = () => copyBrief(c2);
  const b1 = el('button', 'go sec', '导出进度文件');
  b1.onclick = () => {
    const blob = new Blob([JSON.stringify(DB)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = 'math-progress-' + today() + '.json';
    document.body.appendChild(a); a.click(); a.remove();
  };
  const inp = el('input'); inp.type = 'file'; inp.accept = '.json';
  inp.style.cssText = 'margin-top:14px;font-size:13px;color:var(--ink3)';
  inp.onchange = e => {
    const f = e.target.files[0]; if (!f) return;
    const r = new FileReader();
    r.onload = () => { try { const d = JSON.parse(r.result); if (!d.ver) throw new Error('格式不对'); DB = d; save(); render(); }
      catch (err) { alert('导入失败：' + err.message); } };
    r.readAsText(f);
  };
  c2.appendChild(b0); c2.appendChild(b1);
  c2.appendChild(el('div', 'sub', '导入备份：'));
  c2.appendChild(inp);
  m.appendChild(c2);

  const c3 = el('div', 'card');
  c3.innerHTML = '<div class="eyebrow">危险操作</div>';
  const b3 = el('button', 'btn danger', '清空全部数据');
  b3.onclick = () => { if (confirm('全部清空，不可恢复。确定？')) { localStorage.removeItem(KEY); load(); PARENT_OK = true; go('today'); } };
  c3.appendChild(b3);
  m.appendChild(c3);
}

/* ---------- 启动 ---------- */
load();
if (DB.profile.pin === undefined) { DB.profile.pin = null; save(); }
render();
