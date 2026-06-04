#!/usr/bin/env python3
"""一键并行分析：自动分牌谱 → 启动 N 个 worker → 实时进度面板 → 自动合并

用法:
  python run_analysis.py        # 使用 config.py 中的 WORKER_COUNT
  python run_analysis.py 5      # 指定 5 个 worker
"""

import csv
import glob
import os
import signal
import sys
import subprocess
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PLAYER_NAME, WORKER_COUNT, TWOCAPTCHA_API_KEY as _API_KEY

from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from rich import box

SCRIPT_DIR = Path(__file__).parent
DATA_DIR   = SCRIPT_DIR.parent / 'data' / PLAYER_NAME
ANALYZER   = SCRIPT_DIR / 'win_mortal_analyzer_2captcha.py'
PYTHON     = sys.executable


# ── 工具函数 ────────────────────────────────────────────────

def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return max(0, sum(1 for _ in f) - 1)
    except Exception:
        return 0


# ── 分牌谱 ──────────────────────────────────────────────────

def split_tasks(workers: int):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    done_uuids: set = set()
    # 只读主文件（启动前已 merge，分文件已清理）
    # 同时兜底读残留的分文件（异常情况）
    for fpath in glob.glob(str(DATA_DIR / 'mortal_results*.csv')):
        try:
            with open(fpath, 'r', encoding='utf-8-sig') as f:
                for row in csv.DictReader(f):
                    uid = row.get('uuid', '').strip()
                    if uid:
                        done_uuids.add(uid)
        except Exception:
            pass

    paipu_path = DATA_DIR / 'paipu_list.csv'
    with open(paipu_path, 'r', encoding='utf-8-sig') as f:
        all_paipu = list(csv.DictReader(f))

    valid_paipu = []
    skipped = 0
    for p in all_paipu:
        uid = p.get('uuid', '').strip()
        if not uid:
            skipped += 1
            continue
        valid_paipu.append(p)
    if skipped:
        print(f"  [警告] 跳过 {skipped} 条缺少 uuid 的无效牌谱记录")

    all_paipu = valid_paipu
    if not all_paipu:
        return 0, [0] * workers

    remaining  = [{k: v for k, v in p.items() if k is not None}
                  for p in all_paipu if p['uuid'] not in done_uuids]
    fieldnames = [k for k in all_paipu[0].keys() if k is not None]

    for i in range(workers):
        chunk    = remaining[i::workers]
        out_path = DATA_DIR / f'paipu_list_{i}.csv'
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(chunk)

    totals = [len(remaining[i::workers]) for i in range(workers)]
    return len(remaining), totals


# ── 合并结果（写入主文件，清理分文件）────────────────────────

