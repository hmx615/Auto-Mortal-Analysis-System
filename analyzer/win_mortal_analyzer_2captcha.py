#!/usr/bin/env python3
"""
Windows Edge 浏览器自动化 Mortal 牌谱分析器 - 2Captcha 版本
使用 2Captcha 服务自动解决 Cloudflare Turnstile 验证码
"""

import csv
import os
import re
import sys
import time
import json
import random
import io
from datetime import datetime
from typing import Dict, List, Optional

# 设置标准输出为 UTF-8 编码，避免 emoji 和中文输出错误
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 需要安装: pip install selenium webdriver-manager 2captcha-python
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager

try:
    from twocaptcha import TwoCaptcha
    TWOCAPTCHA_AVAILABLE = True
except ImportError:
    TWOCAPTCHA_AVAILABLE = False
    print("⚠ 2captcha-python 未安装")
    print("  安装方法: pip install 2captcha-python")


class MortalAnalyzer:
    def __init__(self, headless: bool = False, proxy: Optional[str] = None, captcha_api_key: Optional[str] = None):
        self.base_url = "https://mjai.ekyu.moe/zh-cn.html"
        self.results = []
        self.headless = headless
        self.proxy = proxy
        self.driver = None
        self.captcha_api_key = captcha_api_key
        self.existing_uuids = set()  # 用于查重

        # 初始化 2Captcha solver
        if self.captcha_api_key and TWOCAPTCHA_AVAILABLE:
            self.solver = TwoCaptcha(self.captcha_api_key)
            print(f"✓ 2Captcha 已初始化")
        else:
            self.solver = None
            if not TWOCAPTCHA_AVAILABLE:
                print("⚠ 2captcha-python 未安装，将使用手动模式")
            elif not self.captcha_api_key:
                print("⚠ 未提供 2Captcha API key，将使用手动模式")

    def init_browser(self):
        """初始化 Edge 浏览器"""
        options = Options()

        if self.headless:
            options.headless = True

        # 代理设置
        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')
            print(f"使用代理: {self.proxy}")

        # 禁用一些不必要的功能以提高稳定性和性能
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # 无头模式优化：禁用不必要的功能
        if self.headless:
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-images')  # 不加载图片，节省资源
            options.add_argument('--blink-settings=imagesEnabled=false')

        # 减少日志输出
        options.add_argument('--log-level=3')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # 尝试自动下载 WebDriver
        try:
            print("正在初始化 Edge 浏览器...")
            service = Service(EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=service, options=options)
            print("✓ WebDriver 自动下载成功")
        except Exception as e:
            print(f"⚠ 自动下载失败: {e}")
            print("尝试使用系统 PATH 中的 Edge WebDriver...")
            try:
                self.driver = webdriver.Edge(options=options)
                print("✓ 使用系统 WebDriver")
            except Exception as e2:
                print(f"✗ 启动浏览器失败: {e2}")
                raise

        # 如果不是无头模式，设置窗口大小（不最大化，节省资源）
        if not self.headless:
            try:
                self.driver.set_window_size(1280, 800)
                # 移动到屏幕角落，减少干扰
                self.driver.set_window_position(0, 0)
            except:
                pass

        print("✓ Edge 浏览器已启动")

    def close_browser(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            print("✓ 浏览器已关闭")

    def solve_turnstile_with_2captcha(self, sitekey: str, url: str) -> Optional[str]:
        """使用 2Captcha 服务解决 Turnstile 验证码"""
        if not self.solver:
            print("  ⚠ 2Captcha 未配置，无法自动解决")
            return None

        try:
            print(f"  📤 发送验证码到 2Captcha...")
            print(f"     Sitekey: {sitekey[:20]}...")
            print(f"     URL: {url}")

            result = self.solver.turnstile(
                sitekey=sitekey,
                url=url
            )

            token = result['code']
            print(f"  ✓ 验证码已解决！Token: {token[:50]}...")
            return token

        except Exception as e:
            print(f"  ✗ 2Captcha 解决失败: {e}")
            return None

    def submit_paipu(self, paipu_url: str, player_id: int = 0, retry_count: int = 0) -> Optional[Dict]:
        """提交单个牌谱并获取结果"""
        max_retries = 2  # 最多重试2次

        try:
            # 访问页面
            self.driver.get(self.base_url)

            # 等待页面加载
            wait = WebDriverWait(self.driver, 30)
            url_input = wait.until(EC.presence_of_element_located((By.NAME, "log-url")))

            # 填入牌谱 URL
            url_input.clear()
            time.sleep(0.5)
            url_input.send_keys(paipu_url)
            time.sleep(0.5)

            # 选择引擎 (Mortal)
            engine_select = Select(self.driver.find_element(By.NAME, "engine"))
            engine_select.select_by_value("mortal")
            time.sleep(0.5)

            # 勾选显示 rating
            try:
                show_rating = self.driver.find_element(By.NAME, "show-rating")
                if not show_rating.is_selected():
                    show_rating.click()
            except:
                pass

            # 滚动到提交按钮区域，确保可见
            try:
                submit_area = self.driver.find_element(By.CSS_SELECTOR, "button[name='submitBtn']")
                # 滚动到元素位置
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", submit_area)
                time.sleep(1)
                # 滚动到页面顶部，避免遮挡
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(0.5)
                # 再次滚动到按钮，确保在视野中但不被遮挡
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_area)
                time.sleep(0.5)
            except:
                pass

            # 使用 2Captcha 解决验证码
            if self.solver:
                print("  🔍 查找 Turnstile 验证码参数...")

                # 查找 Turnstile 容器并提取 sitekey
                turnstile_container = None
                sitekey = None

                try:
                    turnstile_container = self.driver.find_element(By.CSS_SELECTOR, "div.cf-turnstile")
                    sitekey = turnstile_container.get_attribute("data-sitekey")
                    print(f"  ✓ 找到 Turnstile 容器")
                    print(f"     Sitekey: {sitekey}")
                except Exception as e:
                    print(f"  ✗ 未找到 Turnstile 容器: {e}")

                if sitekey:
                    # 使用 2Captcha 解决验证码
                    token = self.solve_turnstile_with_2captcha(sitekey, self.driver.current_url)

                    if token:
                        # 注入 token 到页面
                        print("  💉 注入 token 到页面...")

                        # 查找隐藏的 token 输入框
                        try:
                            # Turnstile 通常会创建一个隐藏的 input 字段来存储 token
                            token_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='cf-turnstile-response']")

                            # 使用 JavaScript 设置 token
                            self.driver.execute_script(
                                "arguments[0].value = arguments[1];",
                                token_input,
                                token
                            )

                            print("  ✓ Token 已注入！")

                            # 获取 callback 函数名
                            callback_name = turnstile_container.get_attribute("data-callback")

                            if callback_name:
                                print(f"  🔔 调用 callback 函数: {callback_name}()")
                                try:
                                    # 调用 callback 函数
                                    self.driver.execute_script(f"if (typeof {callback_name} === 'function') {{ {callback_name}(); }}")
                                    print(f"  ✓ Callback 已调用！")
                                except Exception as e:
                                    print(f"  ⚠ 调用 callback 失败: {e}")

                            # 触发 change 事件
                            self.driver.execute_script(
                                "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                                token_input
                            )

                            # 等待验证完成
                            time.sleep(2)

                        except Exception as e:
                            print(f"  ⚠ 注入 token 失败: {e}")
                            print("  尝试直接提交...")

            else:
                # 手动模式：等待用户点击
                print("  等待验证码通过...")
                print("  >>> 请在浏览器中手动点击验证码框 <<<")
                print("  >>> 验证码通常在提交按钮上方 <<<")

                max_wait = 180
                start_time = time.time()

                while time.time() - start_time < max_wait:
                    try:
                        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[name='submitBtn']")
                        if submit_btn.is_enabled():
                            print("  ✓ 验证码已通过！")
                            break
                    except:
                        pass
                    time.sleep(1)

            # 检查提交按钮是否可用
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[name='submitBtn']")
            if not submit_btn.is_enabled():
                print("  ⚠ 提交按钮未启用，等待...")
                time.sleep(2)

            # 使用 JavaScript 点击（更可靠，不受页面滚动影响）
            print("  提交中...")
            try:
                # 滚动确保按钮在视野中
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
                time.sleep(0.3)
                # 使用 JavaScript 直接点击，避免被遮挡
                self.driver.execute_script("arguments[0].click();", submit_btn)
                print("  ✓ 已提交")
            except Exception as e:
                print(f"  ⚠ JavaScript 点击失败，尝试常规点击: {e}")
                # 降级到常规点击
                submit_btn.click()

            # 等待跳转到结果页面（最多等待5分钟）
            WebDriverWait(self.driver, 300).until(
                EC.url_contains("/report/")
            )

            # 等待结果加载完成
            time.sleep(3)

            # 提取结果
            result = self.extract_result()
            result['paipu_url'] = paipu_url
            return result

        except Exception as e:
            print(f"  错误: {e}")

            # 保存错误截图
            try:
                self.driver.save_screenshot(f"error_{datetime.now().strftime('%H%M%S')}.png")
            except:
                pass

            # 如果是点击被遮挡的错误，且未达到重试次数，则重试
            if "click intercepted" in str(e) and retry_count < max_retries:
                print(f"  🔄 检测到点击被遮挡，重试 ({retry_count + 1}/{max_retries})...")
                time.sleep(2)
                return self.submit_paipu(paipu_url, player_id, retry_count + 1)

            return None

    def extract_result(self) -> Dict:
        """从结果页面提取 rating 和一致率"""
        result = {
            'rating': None,
            'match_rate': None,
            'matches': None,
            'total': None,
            'report_url': self.driver.current_url,
        }

        try:
            current_url = self.driver.current_url

            # 方法1: 尝试从JSON直接获取
            if "?data=" in current_url:
                json_path = current_url.split("?data=")[1]
                json_url = f"https://mjai.ekyu.moe{json_path}"

                print(f"  正在从JSON获取数据: {json_path}")

                try:
                    import requests
                    response = requests.get(json_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        review = data.get('review', {})

                        rating_raw = review.get('rating')
                        if rating_raw is not None:
                            result['rating'] = round(rating_raw * 100, 2)

                        result['matches'] = review.get('total_matches')
                        result['total'] = review.get('total_reviewed')

                        if result['matches'] and result['total']:
                            result['match_rate'] = round(result['matches'] / result['total'] * 100, 2)

                        print(f"  ✓ Rating: {result['rating']}, 一致率: {result['match_rate']}% ({result['matches']}/{result['total']})")
                        return result

                except Exception as e:
                    print(f"  JSON提取失败: {e}")
                    print(f"  尝试从HTML提取...")

            # 方法2: 从HTML提取（备用方法）
            content = self.driver.page_source

            rating_match = re.search(r'<td>Rating</td><td>([0-9.]+)</td>', content)
            if rating_match:
                result['rating'] = float(rating_match.group(1))

            matches_match = re.search(r'<td>Matches/total</td><td>(\d+)/(\d+)\s*=\s*([0-9.]+)%</td>', content)
            if matches_match:
                result['matches'] = int(matches_match.group(1))
                result['total'] = int(matches_match.group(2))
                result['match_rate'] = float(matches_match.group(3))

            print(f"  ✓ Rating: {result['rating']}, 一致率: {result['match_rate']}%")

        except Exception as e:
            print(f"  提取结果错误: {e}")

        return result

    def load_existing_results(self, output_file: str = "data/mortal_results_temp.csv"):
        """加载已存在的分析结果，用于查重和恢复"""
        # 确保路径正确（相对于项目根目录的data文件夹）
        if not os.path.isabs(output_file):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir)
            output_file = os.path.join(parent_dir, output_file)

        if not os.path.exists(output_file):
            print(f"  未找到已有结果文件: {output_file}")
            return

        # 清空现有数据，避免重复累加
        self.existing_uuids.clear()
        loaded_results = []

        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    uuid = row.get('uuid', '').strip()
                    if uuid:  # 确保UUID不为空
                        self.existing_uuids.add(uuid)
                        loaded_results.append(row)

            # 重新设置results（避免重复累加）
            self.results = loaded_results

            print(f"✓ 加载已有结果: {len(self.results)} 条", flush=True)
            print(f"✓ 查重数据库: {len(self.existing_uuids)} 个UUID", flush=True)
        except Exception as e:
            print(f"⚠ 加载已有结果失败: {e}", flush=True)

    def analyze_batch(self, paipu_list: List[Dict], max_count: int = 100, start_index: int = 0):
        """批量分析牌谱"""
        # 先加载已有结果用于查重
        self.load_existing_results("data/mortal_results_temp.csv")

        # 自动处理到列表末尾
        end_index = min(start_index + max_count, len(paipu_list)) if max_count > 0 else len(paipu_list)

        # 预先去重统计
        batch_to_analyze = paipu_list[start_index:end_index]
        need_analyze = []
        already_exist = 0

        for paipu in batch_to_analyze:
            if paipu['uuid'] in self.existing_uuids:
                already_exist += 1
            else:
                need_analyze.append(paipu)

        total_need = len(need_analyze)

        print(f"\n{'='*60}", flush=True)
        print(f"去重统计", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"总牌谱数: {len(batch_to_analyze)} 条", flush=True)
        print(f"已分析过: {already_exist} 条", flush=True)
        print(f"需要分析: {total_need} 条", flush=True)
        print(f"{'='*60}\n", flush=True)

        if total_need == 0:
            print("所有牌谱已分析完成，无需重复分析", flush=True)
            return self.results

        self.init_browser()

        try:
            completed = 0
            start_time = time.time()

            for i, paipu in enumerate(batch_to_analyze):
                actual_index = start_index + i
                uuid = paipu['uuid']

                # 查重检查
                if uuid in self.existing_uuids:
                    continue

                completed += 1

                # 计算进度
                progress = (completed / total_need) * 100

                # 简易进度条
                bar_length = 30
                filled = int(bar_length * completed / total_need)
                bar = '█' * filled + '░' * (bar_length - filled)

                print(f"\n[{completed}/{total_need}] {bar} {progress:.1f}%", flush=True)

                # 计算预计时间（实时显示）
                elapsed_time = time.time() - start_time
                avg_time_per_item = elapsed_time / completed
                remaining_items = total_need - completed
                estimated_time_left = avg_time_per_item * remaining_items

                # 格式化剩余时间
                if estimated_time_left < 60:
                    time_str = f"{int(estimated_time_left)}秒"
                elif estimated_time_left < 3600:
                    minutes = int(estimated_time_left / 60)
                    seconds = int(estimated_time_left % 60)
                    time_str = f"{minutes}分{seconds}秒"
                else:
                    hours = int(estimated_time_left / 3600)
                    minutes = int((estimated_time_left % 3600) / 60)
                    time_str = f"{hours}小时{minutes}分"

                # 显示平均每个用时和预计剩余时间
                print(f"  平均用时: {avg_time_per_item:.1f}秒/个", flush=True)
                print(f"  预计剩余时间: {time_str}", flush=True)

                print(f"  正在分析: {uuid}", flush=True)
                print(f"  时间: {paipu['start_time']}, 名次: {paipu['rank']}, 得分: {paipu['score']}", flush=True)

                result = self.submit_paipu(paipu['paipu_url'])

                if result:
                    result.update({
                        'uuid': paipu['uuid'],
                        'start_time': paipu['start_time'],
                        'score': paipu['score'],
                        'rank': paipu['rank'],
                        'room': paipu.get('room', 'Unknown'),  # 添加房间信息
                    })
                    self.results.append(result)
                    self.existing_uuids.add(uuid)  # 添加到查重集合
                    self.save_results("data/mortal_results_temp.csv")
                    print(f"  ✓ 分析完成", flush=True)
                else:
                    print(f"  ✗ 分析失败，跳过", flush=True)

                time.sleep(2)

        finally:
            self.close_browser()

        return self.results

    def save_results(self, output_path: str):
        """保存结果到 CSV"""
        if not self.results:
            return

        # 确保路径正确（相对于项目根目录）
        if not os.path.isabs(output_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir)
            output_path = os.path.join(parent_dir, output_path)

        # 确保data目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        fieldnames = ['uuid', 'start_time', 'score', 'rank', 'room', 'rating', 'match_rate', 'matches', 'total', 'paipu_url', 'report_url']

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)

        print(f"✓ 结果已保存到: {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Windows Edge Mortal AI 牌谱分析器 - 2Captcha版')
    parser.add_argument('--input', '-i', default='data/paipu_list.csv', help='输入牌谱列表 CSV')
    parser.add_argument('--output', '-o', default='data/mortal_results.csv', help='输出结果 CSV')
    parser.add_argument('--limit', '-l', type=int, default=100, help='分析数量限制')
    parser.add_argument('--start', '-s', type=int, default=0, help='起始索引')
    parser.add_argument('--headless', action='store_true', help='无头模式')
    parser.add_argument('--proxy', '-p', help='代理服务器')
    parser.add_argument('--api-key', '-k', help='2Captcha API Key')

    args = parser.parse_args()

    # 如果没有提供API key，从环境变量或配置文件读取
    api_key = args.api_key or os.getenv('TWOCAPTCHA_API_KEY')

    if not api_key:
        print("="*60)
        print("⚠️  未提供 2Captcha API Key")
        print("="*60)
        print("使用方法：")
        print("1. 注册 2Captcha: https://2captcha.com")
        print("2. 获取 API Key")
        print("3. 运行时添加参数: --api-key YOUR_API_KEY")
        print("   或设置环境变量: set TWOCAPTCHA_API_KEY=YOUR_API_KEY")
        print()
        print("将使用手动模式继续...")
        print("="*60)
        print()

    print("="*60)
    print("Windows Edge Mortal AI 牌谱分析器 - 2Captcha版")
    print("="*60)

    # 读取牌谱列表
    input_path = args.input
    if not os.path.isabs(input_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        input_path = os.path.join(parent_dir, input_path)

    paipu_list = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            paipu_list.append(row)

    actual_count = min(args.limit, len(paipu_list) - args.start)
    print(f"读取到 {len(paipu_list)} 条牌谱")
    print(f"将从第 {args.start} 条开始，最多分析 {args.limit} 条 (实际处理 {actual_count} 条)")
    print()

    # 分析
    analyzer = MortalAnalyzer(headless=args.headless, proxy=args.proxy, captcha_api_key=api_key)
    results = analyzer.analyze_batch(paipu_list, args.limit, args.start)

    # 保存最终结果（save_results会自动处理路径）
    analyzer.save_results(args.output)

    # 打印统计
    if results:
        ratings = [float(r['rating']) for r in results if r['rating']]
        match_rates = [float(r['match_rate']) for r in results if r['match_rate']]

        if ratings:
            print(f"\n{'='*60}")
            print("统计结果")
            print(f"{'='*60}")
            print(f"成功分析: {len(results)} 场")
            print(f"平均 Rating: {sum(ratings)/len(ratings):.2f}")
            print(f"平均一致率: {sum(match_rates)/len(match_rates):.2f}%")


if __name__ == "__main__":
    main()
