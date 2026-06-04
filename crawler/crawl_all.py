#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
牌谱爬虫：API 全量历史数据，并发请求加速
"""
import requests
import time
import re
import csv
import os
import sys
import io
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 从中央配置文件读取
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PLAYER_NAME, PLAYER_ID, REAL_MAJSOUL_ID, MODE

API_BASE    = "https://5-data.amae-koromo.com"
PAIPU_PREFIX = "https://game.maj-soul.com/1/?paipu="

# 并发线程数（太高会被限速，8 是经验值）
CONCURRENCY = 8


def get_modes():
    if isinstance(MODE, float) and '.' in str(MODE):
        return [int(p) for p in str(MODE).split('.')]
    return [int(MODE)]


def fetch_segment(args):
    """单个时间段的 API 请求，供线程池调用"""
    mode, start_ms, end_ms = args
    url = f"{API_BASE}/api/v2/pl4/player_records/{PLAYER_ID}/{start_ms}/{end_ms}"
    try:
        resp = requests.get(url, params={"mode": mode}, timeout=30)
        if resp.status_code == 200:
            return resp.json() or []
    except Exception:
        pass
    return []


def crawl_api_data(limit=None):
    """并发从 API 按周分段获取全量历史牌谱"""
    print("\n" + "="*60, flush=True)
    print("从 API 获取所有数据（并发加速）", flush=True)
    print("="*60, flush=True)
    print(f"玩家: {PLAYER_NAME} (ID: {PLAYER_ID})", flush=True)
    print(f"模式: {MODE}  并发: {CONCURRENCY} 线程", flush=True)

    mode_name_map = {16: "王座之间", 12: "玉之间", 9: "金之间"}
    all_records = []

    for mode in get_modes():
        mode_name = mode_name_map.get(mode, f"mode={mode}")
        print(f"\n正在获取{mode_name}数据...", flush=True)

        # 按周分段（每周约 25-30 局，不超过 API 100 条上限）
        time_ranges = []
        seg = datetime(2022, 1, 1)
        now = datetime.now()
        while seg < now:
            end = min(seg + timedelta(days=7), now)
            time_ranges.append((mode, int(seg.timestamp() * 1000), int(end.timestamp() * 1000)))
            seg = end

        total = len(time_ranges)
        print(f"  共 {total} 个时间段，开始并发获取...", flush=True)

        mode_records = []
        completed = 0

        with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
            futures = {executor.submit(fetch_segment, args): args for args in time_ranges}
            for future in as_completed(futures):
                records = future.result()
                if records:
                    mode_records.extend(records)
                completed += 1
                if completed % 20 == 0 or completed == total:
                    print(f"  进度: {completed}/{total}  已获取: {len(mode_records)} 条", flush=True)

        print(f"  {mode_name}总计: {len(mode_records)} 条", flush=True)
        if not mode_records:
            print(f"  [提示] 未返回数据，可能原因：该模式无记录 / PLAYER_ID 有误 / API 延迟", flush=True)

        all_records.extend(mode_records)

    # 去重排序
    unique = {}
    for r in all_records:
        uid = r.get('uuid')
        if uid and uid not in unique:
            unique[uid] = r
    records = sorted(unique.values(), key=lambda x: x.get('startTime', 0), reverse=True)

    if limit and limit > 0:
        records = records[:limit]

    print(f"\n合并去重后共 {len(records)} 条记录\n", flush=True)

    paipu_list = []
    for record in records:
        uuid = record.get('uuid')
        if not uuid:
            continue

        player_info = next((p for p in record.get('players', []) if p.get('accountId') == PLAYER_ID), None)
        players_sorted = sorted(record.get('players', []), key=lambda x: x.get('score', 0), reverse=True)
        rank = next((i + 1 for i, p in enumerate(players_sorted) if p.get('accountId') == PLAYER_ID), 1)
        room = {16: "Throne", 12: "Jade", 9: "Gold"}.get(record.get('modeId', 0), "Unknown")

        paipu_list.append({
            'uuid': uuid,
            'paipu_url': f"{PAIPU_PREFIX}{uuid}_a{REAL_MAJSOUL_ID}",
            'start_time': datetime.fromtimestamp(record.get('startTime', 0)).strftime('%Y-%m-%d %H:%M:%S'),
            'score': player_info.get('score', 0) if player_info else 0,
            'rank': rank,
            'room': room,
        })

    print(f"[成功] 获取到 {len(paipu_list)} 条历史数据", flush=True)
    return paipu_list


def save(api_data):
    """保存到 CSV（追加模式，不覆盖已有数据）"""
    print("\n" + "="*60, flush=True)
    print("保存数据", flush=True)
    print("="*60, flush=True)

    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', PLAYER_NAME)
    os.makedirs(data_dir, exist_ok=True)
    output_file = os.path.join(data_dir, 'paipu_list.csv')

    all_data = {}
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    all_data[row['uuid']] = row
            print(f"已有数据: {len(all_data)} 条", flush=True)
        except Exception as e:
            print(f"读取已有数据失败: {e}", flush=True)

    new_count = 0
    for item in api_data:
        if item['uuid'] not in all_data:
            all_data[item['uuid']] = item
            new_count += 1

    merged = sorted(all_data.values(), key=lambda x: x['start_time'], reverse=True)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['uuid', 'paipu_url', 'start_time', 'score', 'rank', 'room'])
                writer.writeheader()
                writer.writerows(merged)
            print(f"新增: {new_count} 条，总计: {len(merged)} 条", flush=True)
            print(f"[成功] 已保存到: {output_file}", flush=True)
            break
        except PermissionError:
            if attempt < max_retries - 1:
                print(f"[警告] 文件被占用，5秒后重试... ({attempt + 1}/{max_retries})", flush=True)
                time.sleep(5)
            else:
                print(f"[错误] 无法保存，请关闭占用 paipu_list.csv 的程序后重试", flush=True)
                raise

    month_count = defaultdict(int)
    for item in merged:
        month_count[item['start_time'][:7]] += 1
    print("\n按月份统计（最近6个月）:")
    for month in sorted(month_count.keys(), reverse=True)[:6]:
        print(f"  {month}: {month_count[month]} 条")


def main():
    print("="*60)
    print("雀魂牌谱爬虫（API 全量）")
    print("="*60)

    api_data = crawl_api_data(limit=None)

    if api_data:
        save(api_data)
        print("\n" + "="*60, flush=True)
        print("✓ 完成！", flush=True)
        print("="*60, flush=True)
    else:
        print("\n[错误] 未获取到任何数据", flush=True)


if __name__ == "__main__":
    try:
        main()
        print("\n程序执行完成，3秒后退出...", flush=True)
        time.sleep(3)
    except KeyboardInterrupt:
        print("\n用户中断程序", flush=True)
        sys.exit(0)
    except Exception as e:
        print(f"\n[错误] 程序异常: {e}", flush=True)
        import traceback
        traceback.print_exc()
        print("\n按回车键退出...")
        input()
        sys.exit(1)
