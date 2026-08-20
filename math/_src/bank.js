/* ============================================================
   题库引擎 —— 北师大版七年级上 + 小学基础补漏
   所有题目参数化随机生成，答案由构造保证精确
   ============================================================ */

const R = (a, b) => Math.floor(Math.random() * (b - a + 1)) + a;
const pick = a => a[R(0, a.length - 1)];
const shuf = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = R(0, i);[a[i], a[j]] = [a[j], a[i]]; } return a; };
const gcd = (a, b) => { a = Math.abs(a); b = Math.abs(b); while (b) { const t = a % b; a = b; b = t; } return a || 1; };
function frac(n, d) { if (d < 0) { n = -n; d = -d; } const g = gcd(n, d); return { n: n / g, d: d / g }; }
function fstr(f) { return f.d === 1 ? '' + f.n : f.n + '/' + f.d; }
/* 取与分母互质的分子，保证题干里的分数本身已是最简 */
function nCop(d) { const c = []; for (let i = 1; i < d; i++) if (gcd(i, d) === 1) c.push(i); return c.length ? pick(c) : 1; }
function divisors(n) { const r = []; for (let i = 1; i <= n; i++) if (n % i === 0) r.push(i); return r; }
/* 负数套括号 */
function P(x) { return x < 0 ? '(−' + (-x) + ')' : '' + x; }
/* 裸数字用数学负号，别让题干里冒出半角 -3 */
function N(x) { return x < 0 ? '−' + (-x) : '' + x; }
/* 带符号连接，如 " − 3" / " + 5" */
function S(x) { return x < 0 ? ' − ' + (-x) : ' + ' + x; }
/* 形如 3x − 5 的一次式 */
function lin(cx, cc) {
  let s = '';
  if (cx === 0) s = '' + cc;
  else {
    s = (cx === 1 ? 'x' : cx === -1 ? '−x' : (cx < 0 ? '−' + (-cx) : '' + cx) + 'x');
    if (cc !== 0) s += S(cc);
  }
  return s;
}

/* ---------- 答案解析：支持 整数 / 小数 / 分数 a/b / 混数 2 1/3 ---------- */
function parseVal(s) {
  if (s === null || s === undefined) return null;
  s = ('' + s).trim().replace(/−/g, '-').replace(/／/g, '/').replace(/\s+/g, ' ');
  if (!s) return null;
  let m = s.match(/^(-?)(\d+) (\d+)\/(\d+)$/);
  if (m) { const d = +m[4]; if (!d) return null; const v = (+m[2]) * d + (+m[3]); return frac(m[1] === '-' ? -v : v, d); }
  m = s.match(/^(-?\d+)\/(-?\d+)$/);
  if (m) { if (+m[2] === 0) return null; return frac(+m[1], +m[2]); }
  m = s.match(/^-?(\d+\.?\d*|\.\d+)$/);
  if (m) { const dec = (s.split('.')[1] || '').length; const p = Math.pow(10, dec); return frac(Math.round(parseFloat(s) * p), p); }
  return null;
}
function eqVal(a, b) { const x = parseVal(a), y = parseVal(b); if (!x || !y) return false; return x.n === y.n && x.d === y.d; }

/* ============================================================
   难度自适应：目标把正确率压在 85% 附近
   依据 Wilson et al. 2019《The Eighty Five Percent Rule for optimal
   learning》(Nat Commun 10:4646) —— 太简单和太难都学得慢，85% 最快。
   注：原研究是感知决策/机器学习任务，搬到做题上是工程近似，不是照搬结论。
   LV=1 数字小、形态最简；LV=2 常规；LV=3 数字大、形态复杂。
   ============================================================ */
let LV = 2;
function setLv(v) { LV = (v === 1 || v === 3) ? v : 2; }
/* 按难度缩放上限 */
function lvR(a, b) { const k = LV === 1 ? 0.55 : LV === 3 ? 1.5 : 1; return R(a, Math.max(a + 1, Math.round(b * k))); }
/* 按难度选形态数：LV1 只用前 1 种，LV2 前 n-1 种，LV3 全部 */
function lvT(n) { if (LV === 1) return 1; if (LV === 3) return R(1, n); return R(1, Math.max(1, n - 1)); }

/* 生活化情境词池：把「甲乙两人」「某商品」换成他的世界 */
const NM = ['小宇', '阿哲', '表哥', '同桌', '小凯'];
const PL = ['地铁站', '篮球场', '图书馆', '学校', '小区门口'];
const IT = ['一杯奶茶', '一双球鞋', '一本漫画', '一个篮球', '一包薯片', '一副耳机', '一个键盘', '一个水杯'];
const nm2 = () => { const a = pick(NM); return [a, pick(NM.filter(x => x !== a))]; };

/* ============================================================
   TOPICS：每个知识点一个生成器
   stage  : 'P' 小学基础 / 'M' 七上新课
   pri    : 补漏优先级，越小越先补（影响初一的程度）
   ask    : 家长陪学时该问孩子什么
   ============================================================ */
