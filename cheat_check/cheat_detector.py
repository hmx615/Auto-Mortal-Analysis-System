#!/usr/bin/env python3
"""
查挂检测模块 - 多维度统计分析 + Fisher 合并置信度

用法:
  python cheat_detector.py                   # 使用 config.py 中的 CHEAT_CHECK_TARGET
  python cheat_detector.py 路人的自我修养     # 指定玩家
  python cheat_detector.py --all             # 分析 data/ 下所有玩家
"""

import csv
import glob
import sys
import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from config import (
    PLAYER_NAME         as DEFAULT_PLAYER,
    CHEAT_CHECK_TARGET  as _CFG_TARGET,
    CHEAT_MIN_WINDOW    as _CFG_MIN_WINDOW,
    CHEAT_DELTA_MIN     as _CFG_DELTA_MIN,
    CHEAT_HIGH_MEAN     as _CFG_HIGH_MEAN,
    CHEAT_FULLTIME_MR       as _CFG_FT_MR,
    CHEAT_FULLTIME_RATING   as _CFG_FT_RAT,
    CHEAT_FULLTIME_HIGH_PCT as _CFG_FT_PCT,
)

DATA_ROOT = ROOT / 'data'

MIN_WINDOW         = _CFG_MIN_WINDOW
DELTA_MIN          = _CFG_DELTA_MIN
HIGH_MEAN          = _CFG_HIGH_MEAN
HIGH_RATING_THRESH = 90    # 维度四"高分局"阈值

# 全程开挂三维度阈值
FT_MR_MIN      = _CFG_FT_MR    # match_rate 全局均值
FT_RATING_MIN  = _CFG_FT_RAT   # rating 全局均值
FT_HIGH_PCT    = _CFG_FT_PCT   # rating≥90 占比（%）


# ── 数据加载 ─────────────────────────────────────────────────

TIME_FMTS = (
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M',
    '%m/%d/%y %H:%M',
    '%Y/%m/%d %H:%M:%S',
)

def _parse_time(s: str):
    for fmt in TIME_FMTS:
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            pass
    return None


