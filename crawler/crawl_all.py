#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整牌谱爬虫：API历史数据 + 网页最新数据 = 完整paipu_list.csv
"""
import requests
import time
import re
import csv
import os
import sys
import io
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置
API_BASE = "https://5-data.amae-koromo.com"
PLAYER_ID = 12345678          # 改为你的牌谱屋ID
PLAYER_NAME = "YourName"       # 改为你的昵称
REAL_MAJSOUL_ID = "87654321"   # 改为你的雀魂友人ID

# MODE 配置：
# - 单王座：16 (Throne)
# - 单玉：12 (Jade)
# - 单金：9 (Gold)
# - 混合（如王座+玉）：16.12
MODE = 16.12  
WEB_URL = f"https://amae-koromo.sapk.ch/player/{PLAYER_ID}/{MODE}"
PAIPU_PREFIX = "https://game.maj-soul.com/1/?paipu="

# 房间类型映射
def get_room_type(mode):
    """根据MODE获取房间类型"""
    if isinstance(mode, (int, float)):
        mode_str = str(mode)
        if '.' in mode_str:
            # 混合模式，如16.12
            parts = mode_str.split('.')
            rooms = []
            mode_map = {16: "Throne", 12: "Jade", 9: "Gold"}
            for part in parts:
                try:
                    room = mode_map.get(int(part))
                    if room:
                        rooms.append(room)
                except:
                    pass
            return "+".join(rooms) if rooms else "Unknown"
        else:
            # 单一模式
            mode_map = {16: "Throne", 12: "Jade", 9: "Gold"}
            return mode_map.get(int(mode), "Unknown")
    return "Unknown"

def crawl_api_data(limit=None):
    """从API获取历史牌谱"""
    print("\n" + "="*60, flush=True)
    print("步骤 1/2: 从 API 获取所有数据", flush=True)
    print("="*60, flush=True)

    print(f"玩家: {PLAYER_NAME} (ID: {PLAYER_ID})", flush=True)
    print(f"模式: {MODE}", flush=True)
    print(f"网页查看: https://amae-koromo.sapk.ch/player/{PLAYER_ID}/{MODE}", flush=True)
    if limit:
        print(f"数量限制: {limit}\n", flush=True)
    else:
        print(f"数量限制: 无限制（获取所有）\n", flush=True)

    # 处理混合模式：分别获取每个模式的数据
    modes_to_fetch = []
    if isinstance(MODE, float) and '.' in str(MODE):
        # 混合模式，如16.12
        parts = str(MODE).split('.')
        for part in parts:
            try:
                modes_to_fetch.append(int(part))
            except:
                pass
    else:
        # 单一模式
        modes_to_fetch = [int(MODE)]

    all_records = []

    for mode in modes_to_fetch:
        mode_name_map = {16: "王座之间", 12: "玉之间", 9: "金之间"}
        mode_name = mode_name_map.get(mode, f"mode={mode}")
        print(f"\n正在获取{mode_name}数据...", flush=True)
        mode_records = []

        # 动态生成时间段：从2020年到当前时间，按季度分段（API每次最多返回100条）
        import time as time_module
        from datetime import datetime as dt

        time_ranges = []
        start_year = 2020
        current_time = int(time_module.time() * 1000)  # 当前时间（毫秒）

        # 生成从2020年到当前的所有季度
        for year in range(start_year, dt.now().year + 2):  # +2确保覆盖未来
            for quarter in range(1, 5):  # Q1-Q4
                # 计算季度起止时间
                if quarter == 1:
                    q_start = dt(year, 1, 1)
                    q_end = dt(year, 4, 1)
                elif quarter == 2:
                    q_start = dt(year, 4, 1)
                    q_end = dt(year, 7, 1)
                elif quarter == 3:
                    q_start = dt(year, 7, 1)
                    q_end = dt(year, 10, 1)
                else:  # Q4
                    q_start = dt(year, 10, 1)
                    q_end = dt(year + 1, 1, 1)

                start_ms = int(q_start.timestamp() * 1000)
                end_ms = int(q_end.timestamp() * 1000)

                # 如果起始时间已经超过当前时间，停止生成
                if start_ms > current_time:
                    break

                time_ranges.append((start_ms, end_ms))

            # 如果已经超过当前年份，停止
            if year > dt.now().year:
                break

        for start_time, end_time in time_ranges:
            url = f"{API_BASE}/api/v2/pl4/player_records/{PLAYER_ID}/{start_time}/{end_time}"
            params = {"mode": mode}

            try:
                resp = requests.get(url, params=params, timeout=30)
                if resp.status_code == 200:
                    records = resp.json()
                    if records:
                        mode_records.extend(records)
                        start_date = datetime.fromtimestamp(start_time/1000).strftime('%Y-%m')
                        print(f"  {start_date}: {len(records)} 条", flush=True)
                    time.sleep(0.3)  # 避免请求过快
                else:
                    print(f"  获取失败，状态码: {resp.status_code}")
            except Exception as e:
                print(f"  获取失败: {e}")
                import traceback
                traceback.print_exc()

        print(f"  {mode_name}总计: {len(mode_records)} 条", flush=True)

        if len(mode_records) == 0:
            print(f"  [提示] API未返回{mode_name}数据，可能原因:", flush=True)
            print(f"        1. 该模式没有对局记录", flush=True)
            print(f"        2. API数据更新延迟（通常延迟1个月）", flush=True)
            print(f"        3. PLAYER_ID配置错误", flush=True)
            print(f"        4. 网页端可查看最新数据: https://amae-koromo.sapk.ch/player/{PLAYER_ID}/{mode}", flush=True)

        all_records.extend(mode_records)

    # 去重并排序
    unique_records = {}
    for record in all_records:
        uuid = record.get('uuid')
        if uuid and uuid not in unique_records:
            unique_records[uuid] = record

    records = list(unique_records.values())
    records.sort(key=lambda x: x.get('startTime', 0), reverse=True)

    if limit and limit > 0:
        records = records[:limit]

    print(f"\n合并去重后共 {len(records)} 条记录\n", flush=True)

    paipu_list = []
    for record in records:
        uuid = record.get('uuid')
        if not uuid:
            continue

        player_info = None
        for player in record.get('players', []):
            if player.get('accountId') == PLAYER_ID:
                player_info = player
                break

        players = record.get('players', [])
        players_sorted = sorted(players, key=lambda x: x.get('score', 0), reverse=True)
        rank = 1
        for i, p in enumerate(players_sorted):
            if p.get('accountId') == PLAYER_ID:
                rank = i + 1
                break

        # 根据每条记录的modeId确定房间类型
        mode_id = record.get('modeId', 0)
        mode_map = {16: "Throne", 12: "Jade", 9: "Gold"}
        room = mode_map.get(mode_id, "Unknown")

        paipu_list.append({
            'uuid': uuid,
            'paipu_url': f"{PAIPU_PREFIX}{uuid}_a{REAL_MAJSOUL_ID}",
            'start_time': datetime.fromtimestamp(record.get('startTime', 0)).strftime('%Y-%m-%d %H:%M:%S'),
            'score': player_info.get('score', 0) if player_info else 0,
            'rank': rank,
            'room': room,
        })

    print(f"\n[成功] 获取到 {len(paipu_list)} 条历史数据", flush=True)
    return paipu_list


def crawl_web_data():
    """从网页爬取最新牌谱"""
    print("\n" + "="*60, flush=True)
    print("步骤 2/3: 从网页获取最新数据", flush=True)
    print("="*60, flush=True)

    driver = None
    try:
        print("正在启动浏览器...", flush=True)
        options = EdgeOptions()
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])

        driver = webdriver.Edge(options=options)

        print(f"访问页面: {WEB_URL}", flush=True)
        driver.get(WEB_URL)

        print("等待页面加载...", flush=True)
        time.sleep(10)

        # 多次滚动确保加载所有数据（上下都滚动）
        print("滚动页面加载所有数据...", flush=True)

        # 先滚动到最顶部
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)

        # 向下滚动几次加载更多
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        # 最后滚回顶部，确保顶部最新数据也被加载
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)

        print("正在提取牌谱数据...", flush=True)
        page_source = driver.page_source

        # 提取时间信息
        time_pattern = r'(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})'
        time_matches = re.findall(time_pattern, page_source)

        # 提取rank（汉字或全角数字）
        # 查找 <div class="MuiBox-root css-9p3m8i">１</div> 或 <div class="MuiBox-root css-18ov3r4">４</div>
        rank_pattern = r'<div class="MuiBox-root css-[^"]+">([一二三四１２３４])</div>'
        rank_matches = re.findall(rank_pattern, page_source)

        # 转换rank
        rank_map = {
            '一': 1, '１': 1,
            '二': 2, '２': 2,
            '三': 3, '３': 3,
            '四': 4, '４': 4,
        }
        ranks = [rank_map.get(r, 0) for r in rank_matches]

        # 提取玩家分数
        # 格式: [Cl1] Traaaaa [49100] 或 [St1] メガウソッキー [22700]
        # 使用配置中的PLAYER_NAME，并转义特殊字符
        player_pattern = rf'{re.escape(PLAYER_NAME)} \[([+-]?\d+)\]'
        player_scores = re.findall(player_pattern, page_source)

        # 提取房间类型 - 根据MODE动态构建匹配模式
        # 网页HTML结构：<div aria-colindex="1" ... title="Thr">
        # 房间类型在表格第一列的 title 属性中

        # 根据MODE确定需要匹配的房间
        mode_to_room_abbr = {16: 'Thr', 12: 'Jad', 9: 'Gld'}
        allowed_rooms = []

        if isinstance(MODE, float) and '.' in str(MODE):
            # 混合模式：提取所有模式对应的房间缩写
            parts = str(MODE).split('.')
            for part in parts:
                try:
                    mode_id = int(part)
                    if mode_id in mode_to_room_abbr:
                        allowed_rooms.append(mode_to_room_abbr[mode_id])
                except:
                    pass
        else:
            # 单一模式
            mode_id = int(MODE)
            if mode_id in mode_to_room_abbr:
                allowed_rooms.append(mode_to_room_abbr[mode_id])

        # 构建动态正则（只匹配允许的房间）
        if allowed_rooms:
            room_list = '|'.join(allowed_rooms)
        else:
            room_list = 'Thr|Jad|Gld'  # 默认匹配所有

        # 匹配表格第一列的房间类型：aria-colindex="1".*?title="(Thr|Jad|Gld)"
        room_pattern = rf'aria-colindex="1"[^>]*?title="({room_list})"'
        room_matches = re.findall(room_pattern, page_source)

        # 转换房间类型
        room_map = {
            'Thr': 'Throne',
            'Jad': 'Jade',
            'Gld': 'Gold',
        }
        rooms = [room_map.get(r, 'Unknown') for r in room_matches]

        print(f"找到 {len(time_matches)} 个时间, {len(ranks)} 个rank, {len(player_scores)} 个score, {len(rooms)} 个room", flush=True)

        # 匹配牌谱链接（包含所有玩家的）
        pattern = r'mahjongsoul\.game\.yo-star\.com/\?paipu=([^"\'<>\s&]+)'
        all_matches = re.findall(pattern, page_source)

        print(f"找到 {len(all_matches)} 个牌谱链接", flush=True)

        # 只保留我们玩家的牌谱链接
        our_matches = []
        for match in all_matches:
            if f'_a{REAL_MAJSOUL_ID}' in match:
                our_matches.append(match)

        print(f"找到 {len(our_matches)} 个属于我们玩家的牌谱链接", flush=True)

        # 检查数据一致性
        expected_count = len(our_matches)

        print(f"数据一致性检查:", flush=True)
        print(f"  牌谱链接: {len(our_matches)}", flush=True)
        print(f"  时间: {len(time_matches)}", flush=True)
        print(f"  Rank: {len(ranks)}", flush=True)
        print(f"  Score: {len(player_scores)}", flush=True)
        print(f"  Room: {len(rooms)}", flush=True)

        if len(player_scores) != expected_count:
            print(f"[警告] player_scores数量({len(player_scores)})与牌谱链接数量({expected_count})不一致！", flush=True)
            print(f"[警告] 请检查PLAYER_NAME配置是否正确: {PLAYER_NAME}", flush=True)

        # 以our_matches为基准（牌谱链接数量最准确）
        # 注意：不包括time_matches，因为时间可以从UUID提取
        actual_count = min(len(our_matches), len(ranks), len(player_scores), len(rooms))

        if actual_count < expected_count:
            print(f"[警告] 数据不完整！预期{expected_count}条，实际只能处理{actual_count}条", flush=True)

        # 解析数据
        paipu_dict = {}

        for i in range(actual_count):
            match = our_matches[i]
            parts = match.split('_')
            if len(parts) >= 1:
                uuid = parts[0]
                if uuid in paipu_dict:
                    continue

                # 从UUID提取日期
                date_match = re.match(r'(\d{6})-', uuid)
                if date_match:
                    date_str = date_match.group(1)
                    year = "20" + date_str[:2]
                    month = date_str[2:4]
                    day = date_str[4:6]
                    start_time = f"{year}-{month}-{day} 00:00:00"

                    # 使用精确时间
                    if i < len(time_matches):
                        precise_time = time_matches[i].replace('/', '-')
                        start_time = precise_time + ":00"
                else:
                    start_time = "未知"

                # 获取rank、score和room（索引i对应player_scores的索引）
                rank = ranks[i] if i < len(ranks) else 0
                score = int(player_scores[i]) if i < len(player_scores) else 0
                room = rooms[i] if i < len(rooms) else 'Unknown'

                paipu_dict[uuid] = {
                    'uuid': uuid,
                    'paipu_url': f"{PAIPU_PREFIX}{uuid}_a{REAL_MAJSOUL_ID}",
                    'start_time': start_time,
                    'score': score,
                    'rank': rank,
                    'room': room,
                }

        # 按时间排序
        paipu_list = list(paipu_dict.values())
        paipu_list.sort(key=lambda x: x['start_time'], reverse=True)

        print(f"[成功] 提取到 {len(paipu_list)} 条牌谱", flush=True)

        if len(paipu_list) > 0:
            print(f"前5条:")
            for i, p in enumerate(paipu_list[:5], 1):
                print(f"  {i}. [{p['start_time']}] {p['uuid']}")

        return paipu_list

    except Exception as e:
        print(f"[错误] 网页爬取失败: {e}")
        import traceback
        traceback.print_exc()
        return []

    finally:
        if driver:
            try:
                print("关闭浏览器...")
                driver.quit()
            except Exception as e:
                print(f"关闭浏览器时出错（可忽略）: {e}")

def merge_and_save(api_data, web_data):
    """合并去重并保存（追加模式，不删除已有数据）"""
    print("\n" + "="*60, flush=True)
    print("步骤 3/3: 合并数据并去重", flush=True)
    print("="*60, flush=True)

    all_data = {}

    # 先读取已有的CSV文件（如果存在）
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    output_file = os.path.join(data_dir, 'paipu_list.csv')

    existing_count = 0
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    all_data[row['uuid']] = row
                    existing_count += 1
            print(f"已有数据: {existing_count} 条", flush=True)
        except Exception as e:
            print(f"读取已有数据失败: {e}", flush=True)

    # 添加API数据（优先级高，新增或覆盖room=Unknown的数据）
    api_new_count = 0
    api_update_count = 0
    for item in api_data:
        if item['uuid'] not in all_data:
            all_data[item['uuid']] = item
            api_new_count += 1
        elif all_data[item['uuid']].get('room') == 'Unknown':
            # 用完整的API数据覆盖不完整的网页数据
            all_data[item['uuid']] = item
            api_update_count += 1

    # 添加网页数据（只添加新的）
    web_new_count = 0
    for item in web_data:
        if item['uuid'] not in all_data:
            all_data[item['uuid']] = item
            web_new_count += 1

    print(f"API新增: {api_new_count} 条", flush=True)
    if api_update_count > 0:
        print(f"API更新: {api_update_count} 条（覆盖Unknown数据）", flush=True)
    print(f"网页新增: {web_new_count} 条", flush=True)
    print(f"合并后总计: {len(all_data)} 条", flush=True)

    # 按时间排序
    merged_list = list(all_data.values())
    merged_list.sort(key=lambda x: x['start_time'], reverse=True)

    # 尝试保存，如果文件被占用则提示
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['uuid', 'paipu_url', 'start_time', 'score', 'rank', 'room'])
                writer.writeheader()
                writer.writerows(merged_list)

            print(f"\n[成功] 已保存到: {output_file}", flush=True)
            break
        except PermissionError:
            if attempt < max_retries - 1:
                print(f"\n[警告] 文件被占用，请关闭 Excel 或其他程序中的 paipu_list.csv")
                print(f"将在5秒后重试... ({attempt + 1}/{max_retries})")
                time.sleep(5)
            else:
                print(f"\n[错误] 无法保存文件，请手动关闭以下文件后重新运行：")
                print(f"  {output_file}")
                print("\n提示：如果文件在 Excel 中打开，请先关闭 Excel")
                raise

    # 统计
    from collections import defaultdict
    month_count = defaultdict(int)
    for item in merged_list:
        month = item['start_time'][:7]
        month_count[month] += 1

    print("\n按月份统计:")
    for month in sorted(month_count.keys(), reverse=True)[:6]:
        print(f"  {month}: {month_count[month]} 条")

    print(f"\n最新5条:")
    for i, item in enumerate(merged_list[:5], 1):
        print(f"  {i}. [{item['start_time']}] {item['uuid']}")

def main(web_only=False):
    """
    主函数

    Args:
        web_only: 如果为True，只爬取网页数据（用于定时更新）
    """
    if web_only:
        print("="*60)
        print("雀魂牌谱爬虫（仅网页最新数据）")
        print("="*60)

        # 只执行网页爬取
        print("\n开始执行: 网页数据获取", flush=True)
        web_data = crawl_web_data()
        print(f"完成，获取到 {len(web_data)} 条数据", flush=True)

        # 合并保存
        if web_data:
            print("\n开始执行: 合并保存", flush=True)
            merge_and_save([], web_data)
            print("\n" + "="*60, flush=True)
            print("✓ 更新完成！", flush=True)
            print("="*60, flush=True)
        else:
            print("\n[提示] 未获取到新数据", flush=True)
    else:
        print("="*60)
        print("雀魂牌谱完整爬虫（API + 网页）")
        print("="*60)

        # 步骤1: API历史数据
        print("\n开始执行步骤1: API数据获取", flush=True)
        api_data = crawl_api_data(limit=None)
        print(f"步骤1完成，获取到 {len(api_data)} 条数据", flush=True)

        # 步骤2: 网页最新数据
        print("\n开始执行步骤2: 网页数据获取", flush=True)
        web_data = crawl_web_data()
        print(f"步骤2完成，获取到 {len(web_data)} 条数据", flush=True)

        print(f"\n数据汇总：", flush=True)
        print(f"  API获取: {len(api_data)} 条", flush=True)
        print(f"  网页获取: {len(web_data)} 条", flush=True)

        # 步骤3: 合并保存
        if api_data or web_data:
            print("\n开始执行步骤3: 合并保存", flush=True)
            merge_and_save(api_data, web_data)

            print("\n" + "="*60, flush=True)
            print("✓ 全部完成！", flush=True)
            print("="*60, flush=True)
        else:
            print("\n[错误] 未获取到任何数据", flush=True)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='雀魂牌谱爬虫')
    parser.add_argument('--web-only', action='store_true',
                        help='仅爬取网页最新数据（用于定时更新）')
    args = parser.parse_args()

    try:
        main(web_only=args.web_only)
        if not args.web_only:
            print("\n程序执行完成，3秒后退出...", flush=True)
            time.sleep(3)
    except KeyboardInterrupt:
        print("\n\n用户中断程序", flush=True)
        import sys
        sys.exit(0)
    except Exception as e:
        print(f"\n[错误] 程序异常: {e}", flush=True)
        import traceback
        traceback.print_exc()
        print("\n按回车键退出...")
        input()
        import sys
        sys.exit(1)