const TOPICS = [

/* ---------------- 小学基础 ---------------- */
{
  k: 'calc-order', name: '四则混合运算顺序', stage: 'P', pri: 3,
  ask: '让他先用手指点一遍：这道题先算哪一步？说出顺序再动笔。',
  gen() {
    const t = lvT(3);
    if (t === 1) {
      const a = R(2, LV === 1 ? 6 : 9), b = R(2, LV === 1 ? 6 : 9), c = lvR(11, 40), d = pick([2, 3, 4, 5, 6]), N = d * R(2, 9);
      const ans = c + a * b - N / d;
      return { q: `${c} + ${a} × ${b} − ${N} ÷ ${d} = ?`, ans: '' + ans, type: 'num',
        sol: [`先乘除后加减：${a}×${b}=${a * b}，${N}÷${d}=${N / d}`, `再从左到右算加减：${c}+${a * b}−${N / d} = ${ans}`] };
    }
    if (t === 2) {
      const a = R(3, 12), b = R(2, 9), c = R(2, 6), d = R(2, 9);
      const ans = (a + b) * c - d;
      return { q: `(${a} + ${b}) × ${c} − ${d} = ?`, ans: '' + ans, type: 'num',
        sol: [`有括号先算括号：${a}+${b}=${a + b}`, `${a + b}×${c}=${(a + b) * c}`, `再减：${(a + b) * c}−${d} = ${ans}`] };
    }
    const a = R(3, 12), b = R(2, 9), c = R(2, 9);
    return { q: `用简便方法计算：${a} × ${b} + ${a} × ${c} = ?`, ans: '' + a * (b + c), type: 'num',
      sol: [`两项都有 ${a}，提出来（乘法分配律）：${a}×(${b}+${c})`, `= ${a}×${b + c} = ${a * (b + c)}`] };
  }
},
{
  k: 'frac-add', name: '分数加减（通分）', stage: 'P', pri: 1,
  ask: '问他公分母是怎么找出来的，最后有没有约到最简。',
  gen() {
    const ds = LV === 1 ? [2, 3, 4, 6] : LV === 3 ? [2, 3, 4, 5, 6, 7, 8, 9, 10, 12] : [2, 3, 4, 5, 6, 8, 9, 10, 12];
    const d1 = pick(ds), d2 = pick(ds.filter(x => x !== d1));
    const n1 = nCop(d1), n2 = nCop(d2);
    const plus = Math.random() < 0.5;
    const L = d1 * d2 / gcd(d1, d2);
    const a = n1 * L / d1, b = n2 * L / d2;
    const f = frac(plus ? a + b : a - b, L);
    return { q: `${n1}/${d1} ${plus ? '+' : '−'} ${n2}/${d2} = ?`, ans: fstr(f), type: 'frac',
      sol: [`公分母取 ${L}`, `${n1}/${d1} = ${a}/${L}，${n2}/${d2} = ${b}/${L}`,
            `${a}/${L} ${plus ? '+' : '−'} ${b}/${L} = ${plus ? a + b : a - b}/${L} = ${fstr(f)}`] };
  }
},
{
  k: 'frac-muldiv', name: '分数乘除', stage: 'P', pri: 1,
  ask: '除法那步他有没有翻成乘倒数？让他指出哪个数被翻过来了。',
  gen() {
    const dp = LV === 1 ? [2, 3, 4, 5] : [2, 3, 4, 5, 6, 7, 8, 9, 10];
    const b = pick(dp), d = pick(dp);
    const a = nCop(b), c = nCop(d);
    const mul = Math.random() < 0.5;
    const f = mul ? frac(a * c, b * d) : frac(a * d, b * c);
    return { q: `${a}/${b} ${mul ? '×' : '÷'} ${c}/${d} = ?`, ans: fstr(f), type: 'frac',
      sol: mul ? [`分子乘分子，分母乘分母：${a * c}/${b * d}`, `约简 = ${fstr(f)}`]
               : [`除以一个分数 = 乘它的倒数：${a}/${b} × ${d}/${c}`, `= ${a * d}/${b * c} = ${fstr(f)}`] };
  }
},
{
  k: 'decimal', name: '小数运算与分数互化', stage: 'P', pri: 1,
  ask: '小数点位数他是数出来的还是猜的？让他数一遍。',
  gen() {
    const t = R(1, 3);
    if (t === 1) {
      const x = R(11, 99) / 10, y = R(2, 9);
      const ans = Math.round(x * y * 10) / 10;
      return { q: `${x} × ${y} = ?`, ans: '' + ans, type: 'num',
        sol: [`先当整数算：${x * 10} × ${y} = ${x * 10 * y}`, `原来一共 1 位小数，结果点上 1 位：${ans}`] };
    }
    if (t === 2) {
      const p = pick([[0.25, '1/4'], [0.75, '3/4'], [0.2, '1/5'], [0.6, '3/5'], [0.125, '1/8'], [0.35, '7/20'], [0.08, '2/25'], [0.45, '9/20']]);
      return { q: `把 ${p[0]} 化成最简分数 = ?`, ans: p[1], type: 'frac',
        sol: [`几位小数就以几个 0 的数作分母：${p[0]} 有 ${('' + p[0]).split('.')[1].length} 位小数，分母是 ${Math.pow(10, ('' + p[0]).split('.')[1].length)}`,
              `${('' + p[0]).split('.')[1]}/${Math.pow(10, ('' + p[0]).split('.')[1].length)} 约到最简 = ${p[1]}`] };
    }
    const q0 = R(2, 9), dv = R(11, 49) / 10;
    const dd = Math.round(dv * q0 * 10) / 10;
    return { q: `${dd} ÷ ${dv} = ?`, ans: '' + q0, type: 'num',
      sol: [`除数变整数：两边同时乘 10 → ${dd * 10} ÷ ${dv * 10}`, `= ${q0}`] };
  }
},
{
  k: 'simple-eq', name: '简易方程（小学）', stage: 'P', pri: 2,
  ask: '让他把答案代回原式验算一遍，这个习惯比做对更重要。',
  gen() {
    const t = R(1, 3), x = R(2, 12);
    if (t === 1) { const m = R(2, 9), n = R(1, 20); return { q: `解方程：${m}x + ${n} = ${m * x + n}，x = ?`, ans: '' + x, type: 'num',
      sol: [`两边减 ${n}：${m}x = ${m * x}`, `两边除 ${m}：x = ${x}`] }; }
    if (t === 2) { const m = R(2, 9), n = R(1, 12); return { q: `解方程：${m}(x + ${n}) = ${m * (x + n)}，x = ?`, ans: '' + x, type: 'num',
      sol: [`两边除 ${m}：x + ${n} = ${x + n}`, `x = ${x}`] }; }
    const m = R(2, 9), n = R(1, 12), q0 = R(2, 9), x2 = m * q0 + n;
    return { q: `解方程：(x − ${n}) ÷ ${m} = ${q0}，x = ?`, ans: '' + x2, type: 'num',
      sol: [`两边乘 ${m}：x − ${n} = ${m * q0}`, `x = ${m * q0} + ${n} = ${x2}`] };
  }
},
{
  k: 'percent', name: '百分数与折扣', stage: 'P', pri: 5,
  ask: '问清楚「谁是 1」——百分数题错一半都是把基准搞错。',
  gen() {
    const t = R(1, 3);
    if (t === 1) { const p = R(5, 40) * 10, d = pick([5, 6, 7, 8, 9]);
      return { q: `${pick(IT)}原价 ${p} 元，打 ${d} 折，现在多少钱？`, ans: '' + p * d / 10, type: 'num',
        sol: [`打 ${d} 折 = 按原价的 ${d * 10}% 卖`, `${p} × ${d * 10}% = ${p * d / 10} 元`] }; }
    if (t === 2) { const a = R(2, 40) * 10, p = pick([10, 20, 25, 50]);
      return { q: `某数是 ${a}，增加 ${p}% 后是多少？`, ans: '' + a * (1 + p / 100), type: 'num',
        sol: [`增加后 = 原来的 ${100 + p}%`, `${a} × ${100 + p}% = ${a * (1 + p / 100)}`] }; }
    const b = R(2, 20) * 5, k = pick([2, 4, 5, 10]);
    return { q: `${b} 是 ${b * k} 的百分之几？（只填数字）`, ans: '' + 100 / k, type: 'num',
      sol: [`${b} ÷ ${b * k} = ${fstr(frac(1, k))}`, `化成百分数 = ${100 / k}%`] };
  }
},
{
  k: 'ratio', name: '比与比例', stage: 'P', pri: 5,
  ask: '让他写出「内项之积等于外项之积」，再动笔。',
  gen() {
    const t = R(1, 2);
    if (t === 1) { const a = R(2, 9), b = R(2, 9), k = R(2, 6);
      return { q: `解比例：${a} : ${b} = ${a * k} : x，x = ?`, ans: '' + b * k, type: 'num',
        sol: [`交叉相乘：${a}x = ${b} × ${a * k} = ${b * a * k}`, `x = ${b * k}`] }; }
    const tot = R(3, 12) * 7, r1 = R(2, 5), r2 = R(2, 5);
    const T = (r1 + r2) * R(3, 10);
    return { q: `把 ${T} 按 ${r1} : ${r2} 分成两份，较大的一份是多少？`, ans: '' + T / (r1 + r2) * Math.max(r1, r2), type: 'num',
      sol: [`一共 ${r1 + r2} 份，每份 ${T} ÷ ${r1 + r2} = ${T / (r1 + r2)}`, `较大的占 ${Math.max(r1, r2)} 份 = ${T / (r1 + r2) * Math.max(r1, r2)}`] };
  }
},
{
  k: 'unit', name: '单位换算', stage: 'P', pri: 6,
  ask: '问他是乘还是除——大单位换小单位一定变大。',
  gen() {
    const c = pick([
      () => { const a = R(2, 9) + R(1, 9) / 10; return [`${a} 千米 = ? 米`, '' + Math.round(a * 1000), `1 千米 = 1000 米，${a} × 1000 = ${Math.round(a * 1000)}`]; },
      () => { const a = R(2, 20); return [`${a} 平方米 = ? 平方分米`, '' + a * 100, `1 平方米 = 100 平方分米（面积单位进率是 100）`]; },
      () => { const a = R(2, 9); return [`${a} 立方米 = ? 升`, '' + a * 1000, `1 立方米 = 1000 升`]; },
      () => { const a = R(1, 11) * 5; return [`${a} 分钟 = ? 小时（用分数表示）`, fstr(frac(a, 60)), `${a} ÷ 60 = ${fstr(frac(a, 60))} 小时`]; },
      () => { const a = R(1, 9), b = R(1, 9) * 50; return [`${a} 吨 ${b} 千克 = ? 千克`, '' + (a * 1000 + b), `${a} 吨 = ${a * 1000} 千克，再加 ${b}`]; },
      () => { const a = R(2, 20); return [`${a} 平方分米 = ? 平方厘米`, '' + a * 100, `进率 100`]; }
    ])();
    return { q: c[0], ans: c[1], type: 'frac', sol: [c[2]] };
  }
},
{
  k: 'area', name: '平面图形面积', stage: 'P', pri: 6,
  ask: '让他先把公式写在旁边，再往里代数。',
  gen() {
    const t = R(1, 4);
    if (t === 1) { const a = R(4, 20), h = R(3, 16);
      return { q: `一个三角形的底是 ${a} cm，高是 ${h} cm，面积是多少平方厘米？`, ans: fstr(frac(a * h, 2)), type: 'frac',
        sol: [`三角形面积 = 底 × 高 ÷ 2`, `${a} × ${h} ÷ 2 = ${fstr(frac(a * h, 2))}`] }; }
    if (t === 2) { const a = R(3, 14), b = R(3, 14), h = R(2, 12);
      return { q: `梯形上底 ${a} cm，下底 ${b} cm，高 ${h} cm，面积是多少平方厘米？`, ans: fstr(frac((a + b) * h, 2)), type: 'frac',
        sol: [`梯形面积 = (上底 + 下底) × 高 ÷ 2`, `(${a}+${b}) × ${h} ÷ 2 = ${fstr(frac((a + b) * h, 2))}`] }; }
    if (t === 3) { const a = R(4, 20), h = R(3, 15);
      return { q: `平行四边形的底是 ${a} cm，高是 ${h} cm，面积是多少平方厘米？`, ans: '' + a * h, type: 'num',
        sol: [`平行四边形面积 = 底 × 高 = ${a * h}`] }; }
    const r = R(2, 10);
    return { q: `一个圆的半径是 ${r} cm，面积是多少平方厘米？（π 取 3.14）`, ans: '' + Math.round(3.14 * r * r * 100) / 100, type: 'num',
      sol: [`圆面积 = πr²`, `3.14 × ${r}² = 3.14 × ${r * r} = ${Math.round(3.14 * r * r * 100) / 100}`] };
  }
},
{
  k: 'volume', name: '立体图形体积与表面积', stage: 'P', pri: 6,
  ask: '让他说清算的是「装多少」还是「包多少」。',
  gen() {
    const t = R(1, 3);
    if (t === 1) { const a = R(2, 12), b = R(2, 12), c = R(2, 12);
      return { q: `长方体长 ${a} cm、宽 ${b} cm、高 ${c} cm，体积是多少立方厘米？`, ans: '' + a * b * c, type: 'num',
        sol: [`体积 = 长 × 宽 × 高 = ${a}×${b}×${c} = ${a * b * c}`] }; }
    if (t === 2) { const a = R(2, 12);
      return { q: `正方体的棱长是 ${a} cm，表面积是多少平方厘米？`, ans: '' + 6 * a * a, type: 'num',
        sol: [`6 个面都一样：6 × ${a}² = 6 × ${a * a} = ${6 * a * a}`] }; }
    const a = R(2, 10), b = R(2, 10), c = R(2, 10);
    return { q: `长方体长 ${a} cm、宽 ${b} cm、高 ${c} cm，表面积是多少平方厘米？`, ans: '' + 2 * (a * b + a * c + b * c), type: 'num',
      sol: [`表面积 = 2(长宽 + 长高 + 宽高)`, `= 2 × (${a * b}+${a * c}+${b * c}) = ${2 * (a * b + a * c + b * c)}`] };
  }
},
{
  k: 'word-speed', name: '行程问题', stage: 'P', pri: 4,
  ask: '让他画一条线段图标出两个人的位置，别直接套公式。',
  gen() {
    const t = R(1, 3);
    if (t === 1) { const va = R(3, 9), vb = R(3, 9), h = R(2, 6);
      const N = nm2(), P0 = pick(PL);
      return { q: `${N[0]}家和${N[1]}家相距 ${(va + vb) * h} 千米。两人约好在中间碰头一起去${P0}，${N[0]}每小时走 ${va} 千米，${N[1]}每小时走 ${vb} 千米，同时出发相向而行，几小时碰上？`, ans: '' + h, type: 'num',
        sol: [`两人每小时一共走近 ${va}+${vb} = ${va + vb} 千米`, `${(va + vb) * h} ÷ ${va + vb} = ${h} 小时`] }; }
    if (t === 2) { const v = R(4, 15), t2 = R(2, 8);
      return { q: `一辆车每小时行 ${v} 千米，从深圳出发开了 ${t2} 小时，一共开了多少千米？`, ans: '' + v * t2, type: 'num',
        sol: [`路程 = 速度 × 时间 = ${v} × ${t2} = ${v * t2}`] }; }
    const va = R(3, 8), t0 = pick([1, 2, 3]);
    const diff = pick(divisors(va * t0).filter(d => d >= 2 && d <= 8)) || 2;
    const vb = va + diff;
    const N2 = nm2();
    return { q: `${N2[0]}以每小时 ${va} 千米先走了 ${t0} 小时，${N2[1]}发现有东西要给他，以每小时 ${vb} 千米从同一地点去追，${N2[1]}几小时追上${N2[0]}？`, ans: '' + (va * t0 / diff), type: 'num',
      sol: [`甲先走了 ${va * t0} 千米`, `乙每小时追近 ${vb}−${va} = ${diff} 千米`, `${va * t0} ÷ ${diff} = ${va * t0 / diff} 小时`] };
  }
},
{
  k: 'word-work', name: '工程问题', stage: 'P', pri: 4,
  ask: '问他「1」代表什么——是整件工作量。',
  gen() {
    const a = R(3, 12), b = R(3, 12);
    if (a === b) return this.gen();
    const f = frac(a * b, a + b);
    const N3 = nm2();
    return { q: `一份大扫除任务，${N3[0]}单独做要 ${a} 天，${N3[1]}单独做要 ${b} 天。两人一起做，几天做完？（可填分数）`, ans: fstr(f), type: 'frac',
      sol: [`把整件工作看作 1，甲每天做 1/${a}，乙每天做 1/${b}`, `合作每天做 1/${a} + 1/${b} = ${fstr(frac(a + b, a * b))}`, `1 ÷ ${fstr(frac(a + b, a * b))} = ${fstr(f)} 天`] };
  }
},
{
  k: 'word-sumdiff', name: '和差倍问题', stage: 'P', pri: 4,
  ask: '让他指出「1 倍量」是谁，用它当未知数。',
  gen() {
    const small = R(5, 30), k = R(2, 4), m = R(1, 9);
    const big = k * small + m;
    const I0 = pick(IT);
    return { q: `两个人一共收集了 ${small + big} 张${pick(['球星卡', '游戏卡', '贴纸'])}，多的那个人比少的那个人的 ${k} 倍还多 ${m} 张。少的那个人有多少张？`, ans: '' + small, type: 'num',
      sol: [`设小数为 x，大数是 ${k}x + ${m}`, `x + ${k}x + ${m} = ${small + big}`, `${k + 1}x = ${small + big - m}，x = ${small}`] };
  }
},

/* ---------------- 七上新课 ---------------- */
{
  k: 'numline', name: '相反数·倒数·绝对值·数轴', stage: 'M', pri: 1,
  ask: '相反数和倒数他会不会混？让他各举一个例子。',
  gen() {
    const t = R(1, 4);
    if (t === 1) { const a = R(2, 20) * pick([1, -1]);
      return { q: `${N(a)} 的相反数是 ?`, ans: '' + (-a), type: 'num', sol: [`只改符号不改大小：${N(-a)}`] }; }
    if (t === 2) { const d = R(2, 11), n = nCop(d), s = pick([1, -1]);
      return { q: `${s < 0 ? '−' : ''}${n}/${d} 的倒数是 ?`, ans: fstr(frac(s * d, n)), type: 'frac',
        sol: [`分子分母对调，符号不变：${fstr(frac(s * d, n))}`] }; }
    if (t === 3) { const a = R(2, 30) * pick([1, -1]);
      return { q: `|${a < 0 ? '−' + (-a) : a}| = ?`, ans: '' + Math.abs(a), type: 'num', sol: [`绝对值是到原点的距离，永远非负：${Math.abs(a)}`] }; }
    const a = R(-9, 9), b = R(-9, 9);
    if (a === b) return this.gen();
    return { q: `数轴上表示 ${P(a)} 和 ${P(b)} 的两点，相距多少个单位长度？`, ans: '' + Math.abs(a - b), type: 'num',
      sol: [`距离 = |${a} − ${b}| = ${Math.abs(a - b)}`] };
  }
},
{
  k: 'rat-addsub', name: '有理数加减', stage: 'M', pri: 1,
  ask: '让他把每一个减号都改写成「加相反数」再算，这一步不能省。',
  gen() {
    const M = LV === 1 ? 9 : LV === 3 ? 30 : 15;
    const a = R(-M, M) || 3, b = R(-M, M) || -4, c = R(-M, M) || 5;
    const ans = a + b - c;
    return { q: `${P(a)} + ${P(b)} − ${P(c)} = ?`, ans: '' + ans, type: 'num',
      sol: [`减 ${P(c)} 就是加它的相反数 ${P(-c)}`, `${P(a)} + ${P(b)} + ${P(-c)}`, `= ${a + b} + ${P(-c)} = ${ans}`] };
  }
},
{
  k: 'rat-muldiv', name: '有理数乘除', stage: 'M', pri: 1,
  ask: '先定符号还是先算数？让他先数负号的个数。',
  gen() {
    const a = lvR(2, 9) * pick([1, -1]), c = R(2, LV === 1 ? 4 : 6) * pick([1, -1]), k = R(2, LV === 1 ? 3 : 5);
    const b = Math.abs(c) * k * pick([1, -1]);
    const ans = a * b / c;
    const negs = [a, b, c].filter(x => x < 0).length;
    return { q: `${P(a)} × ${P(b)} ÷ ${P(c)} = ?`, ans: '' + ans, type: 'num',
      sol: [`先看符号：有 ${negs} 个负号，${negs % 2 === 0 ? '偶数个 → 结果为正' : '奇数个 → 结果为负'}`,
            `再算绝对值：${Math.abs(a)} × ${Math.abs(b)} ÷ ${Math.abs(c)} = ${Math.abs(ans)}`, `所以 = ${ans}`] };
  }
},
{
  k: 'abs-calc', name: '绝对值化简计算', stage: 'M', pri: 2,
  ask: '绝对值符号里的式子先算完再脱符号，问他有没有抢步。',
  gen() {
    const a = R(-15, -2), b = R(1, 9), c = R(1, 9), d = R(2, 15);
    const ans = Math.abs(a) + Math.abs(b - c) - d;
    return { q: `|−${-a}| + |${b} − ${c}| − |−${d}| = ?`, ans: '' + ans, type: 'num',
      sol: [`先把每个绝对值里面算出来：|${b}−${c}| = |${b - c}| = ${Math.abs(b - c)}`,
            `${-a} + ${Math.abs(b - c)} − ${d} = ${ans}`] };
  }
},
{
  k: 'power', name: '有理数乘方（括号陷阱）', stage: 'M', pri: 1,
  ask: '这是初一最大的坑：让他读出来——是「负数的平方」还是「平方的相反数」。',
  gen() {
    const b = R(2, LV === 1 ? 4 : 6), form = LV === 1 ? R(1, 2) : R(1, 4);
    if (form === 1) return { q: `(−${b})² = ?`, ans: '' + b * b, type: 'num',
      sol: [`底数是 −${b}，(−${b})² = (−${b})×(−${b}) = ${b * b}`, `负负得正`] };
    if (form === 2) return { q: `−${b}² = ?`, ans: '' + (-b * b), type: 'num',
      sol: [`底数只是 ${b}，负号在外面`, `−${b}² = −(${b}×${b}) = ${-b * b}`] };
    if (form === 3) return { q: `(−${b})³ = ?`, ans: '' + (-b * b * b), type: 'num',
      sol: [`三个负数相乘，奇数个负号 → 结果为负`, `= ${-b * b * b}`] };
    return { q: `−(−${b})² = ?`, ans: '' + (-b * b), type: 'num',
      sol: [`先算 (−${b})² = ${b * b}`, `外面还有一个负号：${-b * b}`] };
  }
},
{
  k: 'rat-mixed', name: '有理数混合运算', stage: 'M', pri: 2,
  ask: '让他把整道题分成几「块」，先标出每块的结果再合并。',
  gen() {
    const t = lvT(2);
    if (t === 1) {
      const a = R(2, LV === 1 ? 3 : 5), b = R(2, 4), d = R(1, 9);
      const ans = -a * a - b * b + d;
      return { q: `−${a}² + (−${b})³ ÷ ${b} − (−${d}) = ?`, ans: '' + ans, type: 'num',
        sol: [`−${a}² = ${-a * a}（负号在外）`, `(−${b})³ = ${-b * b * b}，÷ ${b} = ${-b * b}`,
              `− (−${d}) = + ${d}`, `${-a * a} + ${P(-b * b)} + ${d} = ${ans}`] };
    }
    const a = R(2, 5), b = R(2, 9), c0 = R(2, 6), k = R(2, 5), c = c0 * k;
    const real = a * a * b + c / c0;
    return { q: `(−${a})² × ${b} + ${c} ÷ ${c0} = ?`, ans: '' + real, type: 'num',
      sol: [`(−${a})² = ${a * a}`, `${a * a} × ${b} = ${a * a * b}`, `${c} ÷ ${c0} = ${c / c0}`, `合并 = ${real}`] };
  }
},
/* ---- 以下 4 个知识点来自初一实测易错清单，不是凭空补的 ----
   性质符号与运算符号混淆（-3-5×(-2) 算成 -13）
   括号内是算式时的去括号（(2-3)-(-4+5) 算成 8）
   负分数加减（小学分数运算全是正数，负号一进来就崩）
   分数/负数作底数的乘方（底数圈不对）                        */
{
  k: 'sign-mix', name: '性质符号 vs 运算符号', stage: 'M', pri: 1,
  ask: '让他把中间那个「−」和数字自带的负号分开念一遍：哪个是运算，哪个是这个数本身的符号？',
  gen() {
    const t = lvT(3);
    if (t === 1) {
      const a = lvR(2, 15), b = R(2, LV === 1 ? 6 : 9), c = -R(2, LV === 1 ? 6 : 9);
      return { q: `${a} − ${b} × ${P(c)} = ?`, ans: '' + (a - b * c), type: 'num',
        sol: [`中间的「−」是减法运算，${P(c)} 的负号是这个数自带的，两个不能合成一个`,
              `先算乘法：${b} × ${P(c)} = ${b * c}`,
              `再减：${a} − ${P(b * c)} = ${a} + ${-b * c} = ${a - b * c}`] };
    }
    if (t === 2) {
      const a = R(2, 15), c0 = R(2, 6), k = R(2, 5), b = -c0 * k;
      return { q: `${a} + ${P(b)} ÷ ${c0} = ?`, ans: '' + (a + b / c0), type: 'num',
        sol: [`先算除法：${P(b)} ÷ ${c0} = ${b / c0}`,
              `再算加法：${a} + ${P(b / c0)} = ${a + b / c0}`] };
    }
    const a = -R(2, 12), b = R(2, 9), c = -R(2, 9);
    return { q: `${P(a)} − ${b} × ${P(c)} = ?`, ans: '' + (a - b * c), type: 'num',
      sol: [`三个符号各管各的：开头的负号属于 ${-a}，中间是减法，最后括号里的负号属于 ${-c}`,
            `${b} × ${P(c)} = ${b * c}`,
            `${a} − ${P(b * c)} = ${a} + ${-b * c} = ${a - b * c}`] };
  }
},
{
  k: 'paren-nest', name: '括号里是算式的去括号', stage: 'M', pri: 1,
  ask: '让他用手指点着括号里每一项念「这项变号、这项也变号」，一项都不能漏。',
  gen() {
    const t = lvT(2);
    if (t === 1) {
      const a = lvR(2, 12), b = lvR(2, 12), c = R(2, 9), d = R(2, 9);
      const ans = (a - b) - (-c + d);
      return { q: `(${a} − ${b}) − (−${c} + ${d}) = ?`, ans: '' + ans, type: 'num',
        sol: [`第一个括号先算出来：${a} − ${b} = ${a - b}`,
              `第二个括号前面是「−」，里面两项都要变号：−(−${c} + ${d}) = +${c} − ${d}`,
              `${a - b} + ${c} − ${d} = ${ans}`] };
    }
    const a = R(5, 20), b = R(2, 12), c = R(2, 9), d = R(2, 9);
    const ans = a - (b - (c - d));
    return { q: `${a} − [${b} − (${c} − ${d})] = ?`, ans: '' + ans, type: 'num',
      sol: [`从最里面的小括号开始：${c} − ${d} = ${c - d}`,
            `中括号里：${b} − ${P(c - d)} = ${b - (c - d)}`,
            `${a} − ${P(b - (c - d))} = ${ans}`] };
  }
},
{
  k: 'neg-frac', name: '负分数加减', stage: 'M', pri: 1,
  ask: '通分那一步和小学一模一样，问他新增的难点只有一个：负号。别让他重新学通分。',
  gen() {
    const t = lvT(2);
    const ds = LV === 1 ? [2, 3, 4, 6] : [2, 3, 4, 5, 6, 8, 10, 12];
    if (t === 1) {
      const d1 = pick(ds), d2 = pick(ds.filter(x => x !== d1));
      const n1 = nCop(d1), n2 = nCop(d2);
      const s1 = pick([1, -1]), s2 = pick([1, -1]);
      const L = d1 * d2 / gcd(d1, d2);
      const A = s1 * n1 * L / d1, B = s2 * n2 * L / d2;
      const f = frac(A + B, L);
      const t1 = (s1 < 0 ? '−' : '') + n1 + '/' + d1;
      const t2 = s2 < 0 ? '(−' + n2 + '/' + d2 + ')' : n2 + '/' + d2;
      return { q: `${t1} + ${t2} = ?`, ans: fstr(f), type: 'frac',
        sol: [`通分，公分母 ${L}：${t1} = ${A}/${L}，${(s2 < 0 ? '−' : '') + n2 + '/' + d2} = ${B}/${L}`,
              `分母相同，分子直接加：${A} + ${P(B)} = ${A + B}`,
              `${A + B}/${L} 约简 = ${fstr(f)}`] };
    }
    const w = R(1, 3), d1 = pick([2, 3, 4, 5, 6]), n1 = nCop(d1);
    const d2 = pick([2, 3, 4, 6].filter(x => x !== d1)), n2 = nCop(d2);
    const A = frac(-(w * d1 + n1), d1), B = frac(n2, d2);
    const f = frac(A.n * B.d + B.n * A.d, A.d * B.d);
    return { q: `−${w} ${n1}/${d1} + ${n2}/${d2} = ?`, ans: fstr(f), type: 'frac',
      sol: [`带分数先化成假分数：−${w} ${n1}/${d1} = ${fstr(A)}`,
            `再通分相加：${fstr(A)} + ${n2}/${d2}`,
            `= ${fstr(f)}`] };
  }
},
{
  k: 'power-frac', name: '分数作底数的乘方', stage: 'M', pri: 2,
  ask: '让他用手指圈出底数是哪一部分——括号在不在，答案完全不同。',
  gen() {
    const d = R(2, 6), n = nCop(d), e = pick([2, 3]);
    const sup = e === 2 ? '²' : '³';
    if (Math.random() < 0.5) {
      const v = frac(Math.pow(n, e) * (e % 2 ? -1 : 1), Math.pow(d, e));
      return { q: `(−${n}/${d})${sup} = ?`, ans: fstr(v), type: 'frac',
        sol: [`括号里整个 −${n}/${d} 是底数，分子分母都要乘方`,
              `${e} 个负数相乘，${e % 2 ? '奇数个 → 结果为负' : '偶数个 → 结果为正'}`,
              `= ${fstr(v)}`] };
    }
    const v = frac(-Math.pow(n, e), Math.pow(d, e));
    return { q: `−(${n}/${d})${sup} = ?`, ans: fstr(v), type: 'frac',
      sol: [`底数只是 ${n}/${d}，负号在括号外面，等乘方算完再取相反数`,
            `(${n}/${d})${sup} = ${fstr(frac(Math.pow(n, e), Math.pow(d, e)))}`,
            `前面还有负号 = ${fstr(v)}`] };
  }
},
{
  k: 'sci', name: '科学记数法', stage: 'M', pri: 4,
  ask: '让他数整数位数，n 就是位数减 1。',
  gen() {
    const m = R(11, 99) / 10, k = R(4, 9);
    const val = Math.round(m * Math.pow(10, k));
    return { q: `把 ${val} 写成 a × 10ⁿ（1 ≤ a < 10）的形式，n = ?`, ans: '' + k, type: 'num',
      sol: [`${val} 一共 ${k + 1} 位数`, `n = 位数 − 1 = ${k}（此时 a = ${m}）`] };
  }
},
{
  k: 'monomial', name: '单项式的系数与次数', stage: 'M', pri: 3,
  ask: '系数带不带负号？次数要不要把所有字母的指数加起来？',
  gen() {
    const t = R(1, 3);
    if (t === 1) { const c = R(2, 9) * pick([1, -1]), e1 = R(1, 4), e2 = R(1, 3);
      return { q: `单项式 ${c < 0 ? '−' + (-c) : c}a${e1 > 1 ? '^' + e1 : ''}b${e2 > 1 ? '^' + e2 : ''} 的系数是 ?`, ans: '' + c, type: 'num',
        sol: [`系数就是前面的数字，包含符号：${c}`] }; }
    if (t === 2) { const e1 = R(1, 4), e2 = R(1, 3), e3 = R(1, 2);
      return { q: `单项式 −5x^${e1}y^${e2}z^${e3} 的次数是 ?`, ans: '' + (e1 + e2 + e3), type: 'num',
        sol: [`次数 = 所有字母指数之和 = ${e1} + ${e2} + ${e3} = ${e1 + e2 + e3}`] }; }
    const d = R(2, 7), n = nCop(d);
    return { q: `单项式 −(${n}/${d})xy² 的系数是 ?（填分数）`, ans: fstr(frac(-n, d)), type: 'frac',
      sol: [`系数连符号一起看：${fstr(frac(-n, d))}`] };
  }
},
{
  k: 'like-terms', name: '合并同类项', stage: 'M', pri: 2,
  ask: '让他先用两种记号圈出两类项，再合并。字母部分完全一样才是同类项。',
  gen() {
    const a = R(2, 7), b = R(2, 7), c = R(2, 7), d = R(2, 7);
    const A = a + c, B = -(b + d);
    const tail = m => (m < 0 ? '− ' + (-m) : '+ ' + m) + 'xy²';
    const right = `${A}x²y ${tail(B)}`;
    const cand = [right, `${a - c}x²y ${tail(B)}`, `${A}x²y ${tail(-B)}`, `${A + B}x³y³`, `${a * c}x²y ${tail(B)}`];
    const opts = [];
    for (const o of cand) { if (opts.length < 4 && !opts.includes(o)) opts.push(o); }
    if (!opts.includes(right)) return null;
    return { q: `合并同类项：${a}x²y − ${b}xy² + ${c}x²y − ${d}xy² = ?`, type: 'choice', opts, ans: right,
      sol: [`x²y 一类：${a} + ${c} = ${A}`, `xy² 一类：−${b} − ${d} = ${B}`, `结果 ${right}（x²y 和 xy² 不是同类项，不能再合并）`] };
  }
},
{
  k: 'remove-paren', name: '去括号与化简', stage: 'M', pri: 2,
  ask: '括号前是负号时，里面每一项都要变号。让他逐项指一遍。',
  gen() {
    const m = R(2, 6); let n = R(2, 6); if (n === m) n = m === 6 ? 2 : m + 1;
    const a = R(1, 6), b = R(1, 6);
    const cx = m - n, cc = m * a + n * b;
    const right = lin(cx, cc);
    const cand = [right, lin(cx, m * a - n * b), lin(m + n, cc), lin(cx, a + b), lin(m - n, m * a + b), lin(n - m, cc)];
    const opts = [];
    for (const c of cand) { if (opts.length < 4 && !opts.includes(c)) opts.push(c); }
    if (!opts.includes(right)) return null;
    return { q: `化简：${m}(x + ${a}) − ${n}(x − ${b}) = ?`, type: 'choice', opts, ans: right,
      sol: [`第一个括号：${m}x + ${m * a}`, `第二个括号前是「−${n}」，里面两项都要变号：−${n}x + ${n * b}`,
            `合并：(${m}−${n})x + (${m * a}+${n * b}) = ${right}`] };
  }
},
{
  k: 'eval-expr', name: '整式化简求值', stage: 'M', pri: 3,
  ask: '代负数时有没有加括号？没加括号是最常见的失分点。',
  gen() {
    const x = LV === 1 ? pick([-2, -1, 2]) : pick([-4, -3, -2, -1, 2, 3, 4]), a = R(2, 4), b = R(1, 6), c = R(1, 9);
    const ans = a * x * x - b * x + c;
    return { q: `当 x = ${P(x)} 时，求 ${a}x² − ${b}x + ${c} 的值。`, ans: '' + ans, type: 'num',
      sol: [`代入时把 x 用括号包起来：${a}×${P(x)}² − ${b}×${P(x)} + ${c}`,
            `${P(x)}² = ${x * x}，所以 ${a}×${x * x} = ${a * x * x}`,
            `−${b}×${P(x)} = ${-b * x}`, `${a * x * x} ${S(-b * x)} ${S(c)} = ${ans}`] };
  }
},
{
  k: 'linear-eq', name: '解一元一次方程', stage: 'M', pri: 1,
  ask: '每写一步问他「这一步依据是什么」：移项要变号，两边同乘同除。',
  gen() {
    const t = lvT(3);
    if (t === 1) { const x = LV === 1 ? R(1, 8) : R(-6, 9), m = R(2, LV === 1 ? 5 : 7), n = R(-9, 9);
      return { q: `解方程：${m}x${S(n)} = ${N(m * x + n)}，x = ?`, ans: '' + x, type: 'num',
        sol: [`把常数移到右边（变号）：${m}x = ${N(m * x + n)}${S(-n)} = ${N(m * x)}`, `两边除以 ${m}：x = ${N(x)}`] }; }
    if (t === 2) { const x = R(-5, 8), m = R(3, 8); let n = R(2, 7); if (n === m) n = m + 1;
      const a = R(-9, 9), b = (m - n) * x + a;
      return { q: `解方程：${m}x${S(a)} = ${n}x${S(b)}，x = ?`, ans: '' + x, type: 'num',
        sol: [`含 x 的移到左边，常数移到右边：${m}x − ${n}x = ${b}${S(-a)}`, `${m - n}x = ${b - a}`, `x = ${x}`] }; }
    const b1 = pick([2, 3, 4]); let d1 = pick([2, 3, 6]); if (d1 === b1) d1 = b1 + 1;
    const k1 = R(1, 5), k2 = R(1, 5), x = R(-4, 14);
    const a = b1 * k1 - x, c = x - d1 * k2, e = k1 - k2;
    return { q: `解方程：(x${S(a)})/${b1} − (x${S(c)})/${d1} = ${N(e)}，x = ?`, ans: '' + x, type: 'num',
      sol: [`两边同乘分母的最小公倍数 ${b1 * d1 / gcd(b1, d1)}，去分母`,
            `注意：去分母后每个括号整体乘，别漏项`, `整理解得 x = ${x}`] };
  }
},
{
  k: 'eq-word', name: '一元一次方程应用', stage: 'M', pri: 3,
  ask: '让他先写「设……为 x」再列式，不许跳过设未知数这一步。',
  gen() {
    const t = R(1, 4);
    if (t === 1) { const x = R(3, 20), k = R(2, 5), m = R(2, 15);
      return { q: `一个数的 ${k} 倍加上 ${m} 等于 ${k * x + m}，这个数是多少？`, ans: '' + x, type: 'num',
        sol: [`设这个数为 x：${k}x + ${m} = ${k * x + m}`, `${k}x = ${k * x}，x = ${x}`] }; }
    if (t === 2) { const va = R(3, 8), t0 = pick([1, 2, 3]);
      const diff = pick(divisors(va * t0).filter(d => d >= 2 && d <= 8)) || 2;
      const N4 = nm2();
      return { q: `${N4[0]}每小时走 ${va} 千米，先走 ${t0} 小时；${N4[1]}每小时走 ${va + diff} 千米从同地出发追。设${N4[1]}用 x 小时追上，列方程求 x。`, ans: '' + (va * t0 / diff), type: 'num',
        sol: [`列方程：${va + diff}x = ${va}(x + ${t0})`, `${diff}x = ${va * t0}`, `x = ${va * t0 / diff}`] }; }
    if (t === 3) { const a = R(2, 20) * 10, p = pick([10, 20, 25, 50]);
      return { q: `${pick(IT)}进价 ${a} 元，卖 ${a * (1 + p / 100)} 元，利润率是多少？（只填数字，单位 %）`, ans: '' + p, type: 'num',
        sol: [`利润 = ${a * (1 + p / 100)} − ${a} = ${a * p / 100}`, `利润率 = 利润 ÷ 进价 = ${a * p / 100} ÷ ${a} = ${p}%`] }; }
    const x = R(2, 10), k = pick([2, 3]), S0 = R(8, 14);
    const F = k * (S0 + x) - x;
    return { q: `今年父亲 ${F} 岁，儿子 ${S0} 岁。几年后父亲的年龄是儿子的 ${k} 倍？`, ans: '' + x, type: 'num',
      sol: [`设 x 年后：${F} + x = ${k}(${S0} + x)`, `${F} + x = ${k * S0} + ${k}x`, `${k - 1}x = ${F - k * S0}，x = ${x}`] };
  }
},
{
  k: 'geom', name: '线段与角的计算', stage: 'M', pri: 4,
  ask: '让他画个草图，把已知数字标在图上再算。',
  gen() {
    const t = R(1, 5);
    if (t === 1) { const a = R(5, 30);
      return { q: `线段 AB = ${a} cm，M 是 AB 的中点，AM = ? cm（可填分数）`, ans: fstr(frac(a, 2)), type: 'frac',
        sol: [`中点把线段平分：${a} ÷ 2 = ${fstr(frac(a, 2))}`] }; }
    if (t === 2) { const a = R(20, 160);
      return { q: `一个角是 ${a}°，它的补角是多少度？`, ans: '' + (180 - a), type: 'num', sol: [`补角相加等于 180°：180 − ${a} = ${180 - a}`] }; }
    if (t === 3) { const a = R(10, 80);
      return { q: `一个角是 ${a}°，它的余角是多少度？`, ans: '' + (90 - a), type: 'num', sol: [`余角相加等于 90°：90 − ${a} = ${90 - a}`] }; }
    if (t === 4) { const a = R(10, 88) * 2;
      return { q: `∠AOB = ${a}°，OC 是 ∠AOB 的平分线，∠AOC = ? 度`, ans: '' + a / 2, type: 'num', sol: [`平分线把角分成两个相等的角：${a} ÷ 2 = ${a / 2}`] }; }
    const n = R(1, 5);
    return { q: `${n} 点整的时候，钟表上时针和分针的夹角是多少度？`, ans: '' + 30 * n, type: 'num',
      sol: [`表盘 12 大格，每格 30°`, `相差 ${n} 格 = ${30 * n}°`] };
  }
},
{
  k: 'stat', name: '平均数·中位数·众数', stage: 'M', pri: 5,
  ask: '中位数要先排序，问他排没排。',
  gen() {
    const t = R(1, 3);
    const n = 5;
    let arr = Array.from({ length: n }, () => R(60, 100));
    if (t === 1) {
      const sum = arr.reduce((a, b) => a + b, 0);
      arr[4] += (n - sum % n) % n;
      const s = arr.reduce((a, b) => a + b, 0);
      return { q: `最近 5 次${pick(['数学小测', '英语听写', '体育测试'])}的成绩：${arr.join('、')}。平均分是多少？`, ans: fstr(frac(s, n)), type: 'frac',
        sol: [`求和：${s}`, `${s} ÷ ${n} = ${fstr(frac(s, n))}`] };
    }
    if (t === 2) {
      const sorted = arr.slice().sort((a, b) => a - b);
      return { q: `全班随机抽 5 个人的${pick(['数学成绩', '身高（cm）', '每周运动分钟数'])}：${arr.join('、')}。中位数是多少？`, ans: '' + sorted[2], type: 'num',
        sol: [`先从小到大排：${sorted.join('、')}`, `一共 5 个，中间第 3 个就是中位数：${sorted[2]}`] };
    }
    const v = R(70, 95);
    arr = shuf([v, v, v, R(60, 69), R(96, 100)]);
    return { q: `班里 5 个同学的${pick(['数学成绩', '鞋码', '每天睡眠小时数'])}：${arr.join('、')}。众数是多少？`, ans: '' + v, type: 'num',
      sol: [`出现次数最多的那个数：${v}（出现 3 次）`] };
  }
}
];