def merge_and_cleanup(workers: int, console=None) -> int:
    """合并所有 worker temp 文件到主文件，然后删除分文件"""
    all_rows: dict = {}
    fieldnames = None

    # 先把主文件已有内容读进来（断点续跑时保留历史）
    main_path = DATA_DIR / 'mortal_results.csv'
    if main_path.exists():
        try:
            with open(main_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                if fieldnames is None:
                    fieldnames = reader.fieldnames
                for row in reader:
                    uid = row.get('uuid', '').strip()
                    if uid:
                        all_rows[uid] = row
        except Exception:
            pass

    # 再合并各 worker 分文件
    for fpath in glob.glob(str(DATA_DIR / 'mortal_results_*.csv')):
        try:
            with open(fpath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                if fieldnames is None:
                    fieldnames = reader.fieldnames
                for row in reader:
                    uid = row.get('uuid', '').strip()
                    if uid:
                        all_rows[uid] = row
        except Exception:
            pass

    if not all_rows or not fieldnames:
        return 0

    merged = sorted(all_rows.values(), key=lambda x: x.get('start_time', ''), reverse=True)
    with open(main_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged)

    # 清理分文件（mortal_results_N.csv 和 paipu_list_N.csv）
    for pattern in ('mortal_results_*.csv', 'paipu_list_*.csv'):
        for fpath in glob.glob(str(DATA_DIR / pattern)):
            try:
                os.remove(fpath)
            except Exception:
                pass

    msg = f"合并完成，共 {len(merged)} 条 → {main_path}"
    if console:
        console.print(f"  [green]✓ {msg}[/green]")
    else:
        print(f"✓ {msg}")
    return len(merged)


# ── Rich 进度面板 ────────────────────────────────────────────

def make_bar(done: int, total: int, width: int = 20) -> str:
    if total == 0:
        return '░' * width
    filled = int(width * done / total)
    return '█' * filled + '░' * (width - filled)


def fmt_time(seconds: float) -> str:
    s = int(seconds)
    if s < 60:
        return f"{s}秒"
    if s < 3600:
        return f"{s // 60}分{s % 60:02d}秒"
    return f"{s // 3600}小时{(s % 3600) // 60}分"


def build_panel(workers: int, totals: list, baselines: list, processes: list, start_ts: float) -> Panel:
    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold cyan",
                  padding=(0, 1))
    table.add_column("Worker",   style="cyan",  width=9,  no_wrap=True)
    table.add_column("进度条",                  width=24, no_wrap=True)
    table.add_column("完成/总计",               width=10, no_wrap=True)
    table.add_column("均速",                    width=12, no_wrap=True)
    table.add_column("预计剩余",                width=12, no_wrap=True)

    elapsed    = time.time() - start_ts
    total_done = 0
    total_all  = sum(totals)

    for i in range(workers):
        # 本次新完成数 = 当前行数 - 启动前基准行数
        done  = max(0, count_csv_rows(DATA_DIR / f'mortal_results_{i}.csv') - baselines[i])
        total = totals[i]
        total_done += done

        bar = make_bar(done, total)
        pct = f"{done / total * 100:.0f}%" if total > 0 else "—"

        finished = processes[i].poll() is not None

        if done > 0:
            avg     = elapsed / done
            avg_str = f"{avg:.0f}秒/个"
            remain  = avg * (total - done)
            if finished or done >= total:
                eta_str = "[green]✓ 完成[/green]"
            else:
                eta_str = fmt_time(remain)
        else:
            avg_str = "—"
            if finished:
                eta_str = "[yellow]⚠ 已退出[/yellow]"
            else:
                eta_str = "[dim]启动中...[/dim]"

        table.add_row(f"Worker {i+1}", f"{bar} {pct}", f"{done}/{total}", avg_str, eta_str)

    # 总计行
    bar_all = make_bar(total_done, total_all)
    pct_all = f"{total_done / total_all * 100:.0f}%" if total_all > 0 else "—"

    if total_done > 0 and total_done < total_all:
        avg_total = elapsed / total_done
        eta_total = fmt_time(avg_total * (total_all - total_done))
        avg_total_str = f"{avg_total:.0f}秒/个"
    elif total_done >= total_all > 0:
        avg_total_str = f"{elapsed / total_done:.0f}秒/个"
        eta_total = "[green]已完成[/green]"
    else:
        avg_total_str = "—"
        eta_total = "计算中..."

    table.add_section()
    table.add_row(
        "[bold]总计[/bold]",
        f"{bar_all} {pct_all}",
        f"[bold]{total_done}/{total_all}[/bold]",
        avg_total_str,
        f"{eta_total}  (用时 {fmt_time(elapsed)})",
    )

    title = f"[bold]Mortal 并行分析[/bold]  账号: [yellow]{PLAYER_NAME}[/yellow]  {workers} workers"
    return Panel(table, title=title, border_style="blue")


# ── 主流程 ───────────────────────────────────────────────────

def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else WORKER_COUNT
    console = Console()

    console.print(f"\n[bold cyan]Mortal 并行分析[/bold cyan]  "
                  f"账号: [yellow]{PLAYER_NAME}[/yellow]  "
                  f"workers: [green]{workers}[/green]\n")

    # 0. 启动前先合并残留分文件 → 主文件，保证查重数据完整
    residual = glob.glob(str(DATA_DIR / 'mortal_results_*.csv'))
    if residual:
        console.print("[bold]0/3[/bold] 合并上次残留分文件...")
        merge_and_cleanup(workers, console)
        console.print()

    # 1. 分牌谱
    console.print("[bold]1/3[/bold] 分配牌谱...")
    total_remaining, totals = split_tasks(workers)

    total_all_paipu = count_csv_rows(DATA_DIR / 'paipu_list.csv')
    already_done    = total_all_paipu - total_remaining

    console.print(f"\n  牌谱总数:   [white]{total_all_paipu}[/white]")
    console.print(f"  已分析:     [green]{already_done}[/green]")
    console.print(f"  本次剩余:   [yellow]{total_remaining}[/yellow]\n")

    for i, n in enumerate(totals):
        console.print(f"  Worker {i+1}: {n} 条")
    console.print()

    if total_remaining == 0:
        console.print("[green]✓ 所有牌谱已分析完成，无需重复分析[/green]\n")
        return

    # 2. 启动 workers
    console.print("[bold]2/3[/bold] 启动 workers...")
    baselines = [count_csv_rows(DATA_DIR / f'mortal_results_{i}.csv') for i in range(workers)]

    processes, log_files = [], []
    for i in range(workers):
        log_path = DATA_DIR / f'worker_{i}.log'
        lf = open(log_path, 'w', encoding='utf-8')
        log_files.append(lf)
        cmd = [PYTHON, str(ANALYZER), '--worker', str(i), '--headless', '--limit', '0']
        p = subprocess.Popen(cmd, stdout=lf, stderr=lf, cwd=str(SCRIPT_DIR))
        processes.append(p)
        console.print(f"  Worker {i+1} 已启动 (PID {p.pid})")

    console.print()

    # Ctrl+C 时终止所有 worker 并合并已有结果
    def on_interrupt(sig, frame):
        console.print("\n[yellow]用户中断，正在终止 workers...[/yellow]")
        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass
        for lf in log_files:
            try:
                lf.close()
            except Exception:
                pass
        console.print("[bold]合并已完成的结果...[/bold]")
        merge_and_cleanup(workers, console)
        sys.exit(0)

    signal.signal(signal.SIGINT, on_interrupt)

    # 3. 实时进度面板
    start_ts = time.time()
    with Live(build_panel(workers, totals, baselines, processes, start_ts),
              refresh_per_second=1, console=console) as live:
        while True:
            live.update(build_panel(workers, totals, baselines, processes, start_ts))
            if all(p.poll() is not None for p in processes):
                live.update(build_panel(workers, totals, baselines, processes, start_ts))
                break
            time.sleep(1)

    for lf in log_files:
        lf.close()

    # 4. 合并并清理分文件
    console.print("\n[bold]3/3[/bold] 合并结果...")
    merge_and_cleanup(workers, console)

    elapsed = time.time() - start_ts
    console.print(f"\n[bold green]✓ 全部完成！[/bold green]  总用时: {fmt_time(elapsed)}\n")


if __name__ == '__main__':
    main()