def load_player_data(player: str) -> list:
    base = DATA_ROOT / player
    if not base.exists():
        raise FileNotFoundError(f"玩家目录不存在: {base}")

    seen = {}
    for fp in glob.glob(str(base / 'mortal_results*.csv')):
        with open(fp, 'r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                uid = row.get('uuid', '').strip()
                mr_s = row.get('match_rate', '').strip()
                t_s  = row.get('start_time', '').strip()
                if not uid or not mr_s or not t_s:
                    continue
                try:
                    mr = float(mr_s)
                    rt = float(row.get('rating') or 0)
                except ValueError:
                    continue
                t = _parse_time(t_s)
                if t is None:
                    continue
                seen[uid] = {
                    'uuid': uid, 'time': t,
                    'match_rate': mr, 'rating': rt,
                    'rank': int(row.get('rank') or 0),
                }

    if not seen:
        raise ValueError(f"玩家 {player} 无有效分析数据，请先运行分析模块")

    return sorted(seen.values(), key=lambda x: x['time'])


# ── 变点检测 ─────────────────────────────────────────────────

def _cohen_d(a: np.ndarray, b: np.ndarray) -> float:
    pooled = np.sqrt((np.var(a, ddof=1) + np.var(b, ddof=1)) / 2)
    return float((np.mean(b) - np.mean(a)) / pooled) if pooled > 0 else 0.0


def check_fulltime(mr: np.ndarray, rat: np.ndarray) -> dict:
    """全程开挂三维度检测，三项同时满足才判定。"""
    rat_valid = rat[rat > 0]
    mean_mr    = float(np.mean(mr))
    mean_rat   = float(np.mean(rat_valid)) if len(rat_valid) else 0.0
    high_pct   = float((rat_valid >= HIGH_RATING_THRESH).mean() * 100) if len(rat_valid) else 0.0
    hit_mr     = mean_mr   >= FT_MR_MIN
    hit_rat    = mean_rat  >= FT_RATING_MIN
    hit_pct    = high_pct  >= FT_HIGH_PCT
    is_fulltime = hit_mr and hit_rat and hit_pct
    return {
        'is_fulltime': is_fulltime,
        'mean_mr':   mean_mr,   'hit_mr':  hit_mr,
        'mean_rat':  mean_rat,  'hit_rat': hit_rat,
        'high_pct':  high_pct,  'hit_pct': hit_pct,
    }


def find_best_changepoint(series: np.ndarray, min_window: int) -> dict:
    n = len(series)
    best = {'idx': -1, 'delta': 0.0, 'p_value': 1.0, 't_stat': 0.0, 'cohen_d': 0.0}
    for i in range(min_window, n - min_window):
        bef, aft = series[:i], series[i:]
        delta = float(np.mean(aft) - np.mean(bef))
        if delta <= 0:
            continue
        t_stat, p_val = stats.ttest_ind(bef, aft, equal_var=False)
        cd = _cohen_d(bef, aft)
        if p_val < best['p_value'] or (abs(p_val - best['p_value']) < 1e-4 and delta > best['delta']):
            best = {'idx': i, 'delta': delta, 'p_value': float(p_val),
                    't_stat': float(t_stat), 'cohen_d': cd}
    return best


# ── 统计维度 ─────────────────────────────────────────────────

def _mean_shift_tests(before: np.ndarray, after: np.ndarray) -> dict:
    if len(before) < 2 or len(after) < 2:
        return {'p_welch': 1.0, 'p_mwu': 1.0, 'p_value': 1.0,
                't_stat': 0.0, 'u_stat': 0.0, 'cohen_d': 0.0,
                'mean_before': float(np.mean(before)) if len(before) else 0.0,
                'mean_after':  float(np.mean(after))  if len(after)  else 0.0,
                'delta': 0.0, 'insufficient': True}
    t_stat, p_welch = stats.ttest_ind(before, after, equal_var=False)
    u_stat, p_mwu   = stats.mannwhitneyu(before, after, alternative='two-sided')
    cd    = _cohen_d(before, after)
    delta = float(np.mean(after) - np.mean(before))
    return {
        'p_welch': float(p_welch), 'p_mwu': float(p_mwu),
        'p_value': min(float(p_welch), float(p_mwu)),
        't_stat': float(t_stat), 'u_stat': float(u_stat),
        'cohen_d': cd, 'delta': delta,
        'mean_before': float(np.mean(before)),
        'mean_after':  float(np.mean(after)),
        'insufficient': False,
    }


def dim1_rating_shift(rat_before: np.ndarray, rat_after: np.ndarray) -> dict:
    return _mean_shift_tests(rat_before, rat_after)


def dim2_matchrate_shift(mr_before: np.ndarray, mr_after: np.ndarray) -> dict:
    return _mean_shift_tests(mr_before, mr_after)


def dim3_variance_drop(mr_before: np.ndarray, mr_after: np.ndarray) -> dict:
    if len(mr_before) < 2 or len(mr_after) < 2:
        return {'F': 0.0, 'p_value': 1.0, 'var_before': 0.0, 'var_after': 0.0,
                'std_before': 0.0, 'std_after': 0.0, 'var_ratio': 1.0, 'insufficient': True}
    var_b = float(np.var(mr_before, ddof=1))
    var_a = float(np.var(mr_after,  ddof=1))
    if var_a == 0:
        F, p_val = float('inf'), 0.0
        var_ratio = float('inf')
    else:
        F = var_b / var_a
        p_val = float(stats.f.sf(F, len(mr_before) - 1, len(mr_after) - 1))
        var_ratio = F
    return {
        'F': F, 'p_value': p_val,
        'var_before': var_b, 'var_after': var_a,
        'std_before': float(np.std(mr_before, ddof=1)),
        'std_after':  float(np.std(mr_after,  ddof=1)),
        'var_ratio': var_ratio, 'insufficient': False,
    }


def dim4_high_score_binom(rat_before: np.ndarray, rat_after: np.ndarray,
                           threshold: float = HIGH_RATING_THRESH) -> dict:
    if len(rat_before) < 2 or len(rat_after) < 2:
        return {'p_value': 1.0, 'k': 0, 'm': 0, 'p0': 0.0,
                'rate_after': 0.0, 'threshold': threshold, 'insufficient': True}
    n_high_b = int((rat_before >= threshold).sum())
    p0 = max(n_high_b / len(rat_before), 1.0 / len(rat_before))
    k  = int((rat_after >= threshold).sum())
    m  = len(rat_after)
    try:
        res = stats.binomtest(k, m, p0, alternative='greater')
        p_val = float(res.pvalue)
    except AttributeError:
        p_val = float(stats.binom_test(k, m, p0, alternative='greater'))
    return {
        'p_value': p_val, 'k': k, 'm': m, 'p0': p0,
        'rate_after': k / m if m else 0.0,
        'n_high_before': n_high_b, 'n_before': len(rat_before),
        'threshold': threshold, 'insufficient': False,
    }


# ── Fisher 合并 ───────────────────────────────────────────────

def fisher_combine(p_values: list) -> tuple:
    tiny = np.finfo(float).tiny
    valid = [max(p, tiny) for p in p_values if p < 1.0]
    if not valid:
        return 0.0, 0.0
    chi2_stat = -2.0 * sum(np.log(p) for p in valid)
    df = 2 * len(valid)
    combined_p = float(stats.chi2.sf(chi2_stat, df))
    confidence = min(1.0 - combined_p, 0.999)
    return chi2_stat, confidence


def make_verdict(confidence: float, dim3: dict, delta_mr: float) -> tuple:
    """
    判定逻辑：
    - 核心门控：方差是否显著下降（AI特征）
      - 方差无变化 → 自然进步，无论其他维度多显著
      - 方差显著下降 → 走 Fisher 置信度路径
    """
    var_dropped = (dim3 is not None
                   and not dim3.get('insufficient')
                   and dim3['p_value'] < 0.05
                   and dim3['var_ratio'] > 1.3)

    if not var_dropped:
        if delta_mr >= 8.0:
            return "△ 存在突变，性质不明", \
                   f"match_rate +{delta_mr:.1f}pp 但方差无变化，建议人工复核"
        return "✓ 自然进步", "性能提升但方差无变化，符合自然进步特征"

    pct = confidence * 100
    if pct < 50:
        return "无异常",   "各维度统计均未显示显著异常"
    if pct < 80:
        return "轻微异常", "部分维度出现统计偏差，建议关注"
    if pct < 95:
        return "高度疑似", "多维度统计显著，高度疑似AI辅助"
    return     "极高置信", "所有维度高度显著，极高概率存在AI辅助"


# ── 主分析 ────────────────────────────────────────────────────

def analyze(player: str, min_window: int = MIN_WINDOW,
            delta_min: float = DELTA_MIN, high_mean: float = HIGH_MEAN) -> dict:
    rows = load_player_data(player)
    n    = len(rows)
    if n < min_window * 2:
        return {'error': f"数据不足（{n} 场，至少需要 {min_window * 2} 场）",
                'player': player}

    mr    = np.array([r['match_rate'] for r in rows])
    times = [r['time'] for r in rows]
    rat_all = np.array([r['rating'] for r in rows])

    # 全程开挂检测（优先于变点检测）
    ft = check_fulltime(mr, rat_all)

    cp = find_best_changepoint(mr, min_window)

    d1 = d2 = d3 = d4 = None
    chi2_stat = confidence = 0.0
    grade = description = ''

    if cp['idx'] >= 0:
        idx = cp['idx']
        mr_b, mr_a   = mr[:idx],      mr[idx:]
        rat_b_raw    = rat_all[:idx]
        rat_a_raw    = rat_all[idx:]
        rat_b = rat_b_raw[rat_b_raw > 0]
        rat_a = rat_a_raw[rat_a_raw > 0]

        cp['time']         = times[idx]
        cp['n_before']     = idx
        cp['n_after']      = n - idx
        cp['mean_mr_before'] = float(np.mean(mr_b))
        cp['mean_mr_after']  = float(np.mean(mr_a))
        cp['mean_rat_before'] = float(np.mean(rat_b)) if len(rat_b) else 0.0
        cp['mean_rat_after']  = float(np.mean(rat_a)) if len(rat_a) else 0.0

        d1 = dim1_rating_shift(rat_b, rat_a)
        d2 = dim2_matchrate_shift(mr_b, mr_a)
        d3 = dim3_variance_drop(mr_b, mr_a)
        d4 = dim4_high_score_binom(rat_b, rat_a)

        p_vals = [d['p_value'] for d in [d1, d2, d3, d4]
                  if not d.get('insufficient')]
        chi2_stat, confidence = fisher_combine(p_vals)
    else:
        cp['time'] = cp['n_before'] = cp['n_after'] = None

    grade, description = make_verdict(
        confidence,
        d3,
        cp['delta'] if cp and cp['idx'] >= 0 else 0.0
    )

    return {
        'player': player, 'n_games': n, 'times': times,
        'mean_all': float(np.mean(mr)),
        'fulltime': ft,
        'changepoint': cp,
        'dim1': d1, 'dim2': d2, 'dim3': d3, 'dim4': d4,
        'chi2_stat': chi2_stat, 'confidence': confidence,
        'grade': grade, 'description': description,
    }


# ── 报告输出 ──────────────────────────────────────────────────

def _sig(p: float) -> str:
    return '[显著 ***]' if p < 0.001 else '[显著 **]' if p < 0.01 else \
           '[显著 *]'  if p < 0.05  else '[不显著]'

def _effect(d: float) -> str:
    return '大效应' if abs(d) >= 0.8 else '中效应' if abs(d) >= 0.5 else '小效应'


def print_report(result: dict):
    if 'error' in result:
        print(f"✗ [{result['player']}] {result['error']}\n")
        return

    lines = _build_report_lines(result)
    output = '\n'.join(lines) + '\n'
    print(output)

    # 保存到玩家目录
    out_path = DATA_ROOT / result['player'] / 'cheat_report.txt'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(output)
    print(f"  报告已保存: {out_path}\n")


def _build_report_lines(result: dict) -> list:
    W = 62
    lines = []
    a = lines.append

    a('=' * W)
    a(f"  查挂报告  玩家: {result['player']}")
    a('=' * W)
    t0 = result['times'][0].strftime('%Y-%m-%d')
    t1 = result['times'][-1].strftime('%Y-%m-%d')
    a(f"  总场数:    {result['n_games']}    时间范围: {t0} → {t1}")
    a(f"  全局均值:  match_rate {result['mean_all']:.2f}%")

    cp = result['changepoint']
    ft = result['fulltime']

    a(f"\n── 全程开挂检测 {'─' * 43}")
    def _hit(ok): return '✓ 达标' if ok else '✗ 未达'
    a(f"  match_rate 均值:  {ft['mean_mr']:.2f}%  (阈值 ≥{FT_MR_MIN}%)  {_hit(ft['hit_mr'])}")
    a(f"  rating 均值:      {ft['mean_rat']:.2f}   (阈值 ≥{FT_RATING_MIN})  {_hit(ft['hit_rat'])}")
    a(f"  rating≥90 占比:   {ft['high_pct']:.1f}%  (阈值 ≥{FT_HIGH_PCT}%)  {_hit(ft['hit_pct'])}")
    if ft['is_fulltime']:
        a(f"  → 三项全部达标，判定为 ⚠ 疑似全程AI辅助")
    else:
        hits = sum([ft['hit_mr'], ft['hit_rat'], ft['hit_pct']])
        a(f"  → {hits}/3 项达标，不触发全程开挂判定")

    a(f"\n── 变点检测 {'─' * 49}")
    if cp['idx'] < 0:
        a("  未检测到有效变点，跳过统计检验")
    else:
        a(f"  节点时间:  {cp['time'].strftime('%Y-%m-%d %H:%M')}")
        a(f"  节点前:    {cp['n_before']} 场  match_rate {cp['mean_mr_before']:.2f}%  rating {cp['mean_rat_before']:.2f}")
        a(f"  节点后:    {cp['n_after']} 场  match_rate {cp['mean_mr_after']:.2f}%  rating {cp['mean_rat_after']:.2f}")

    for label, d, unit in [
        ('维度一：Rating 均值突变',   result['dim1'], ''),
        ('维度二：一致率均值突变',     result['dim2'], '%'),
    ]:
        a(f"\n── {label} {'─' * (W - len(label) - 5)}")
        if d is None or d.get('insufficient'):
            a("  数据不足，跳过"); continue
        a(f"  Welch t 检验:   t={d['t_stat']:>7.2f}  p={d['p_welch']:.2e}  {_sig(d['p_welch'])}")
        a(f"  Mann-Whitney U: U={d['u_stat']:>7.0f}  p={d['p_mwu']:.2e}  {_sig(d['p_mwu'])}")
        a(f"  Cohen's d:      {d['cohen_d']:.3f}  ({_effect(d['cohen_d'])})")
        a(f"  均值变化:       {d['mean_before']:.2f}{unit} → {d['mean_after']:.2f}{unit}  (Δ {d['delta']:+.2f}{unit})")
        a(f"  代表 p 值:      {d['p_value']:.2e}")

    d3 = result['dim3']
    a(f"\n── 维度三：方差骤降检验 {'─' * 38}")
    if d3 is None or d3.get('insufficient'):
        a("  数据不足，跳过")
    else:
        a(f"  F 统计量:       {d3['F']:.3f}  (前/后方差比)")
        a(f"  F 检验 p 值:    {d3['p_value']:.2e}  {_sig(d3['p_value'])}")
        a(f"  节点前标准差:   {d3['std_before']:.2f}%   节点后标准差: {d3['std_after']:.2f}%")

    d4 = result['dim4']
    a(f"\n── 维度四：持续高分二项检验 {'─' * 35}")
    if d4 is None or d4.get('insufficient'):
        a("  数据不足，跳过")
    else:
        a(f"  高分局阈值:     rating ≥ {d4['threshold']}")
        a(f"  节点前基准概率: {d4['p0']*100:.1f}%  ({d4['n_high_before']}/{d4['n_before']})")
        a(f"  节点后高分局:   {d4['k']}/{d4['m']}  ({d4['rate_after']*100:.1f}%)")
        a(f"  二项检验 p 值:  {d4['p_value']:.2e}  {_sig(d4['p_value'])}")

    a(f"\n{'─' * W}")
    if result['chi2_stat'] > 0:
        a(f"  Fisher χ²:     {result['chi2_stat']:.2f}")
    conf_pct = result['confidence'] * 100
    if result['fulltime']['is_fulltime']:
        grade = "⚠ 疑似全程AI辅助"
        desc  = f"三维度全部达标（match_rate {result['fulltime']['mean_mr']:.1f}% / rating {result['fulltime']['mean_rat']:.1f} / 高分占比 {result['fulltime']['high_pct']:.1f}%）"
    else:
        grade = result['grade']
        desc  = result['description']
    a(f"  综合置信度:    {conf_pct:.1f}%")
    a(f"  等级:          {grade}")
    a(f"  说明:          {desc}")
    a('=' * W)

    return lines


# ── CLI ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='查挂检测')
    parser.add_argument('player',       nargs='?', default=None)
    parser.add_argument('--all',        action='store_true')
    parser.add_argument('--min-window', type=int,   default=None)
    parser.add_argument('--delta',      type=float, default=None)
    parser.add_argument('--high-mean',  type=float, default=None)
    args = parser.parse_args()

    min_window = args.min_window if args.min_window is not None else MIN_WINDOW
    delta_min  = args.delta      if args.delta      is not None else DELTA_MIN
    high_mean  = args.high_mean  if args.high_mean  is not None else HIGH_MEAN
    kwargs = dict(min_window=min_window, delta_min=delta_min, high_mean=high_mean)

    if args.all or _CFG_TARGET.strip().upper() == 'ALL':
        players = [p.name for p in DATA_ROOT.iterdir() if p.is_dir()]
    elif args.player:
        players = [args.player]
    elif ',' in _CFG_TARGET:
        players = [p.strip() for p in _CFG_TARGET.split(',') if p.strip()]
    else:
        players = [_CFG_TARGET.strip() or DEFAULT_PLAYER]

    for player in players:
        try:
            result = analyze(player, **kwargs)
        except (FileNotFoundError, ValueError) as e:
            print(f"✗ [{player}] {e}\n")
            continue
        print_report(result)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n✗ 程序异常: {e}")
        import traceback
        traceback.print_exc()