const TMAP = {}; TOPICS.forEach(t => TMAP[t.k] = t);

/* ============================================================
   梯子题（搭桥）：先给一道他小学就会做的锚点题，紧接着给一道
   只多了负号 / 字母的初一题，让他自己看出「方法没变」。
   出处：小学薄弱生衔接初一的通行做法——先算 5−3，再算 5−(−3)。
   ============================================================ */
const BRIDGE = {
  'rat-addsub': () => { const a = R(8, 18), b = R(2, a - 3);   /* 必须 a>b，锚点题得是他真会做的 */
    return { p: { q: `${a} − ${b} = ?`, ans: '' + (a - b), type: 'num', sol: [`这道你小学就做过：${a - b}`, `记住这个数，下一题只多一个负号`] },
             m: { q: `${a} − (−${b}) = ?`, ans: '' + (a + b), type: 'num',
                  sol: [`和上面那道只差括号里的一个负号`, `减去 −${b}，等于加上 ${b}`, `${a} + ${b} = ${a + b}`] } }; },

  'rat-muldiv': () => { const a = R(3, 9), b = R(3, 9);
    return { p: { q: `${a} × ${b} = ?`, ans: '' + a * b, type: 'num', sol: [`乘法口诀就够：${a * b}`, `下一题的数字一样，只是前面多个负号`] },
             m: { q: `(−${a}) × ${b} = ?`, ans: '' + (-a * b), type: 'num',
                  sol: [`数字部分和上面一样是 ${a * b}`, `只有 1 个负号，奇数个 → 结果为负`, `= ${-a * b}`] } }; },

  'power': () => { const b = R(2, 5);
    return { p: { q: `${b}³ = ?`, ans: '' + b * b * b, type: 'num', sol: [`${b}×${b}×${b} = ${b * b * b}`, `下一题把底数换成 −${b}，看看结果会怎样`] },
             m: { q: `(−${b})³ = ?`, ans: '' + (-b * b * b), type: 'num',
                  sol: [`绝对值和上面一样是 ${b * b * b}`, `3 个负数相乘，奇数个 → 负`, `= ${-b * b * b}`] } }; },

  'neg-frac': () => { const d1 = pick([2, 3, 4, 6]), d2 = pick([2, 3, 4, 6].filter(x => x !== d1));
    const L = d1 * d2 / gcd(d1, d2);
    return { p: { q: `1/${d1} + 1/${d2} = ?`, ans: fstr(frac(L / d1 + L / d2, L)), type: 'frac',
                  sol: [`公分母 ${L}，通分后相加 = ${fstr(frac(L / d1 + L / d2, L))}`, `下一题通分的做法一字不改，只是第一项带负号`] },
             m: { q: `−1/${d1} + 1/${d2} = ?`, ans: fstr(frac(-L / d1 + L / d2, L)), type: 'frac',
                  sol: [`通分的做法和上面完全一样，公分母还是 ${L}`, `只是第一项带负号：${-L / d1}/${L} + ${L / d2}/${L}`,
                        `= ${fstr(frac(-L / d1 + L / d2, L))}`] } }; },

  'like-terms': () => { const a = R(2, 6), b = R(2, 6), n = R(3, 9);
    return { p: { q: `${a} × ${n} + ${b} × ${n} = ?（用简便方法）`, ans: '' + (a + b) * n, type: 'num',
                  sol: [`都有 ${n}，提出来：(${a}+${b}) × ${n} = ${(a + b) * n}`, `下一题把 ${n} 换成字母 a，做法完全一样`] },
             m: { q: `化简：${a}a + ${b}a = ?（填合并后 a 前面的数）`, ans: '' + (a + b), type: 'num',
                  sol: [`把上面那道的 ${n} 换成字母 a，做法一样`, `${a} 个 a 加 ${b} 个 a = ${a + b} 个 a`,
                        `所以是 ${a + b}a，系数 ${a + b}`] } }; },

  'remove-paren': () => { const b = R(2, 6), c = R(2, 6), a = R(b + c + 2, 24);
    return { p: { q: `${a} − (${b} + ${c}) = ?`, ans: '' + (a - b - c), type: 'num',
                  sol: [`括号里先算：${b}+${c} = ${b + c}`, `${a} − ${b + c} = ${a - b - c}`, `下一题不许先算括号，直接去括号看符号`] },
             m: { q: `${a} − (${b} + ${c}) 去括号后等于 ${a} − ${b} ? ${c}，问号处是 + 还是 −？（填 1 表示 +，填 2 表示 −）`,
                  ans: '2', type: 'num',
                  sol: [`括号前是负号，里面每一项都要变号`, `${a} − ${b} − ${c}，所以问号是「−」`,
                        `这条规则到了 ${a} − (${b}x + ${c}) 一样成立`] } }; },

  'eval-expr': () => { const a = R(2, 5), b = R(1, 9), x = R(2, 5);
    return { p: { q: `当 x = ${x} 时，${a}x + ${b} = ?`, ans: '' + (a * x + b), type: 'num',
                  sol: [`把 x 换成 ${x}：${a}×${x} + ${b} = ${a * x + b}`, `下一题 x 变成负数，代入时记得加括号`] },
             m: { q: `当 x = −${x} 时，${a}x + ${b} = ?`, ans: '' + (-a * x + b), type: 'num',
                  sol: [`代入时把 x 用括号包起来：${a}×(−${x}) + ${b}`, `${a}×(−${x}) = ${-a * x}`,
                        `${-a * x} + ${b} = ${-a * x + b}`] } }; },

  'linear-eq': () => { const m = R(2, 7), x = R(2, 9), n = R(1, 12);
    return { p: { q: `解方程：${m}x + ${n} = ${m * x + n}，x = ?`, ans: '' + x, type: 'num',
                  sol: [`两边减 ${n}，再除 ${m}：x = ${x}`, `下一题步骤一字不改，只是答案会是负数`] },
             m: { q: `解方程：${m}x + ${n} = ${N(-m * x + n)}，x = ?`, ans: '' + (-x), type: 'num',
                  sol: [`步骤和上面一题一模一样：两边减 ${n}`, `${m}x = ${N(-m * x)}`,
                        `两边除 ${m}：x = ${N(-x)}（初一开始，答案可以是负数）`] } }; },

  'sign-mix': () => { const b = R(2, 6), c = R(2, 6), a = R(b * c + 1, b * c + 16);
    return { p: { q: `${a} − ${b} × ${c} = ?`, ans: '' + (a - b * c), type: 'num',
                  sol: [`先乘后减：${b}×${c} = ${b * c}，${a} − ${b * c} = ${a - b * c}`, `下一题只把 ${c} 换成 −${c}，顺序不变`] },
             m: { q: `${a} − ${b} × (−${c}) = ?`, ans: '' + (a + b * c), type: 'num',
                  sol: [`顺序和上面一样，先算乘法：${b} × (−${c}) = ${-b * c}`,
                        `${a} − (−${b * c})，减负数变加正数`, `= ${a} + ${b * c} = ${a + b * c}`] } }; }
};

