#!/usr/bin/env python3
"""
Mortal 牌谱分析器 - 2Captcha 版本
"""

import csv
import os
import re
import sys
import time
import io
from typing import Dict, List, Optional

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

try:
    from twocaptcha import TwoCaptcha
    TWOCAPTCHA_AVAILABLE = True
except ImportError:
    TWOCAPTCHA_AVAILABLE = False
    print("⚠ 2captcha-python 未安装，安装方法: pip install 2captcha-python")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PLAYER_NAME, TWOCAPTCHA_API_KEY as _CONFIG_API_KEY


class MortalAnalyzer:
    def __init__(self, headless: bool = False, proxy: Optional[str] = None, captcha_api_key: Optional[str] = None):
        self.base_url = "https://mjai.ekyu.moe/zh-cn.html"
        self.results = []
        self.headless = headless
        self.proxy = proxy
        self.driver = None
        self.existing_uuids = set()

        if captcha_api_key and TWOCAPTCHA_AVAILABLE:
            self.solver = TwoCaptcha(captcha_api_key)
            print("✓ 2Captcha 已初始化")
        else:
            self.solver = None

    def init_browser(self):
        options = Options()
        if self.headless:
            options.headless = True
        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        if self.headless:
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-images')
            options.add_argument('--blink-settings=imagesEnabled=false')
        options.add_argument('--log-level=3')

        try:
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            from selenium.webdriver.edge.service import Service
            self.driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)
        except Exception:
            self.driver = webdriver.Edge(options=options)

        if not self.headless:
            self.driver.set_window_size(1280, 800)
        print("✓ 浏览器已启动")

    def close_browser(self):
        if self.driver:
            self.driver.quit()

    def solve_turnstile_with_2captcha(self, sitekey: str, url: str) -> Optional[str]:
        if not self.solver:
            return None
        try:
            print("  发送验证码到 2Captcha...", flush=True)
            result = self.solver.turnstile(sitekey=sitekey, url=url)
            token = result['code']
            print(f"  ✓ 验证码已解决", flush=True)
            return token
        except Exception as e:
            print(f"  ✗ 2Captcha 失败: {e}", flush=True)
            return None

    def submit_paipu(self, paipu_url: str, retry_count: int = 0, captcha_retry: int = 0) -> Optional[Dict]:
        max_retries = 3
        max_captcha_retries = 3

        try:
            self.driver.get(self.base_url)
            wait = WebDriverWait(self.driver, 30)
            url_input = wait.until(EC.presence_of_element_located((By.NAME, "log-url")))

            url_input.clear()
            url_input.send_keys(paipu_url)

            Select(self.driver.find_element(By.NAME, "engine")).select_by_value("mortal")

            try:
                show_rating = self.driver.find_element(By.NAME, "show-rating")
                if not show_rating.is_selected():
                    show_rating.click()
            except Exception:
                pass

            # 2Captcha 解决验证码
            try:
                turnstile = self.driver.find_element(By.CSS_SELECTOR, "div.cf-turnstile")
                sitekey = turnstile.get_attribute("data-sitekey")
            except Exception:
                sitekey = None

            if sitekey and self.solver:
                token = self.solve_turnstile_with_2captcha(sitekey, self.driver.current_url)
                if token:
                    try:
                        token_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='cf-turnstile-response']")
                        self.driver.execute_script("arguments[0].value = arguments[1];", token_input, token)
                        callback = turnstile.get_attribute("data-callback")
                        if callback:
                            self.driver.execute_script(f"if (typeof {callback} === 'function') {{ {callback}(); }}")
                        self.driver.execute_script(
                            "arguments[0].dispatchEvent(new Event('change', {{ bubbles: true }}));", token_input)
                        time.sleep(2)
                    except Exception as e:
                        print(f"  ⚠ 注入 token 失败: {e}", flush=True)
                else:
                    if captcha_retry < max_captcha_retries:
                        print(f"  🔄 重试验证码 ({captcha_retry + 1}/{max_captcha_retries})...", flush=True)
                        return self.submit_paipu(paipu_url, retry_count, captcha_retry + 1)
                    print("  ✗ 验证码重试耗尽，跳过", flush=True)
                    return None

            # 等待提交按钮可用
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[name='submitBtn']")
            if not submit_btn.is_enabled():
                deadline = time.time() + 30
                while time.time() < deadline:
                    time.sleep(1)
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[name='submitBtn']")
                    if submit_btn.is_enabled():
                        break
                else:
                    if captcha_retry < max_captcha_retries:
                        print(f"  🔄 按钮超时，重试验证码 ({captcha_retry + 1}/{max_captcha_retries})...", flush=True)
                        return self.submit_paipu(paipu_url, retry_count, captcha_retry + 1)
                    print("  ✗ 验证码重试耗尽，跳过", flush=True)
                    return None

            print("  提交中...", flush=True)
            self.driver.execute_script("arguments[0].click();", submit_btn)

            try:
                WebDriverWait(self.driver, 60).until(EC.url_contains("/report/"))
            except Exception:
                raise Exception("等待结果页超时(60s)，可能为无效牌谱或网络问题")
            time.sleep(3)

            result = self.extract_result()
            result['paipu_url'] = paipu_url
            return result

        except Exception as e:
            error_str = str(e).strip() or "未知错误"
            print(f"  ✗ {error_str[:120]}", flush=True)
            if retry_count < max_retries:
                print(f"  🔄 重试 ({retry_count + 1}/{max_retries})...", flush=True)
                return self.submit_paipu(paipu_url, retry_count + 1, captcha_retry)
            print("  ✗ 重试耗尽，跳过", flush=True)
            return None

    def extract_result(self) -> Dict:
        result = {'rating': None, 'match_rate': None, 'matches': None, 'total': None,
                  'report_url': self.driver.current_url}
        try:
            current_url = self.driver.current_url
            if "?data=" in current_url:
                import requests
                json_url = "https://mjai.ekyu.moe" + current_url.split("?data=")[1]
                resp = requests.get(json_url, timeout=10)
                if resp.status_code == 200:
                    review = resp.json().get('review', {})
                    if review.get('rating') is not None:
                        result['rating'] = round(review['rating'] * 100, 2)
                    result['matches'] = review.get('total_matches')
                    result['total'] = review.get('total_reviewed')
                    if result['matches'] and result['total']:
                        result['match_rate'] = round(result['matches'] / result['total'] * 100, 2)
                    print(f"  ✓ Rating: {result['rating']}, 一致率: {result['match_rate']}%", flush=True)
                    return result

            content = self.driver.page_source
            m = re.search(r'<td>Rating</td><td>([0-9.]+)</td>', content)
            if m:
                result['rating'] = float(m.group(1))
            m = re.search(r'<td>Matches/total</td><td>(\d+)/(\d+)\s*=\s*([0-9.]+)%</td>', content)
            if m:
                result['matches'] = int(m.group(1))
                result['total'] = int(m.group(2))
                result['match_rate'] = float(m.group(3))
            print(f"  ✓ Rating: {result['rating']}, 一致率: {result['match_rate']}%", flush=True)
        except Exception as e:
            print(f"  ⚠ 提取结果失败: {e}", flush=True)
        return result

    def load_existing_results(self, output_file: str = None):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(os.path.dirname(script_dir), 'data', PLAYER_NAME)

        if output_file is None:
            output_file = os.path.join(data_dir, 'mortal_results.csv')
        elif not os.path.isabs(output_file):
            output_file = os.path.join(data_dir, output_file)

        self.existing_uuids.clear()
        loaded_results = []

        main_file = os.path.join(data_dir, 'mortal_results.csv')
        if main_file != output_file and os.path.exists(main_file):
            try:
                with open(main_file, 'r', encoding='utf-8') as f:
                    for row in csv.DictReader(f):
                        uid = row.get('uuid', '').strip()
                        if uid:
                            self.existing_uuids.add(uid)
                print(f"✓ 主文件去重UUID: {len(self.existing_uuids)} 个", flush=True)
            except Exception as e:
                print(f"⚠ 读取主文件失败: {e}", flush=True)

        if not os.path.exists(output_file):
            return

        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    uid = row.get('uuid', '').strip()
                    if uid:
                        self.existing_uuids.add(uid)
                        loaded_results.append(row)
            self.results = loaded_results
            print(f"✓ 加载已有结果: {len(self.results)} 条", flush=True)
        except Exception as e:
            print(f"⚠ 加载已有结果失败: {e}", flush=True)

    def analyze_batch(self, paipu_list: List[Dict], max_count: int = 100, start_index: int = 0, temp_file: str = None):
        self.load_existing_results(temp_file)

        end_index = min(start_index + max_count, len(paipu_list)) if max_count > 0 else len(paipu_list)
        batch = paipu_list[start_index:end_index]
        need_analyze = [p for p in batch if p['uuid'] not in self.existing_uuids]
        total_need = len(need_analyze)

        print(f"\n总牌谱: {len(batch)}  已分析: {len(batch)-total_need}  待分析: {total_need}", flush=True)

        if total_need == 0:
            print("所有牌谱已分析完成", flush=True)
            return self.results

        self.init_browser()
        try:
            completed = 0
            start_ts = time.time()
            for paipu in need_analyze:
                completed += 1
                elapsed = time.time() - start_ts
                avg = elapsed / completed
                remain = avg * (total_need - completed)
                print(f"\n[{completed}/{total_need}]  均速: {avg:.0f}秒/个  预计剩余: {int(remain//60)}分{int(remain%60)}秒", flush=True)
                print(f"  {paipu['uuid']}", flush=True)

                result = self.submit_paipu(paipu['paipu_url'])
                if result:
                    result.update({
                        'uuid': paipu['uuid'],
                        'start_time': paipu['start_time'],
                        'score': paipu['score'],
                        'rank': paipu['rank'],
                        'room': paipu.get('room', 'Unknown'),
                    })
                    self.results.append(result)
                    self.existing_uuids.add(paipu['uuid'])
                    self.save_results(temp_file)
                    print("  ✓ 完成", flush=True)
                else:
                    print("  ✗ 跳过", flush=True)

                time.sleep(2)
        finally:
            self.close_browser()

        return self.results

    def save_results(self, output_path: str = None):
        if not self.results:
            return
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', PLAYER_NAME)
        if output_path is None:
            output_path = os.path.join(data_dir, 'mortal_results.csv')
        elif not os.path.isabs(output_path):
            output_path = os.path.join(data_dir, output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fieldnames = ['uuid', 'start_time', 'score', 'rank', 'room', 'rating', 'match_rate', 'matches', 'total', 'paipu_url', 'report_url']
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)
        print(f"✓ 已保存: {output_path}", flush=True)