/* 取一对梯子题；没有配对的知识点返回 null */
function genBridge(k) {
  if (!BRIDGE[k]) return null;
  const pair = BRIDGE[k]();
  const tag = Math.random().toString(36).slice(2, 8);
  return [
    Object.assign({ topic: null, tname: '搭桥 ① 这道你小学就会', ask: TMAP[k].ask, qid: 'brp_' + tag }, pair.p),
    Object.assign({ topic: k, tname: '搭桥 ② 只多了一个负号', ask: TMAP[k].ask, qid: 'brm_' + tag }, pair.m)
  ];
}


/* 生成一题，带重试防退化 */
function genQ(k, lv) {
  const t = TMAP[k];
  setLv(lv);
  for (let i = 0; i < 12; i++) {
    let o;
    try { o = t.gen(); } catch (e) { continue; }
    if (!o || o.skip) continue;
    o.topic = k; o.tname = t.name; o.ask = t.ask;
    o.qid = k + '_' + Math.random().toString(36).slice(2, 9);
    if (o.type === 'choice') o.opts = shuf(o.opts);
    return o;
  }
  return { topic: k, tname: t.name, ask: t.ask, qid: k + '_f', q: '（本题生成失败，跳过即可）', ans: '0', type: 'num', sol: ['—'] };
}
function genMany(k, n, lv) { const r = []; const seen = new Set(); let guard = 0;
  while (r.length < n && guard++ < n * 20) { const q = genQ(k, lv); if (seen.has(q.q)) continue; seen.add(q.q); r.push(q); }
  return r; }

/* ---------- 口算热身 ---------- */
/* force: 'warmup-frac' 先练小学分数/小数手感，'warmup-neg' 再进负数。
   出处：衔接建议「先做 5 分钟分数小数加减，再转到带负号的题」，不要一上来就负数。*/
function warmupQ(stage, force) {
  const kinds = ['int'];
  if (stage >= 2) kinds.push('frac');
  if (stage >= 2) kinds.push('neg');
  if (stage >= 3) kinds.push('negmul', 'pow');
  let kd;
  if (force === 'frac') kd = pick(['int', 'frac']);
  else if (force === 'neg') kd = pick(stage >= 3 ? ['neg', 'negmul', 'pow'] : ['neg']);
  else kd = pick(kinds);
  if (kd === 'int') { const t = R(1, 3);
    if (t === 1) { const a = R(11, 89), b = R(11, 89); return { q: `${a} + ${b}`, ans: '' + (a + b) }; }
    if (t === 2) { const a = R(21, 99), b = R(11, 20); return { q: `${a} − ${b}`, ans: '' + (a - b) }; }
    const a = R(3, 12), b = R(3, 12); return { q: `${a} × ${b}`, ans: '' + a * b }; }
  if (kd === 'frac') { const d = pick([2, 3, 4, 5, 6, 8]), n1 = nCop(d), d2 = pick([2, 3, 4, 6, 8]), n2 = nCop(d2);
    const L = d * d2 / gcd(d, d2); const f = frac(n1 * L / d + n2 * L / d2, L);
    return { q: `${n1}/${d} + ${n2}/${d2}`, ans: fstr(f) }; }
  if (kd === 'neg') { const a = R(-19, 19) || 4, b = R(-19, 19) || -5;
    return { q: `${P(a)} + ${P(b)}`, ans: '' + (a + b) }; }
  if (kd === 'negmul') { const a = R(2, 12) * pick([1, -1]), b = R(2, 9) * pick([1, -1]);
    return { q: `${P(a)} × ${P(b)}`, ans: '' + a * b }; }
  const b = R(2, 6), f = R(1, 3);
  if (f === 1) return { q: `(−${b})²`, ans: '' + b * b };
  if (f === 2) return { q: `−${b}²`, ans: '' + (-b * b) };
  return { q: `(−${b})³`, ans: '' + (-b * b * b) };
}