def main():
    import argparse
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', PLAYER_NAME)

    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', '-w', type=int, default=None)
    parser.add_argument('--input', '-i', default=None)
    parser.add_argument('--output', '-o', default=None)
    parser.add_argument('--limit', '-l', type=int, default=100)
    parser.add_argument('--start', '-s', type=int, default=0)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--proxy', '-p', default=None)
    parser.add_argument('--api-key', '-k', default=None)
    parser.add_argument('--temp', '-t', default=None)
    args = parser.parse_args()

    if args.worker is not None:
        w = args.worker
        input_path  = args.input  or os.path.join(data_dir, f'paipu_list_{w}.csv')
        temp_path   = args.temp   or os.path.join(data_dir, f'mortal_results_{w}.csv')
        output_path = args.output or os.path.join(data_dir, f'mortal_results_{w}.csv')
    else:
        input_path  = args.input  or os.path.join(data_dir, 'paipu_list.csv')
        temp_path   = args.temp   or os.path.join(data_dir, 'mortal_results.csv')
        output_path = args.output or os.path.join(data_dir, 'mortal_results.csv')

    api_key = args.api_key or os.getenv('TWOCAPTCHA_API_KEY') or _CONFIG_API_KEY or None

    print("="*60)
    print(f"Mortal 分析器  账号: {PLAYER_NAME}" + (f"  Worker: {args.worker}" if args.worker is not None else ""))
    print("="*60)

    paipu_list = []
    with open(input_path, 'r', encoding='utf-8') as f:
        paipu_list = list(csv.DictReader(f))

    analyzer = MortalAnalyzer(headless=args.headless, proxy=args.proxy, captcha_api_key=api_key)
    results = analyzer.analyze_batch(paipu_list, args.limit, args.start, temp_path)
    analyzer.save_results(output_path)

    if results:
        ratings = [float(r['rating']) for r in results if r['rating']]
        match_rates = [float(r['match_rate']) for r in results if r['match_rate']]
        if ratings:
            print(f"\n成功: {len(results)} 场  平均Rating: {sum(ratings)/len(ratings):.2f}  平均一致率: {sum(match_rates)/len(match_rates):.2f}%")


if __name__ == "__main__":
    main()