/* ============================================================
   数学史彩蛋：每天最多弹 2 条，和当天练的知识点挂钩。
   目的不是好玩，是让他知道这些规则不是老师瞎编的、是人想出来的。
   （游戏化 meta 分析：有效的是自主感与关联感，不是徽章积分。）
   ============================================================ */
const FACTS = [
{ id: 'f01', ks: ['numline', 'rat-addsub'], t: '负数是中国人最先用的',
  b: '《九章算术》两千年前就在用正负数，比印度早约 700 年，比欧洲早 1700 年。刘徽还规定：红色小棍摆的是正数，黑色的是负数——和现在说的「赤字」刚好相反。' },
{ id: 'f02', ks: ['rat-addsub', 'sign-mix'], t: '你今天练的规则，两千年前就写下来了',
  b: '《九章算术》「正负术」原文八个字：同名相除，异名相益。翻译过来就是你刚练的那句——减去一个数，等于加上它的相反数。' },
{ id: 'f03', ks: ['rat-muldiv', 'power'], t: '欧洲人曾管负数叫「荒谬的数」',
  b: '17 世纪以前，欧洲数学家拒绝承认负数，管它叫「假数」「荒谬的数」，理由是「哪有比什么都没有还少的东西」。中国人早一千多年就不纠结这个了。' },
{ id: 'f04', ks: ['linear-eq', 'eq-word'], t: 'algebra 的原意是「把它接回去」',
  b: '公元 820 年，巴格达的花拉子米写了本书叫 al-jabr，意思是「还原、重新接好」。这个词后来变成英文 algebra。你解方程时把项从一边移到另一边、把式子重新接好——那个动作就是 al-jabr 本身。' },
{ id: 'f05', ks: ['linear-eq'], t: 'algorithm（算法）是一个人的名字',
  b: '花拉子米 al-Khwarizmi 的名字被翻成拉丁文后变成了 algorithm。今天所有电脑程序都在用这个词，源头是一千两百年前一个写方程的人。' },
{ id: 'f06', ks: ['linear-eq', 'eval-expr', 'simple-eq'], t: '等号只有 468 岁',
  b: '1557 年威尔士人 Robert Recorde 第一次用「=」表示相等，理由很朴素：没有两样东西能比两条平行线更相等。同一本书也是第一本用英文写「+」和「−」的书。' },
{ id: 'f07', ks: ['frac-add', 'frac-muldiv'], t: '古埃及人不会写 3/4',
  b: '古埃及只承认分子是 1 的分数。要表示 3/4，他们得写成 1/2 + 1/4。你随手就能写的 3/4，在那时候是个技术难题。' },
{ id: 'f08', ks: ['power', 'sci'], t: '阿基米德数过宇宙里的沙子',
  b: '两千多年前阿基米德写《数沙者》，为了算「整个宇宙能装多少粒沙」，他不得不发明一套表示超大数的办法——那就是科学记数法的祖先。' },
{ id: 'f09', ks: ['sci', 'power'], t: '一张纸折 42 次能到月球',
  b: '纸厚 0.1 毫米，每折一次翻一倍。2⁴² × 0.1 毫米 ≈ 44 万公里，比地球到月球还远。乘方涨得快到反直觉，这就是为什么大数非要写成 10ⁿ。' },
{ id: 'f10', ks: ['area', 'geom', 'volume'], t: '祖冲之的圆周率领先世界九百年',
  b: '1500 年前祖冲之算出 3.1415926 < π < 3.1415927，精确到小数第 7 位。欧洲要到 16 世纪才追上这个精度。' },
{ id: 'f11', ks: ['geom'], t: '圆是 360 度，得怪巴比伦人',
  b: '巴比伦人用 60 进制数数（60 好分），于是一圈定 360 度、1 小时 60 分、1 分 60 秒。四千年前的习惯，你今天还在用。' },
{ id: 'f12', ks: ['numline', 'abs-calc'], t: '0 是最晚出生的数字',
  b: '1、2、3 谁都会数，但「什么都没有」也算一个数——这个念头直到公元 5 世纪才在印度定下来，欧洲又花了近千年才接受它。' },
{ id: 'f13', ks: ['like-terms', 'monomial'], t: 'x 为什么代表未知数',
  b: '花拉子米管未知数叫「某物」，阿拉伯语 shay’。传到西班牙写成 xay，慢慢缩成一个 x。笛卡尔后来定了规矩：已知数用 a b c，未知数用 x y z。' },
{ id: 'f14', ks: ['stat'], t: '平均数是天文学家发明的',
  b: '测星星位置每次都有误差。天文学家发现把多次测量取平均，误差会互相抵消。平均数最早不是用来算成绩的，是用来对付误差的。' },
{ id: 'f15', ks: ['eq-word', 'word-sumdiff'], t: '四千年前的应用题',
  b: '古埃及莱因德纸草书里有这么一道：「某数加上它的七分之一等于 19，求某数。」和你今天做的方程应用题几乎一模一样。' },
{ id: 'f16', ks: ['rat-mixed', 'sign-mix', 'rat-muldiv'], t: '负负得正不是规定，是被逼出来的',
  b: '如果 (−1)×(−1) 等于 −1，乘法分配律立刻自相矛盾：(−1)×(1−1) 会算出两个不同答案。数学家不是随便定的，是因为只有负负得正，其他规则才不打架。' },
{ id: 'f17', ks: ['power-frac', 'power'], t: '棋盘上的麦子',
  b: '传说发明国际象棋的人只要一个赏赐：第一格 1 粒麦，每格翻倍。到第 64 格是 2⁶³ 粒，全世界几千年的收成都不够。这就是乘方。' },
{ id: 'f18', ks: ['calc-order', 'paren-nest'], t: '先乘后加是约定，不是天理',
  b: '运算顺序是数学家为了少写括号约的规矩。没有这个约定，3+4×5 就得写成 3+(4×5) 才不含糊。你背的规则，本质是一份省事的合同。' },
{ id: 'f19', ks: ['percent', 'ratio'], t: '百分号是写快了缩出来的',
  b: '意大利商人写 per cento（每一百），写快了缩成 per c̸o，再快就成了 %。两个小圈加一道斜线，意思就是「分母是 100」。' },
{ id: 'f21', ks: ['unit'], t: '「米」原本是地球的尺寸',
  b: '1791 年法国人定义 1 米 = 从北极到赤道距离的千万分之一。后来发现测量有偏差，但米这个长度就这么定下来了。你换算的每一个单位背后都有一场吵架。' },
{ id: 'f22', ks: ['word-speed', 'word-work'], t: '追及问题救过命',
  b: '二战时英国靠「追及」这类计算推算德国潜艇位置：知道对方速度和自己速度，算出多久能拦上。学校里的行程题，原型是真实的航海和作战问题。' },
{ id: 'f23', ks: ['remove-paren', 'like-terms'], t: '括号是印刷厂逼出来的',
  b: '16 世纪之前数学家用一条横线盖住整个式子表示「这些是一体的」，印刷时特别难排。于是改用了 ( ) 这种一行就能打完的写法，沿用至今。' },
{ id: 'f24', ks: ['neg-frac', 'frac-add'], t: '分数线的横杠有名字',
  b: '那条横线叫 vinculum，拉丁语「捆绳」的意思——它的作用就是把上下两部分捆成一个整体。所以分数线天然带括号功能，这也是为什么 (a+b)/2 不用再加括号。' },
{ id: 'f20', ks: ['decimal', 'neg-frac'], t: '小数点差点长成别的样子',
  b: '16 世纪欧洲的小数写法五花八门：有人用竖线，有人用逗号，有人在整数部分下面划横线。今天英美用点、欧洲大陆用逗号，就是那场混战留下的。' }
];
/* 挑一条：优先和今天知识点相关且没看过的 */
function pickFact(ks, seen) {
  seen = seen || [];
  const rel = FACTS.filter(f => f.ks.some(k => ks.indexOf(k) >= 0) && seen.indexOf(f.id) < 0);
  if (rel.length) return pick(rel);
  const any = FACTS.filter(f => seen.indexOf(f.id) < 0);
  if (any.length) return pick(any);
  const rel2 = FACTS.filter(f => f.ks.some(k => ks.indexOf(k) >= 0));
  return rel2.length ? pick(rel2) : pick(FACTS);
}
