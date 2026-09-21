#!/usr/bin/env python3
"""Scrape player records through Amae-Koromo's normal browser UI.

The records endpoint requires a CAP token.  This scraper lets the site's
headed browser flow obtain that token, then reads the rendered virtual table
while scrolling.  It does not inspect or replay the protected API requests.
"""

import argparse
import csv
import re
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs

from selenium import webdriver
from selenium.webdriver.edge.options import Options


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
PLAYER_URL = "https://amae-koromo.sapk.ch/player/{}/{}"

ROOM_NAMES = {
    "Thr": "Throne",
    "Jad": "Jade",
    "Gld": "Gold",
    "Gld E": "Gold East",
}


def load_config_defaults() -> tuple:
    try:
        import config
    except ImportError:
        return None, None, None
    return (
        getattr(config, "PLAYER_NAME", None),
        getattr(config, "PLAYER_ID", None),
        getattr(config, "MODE", None),
    )


def normalize_modes(value) -> str:
    if value is None:
        return "16,12"
    text = str(value).strip()
    if "," not in text and "." in text:
        text = text.replace(".", ",")
    return text


def make_driver() -> webdriver.Edge:
    options = Options()
    options.page_load_strategy = "none"
    options.add_argument("--window-size=1440,1000")
    return webdriver.Edge(options=options)


def wait_for_records(driver: webdriver.Edge, timeout: int) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        rows = driver.find_elements("css selector", ".ReactVirtualized__Table__row")
        links = driver.find_elements("css selector", 'a[title="View game"]')
        if rows and links:
            return
        time.sleep(2)
    body = driver.find_element("tag name", "body").text
    raise RuntimeError(
        "等待牌谱列表超时。请确认 Edge 窗口可见且 CAP 验证已完成。\n"
        + body[-800:]
    )


def rendered_rows(driver: webdriver.Edge) -> list:
    return driver.execute_script(
        """
        return [...document.querySelectorAll('.ReactVirtualized__Table__row')].map(row => {
          const cells = [...row.querySelectorAll(':scope > [role="gridcell"]')];
          const players = [...row.querySelectorAll('a[title="View game"]')].map(a => ({
            text: (a.textContent || '').trim(),
            href: a.href,
            isTarget: Boolean(a.parentElement?.querySelector('a[title="AI review"]'))
          }));
          return {
            room: (cells[0]?.textContent || '').trim(),
            rank: (cells[1]?.textContent || '').trim(),
            date: (cells[3]?.textContent || '').trim(),
            players
          };
        });
        """
    )


def parse_row(row: dict, player: str) -> Optional[dict]:
    # The target account can have older records under a previous nickname.  The
    # site marks that account with an adjacent AI-review link in every row.
    target = next((item for item in row["players"] if item.get("isTarget")), None)
    if not target:
        target = next((item for item in row["players"] if player in item["text"]), None)
    if not target:
        return None

    query = parse_qs(urlparse(target["href"]).query)
    paipu = (query.get("paipu") or [""])[0]
    if not paipu:
        return None
    uuid = paipu.split("_a", 1)[0]

    score_match = re.search(r"\[(-?\d+)\]\s*$", target["text"])
    score = int(score_match.group(1)) if score_match else 0
    rank_text = unicodedata.normalize("NFKC", row["rank"])
    rank_match = re.search(r"[1-4]", rank_text)
    rank = int(rank_match.group(0)) if rank_match else 0
    start_time = datetime.strptime(row["date"], "%Y/%m/%d %H:%M").strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return {
        "uuid": uuid,
        "paipu_url": target["href"],
        "start_time": start_time,
        "score": score,
        "rank": rank,
        "room": ROOM_NAMES.get(row["room"], row["room"]),
    }


def table_height(driver: webdriver.Edge) -> int:
    return int(
        driver.execute_script(
            """
            const tables = [...document.querySelectorAll(
              '.ReactVirtualized__Grid__innerScrollContainer'
            )];
            return tables.reduce((m, e) => Math.max(m, e.scrollHeight), 0);
            """
        )
        or 0
    )


def scrape_mode(driver: webdriver.Edge, player: str, player_id: int,
                mode: str, timeout: int) -> dict:
    url = PLAYER_URL.format(player_id, mode)
    print(f"\n打开页面: {url}", flush=True)
    driver.get(url)
    wait_for_records(driver, timeout)

    records = {}
    y = 0
    pass_number = 0
    last_height = -1
    stagnant_passes = 0

    while pass_number < 6:
        pass_number += 1
        page_height = int(driver.execute_script("return document.documentElement.scrollHeight"))
        viewport = int(driver.execute_script("return window.innerHeight"))
        step = max(350, int(viewport * 0.7))

        while y <= page_height:
            driver.execute_script("window.scrollTo(0, arguments[0])", y)
            time.sleep(0.12)
            for raw in rendered_rows(driver):
                try:
                    item = parse_row(raw, player)
                except (KeyError, ValueError):
                    continue
                if item:
                    records[item["uuid"]] = item
            y += step

        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight)")
        time.sleep(2)
        new_height = int(driver.execute_script("return document.documentElement.scrollHeight"))
        expected = round(table_height(driver) / 70) if table_height(driver) else 0
        oldest = min((item["start_time"] for item in records.values()), default="-")
        print(
            f"  第 {pass_number} 轮: {len(records)} 场"
            f" / 页面行数约 {expected}, 最早 {oldest}",
            flush=True,
        )

        if expected and len(records) >= expected:
            break
        if new_height == last_height:
            stagnant_passes += 1
        else:
            stagnant_passes = 0
        if stagnant_passes >= 2:
            break
        last_height = new_height
        y = max(0, min(page_height, new_height) - viewport * 2)

    return records


def save_records(path: Path, records: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("uuid"):
                    existing[row["uuid"]] = row
    existing.update(records)
    rows = sorted(existing.values(), key=lambda item: item["start_time"], reverse=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["uuid", "paipu_url", "start_time", "score", "rank", "room"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n已保存 {len(rows)} 场牌谱: {path}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="通过牌谱屋前端滚动抓取牌谱")
    parser.add_argument("player", nargs="?", help="雀魂昵称；省略时读取 config.py")
    parser.add_argument("--player-id", type=int, help="牌谱屋玩家 ID；省略时读取 config.py")
    parser.add_argument("--modes", help="模式列表，例如 16,12,9,8")
    parser.add_argument("--timeout", type=int, default=90, help="每个页面验证等待秒数")
    parser.add_argument("--output", type=Path, help="输出 CSV 路径")
    args = parser.parse_args()

    config_player, config_player_id, config_mode = load_config_defaults()
    player = args.player or config_player
    player_id = args.player_id or config_player_id
    if not player or not player_id:
        parser.error("请提供 player 和 --player-id，或在 config.py 中配置 PLAYER_NAME/PLAYER_ID")

    mode_text = normalize_modes(args.modes if args.modes is not None else config_mode)
    modes = [item.strip() for item in mode_text.split(",") if item.strip()]
    output = args.output or ROOT / "data" / player / "paipu_list.csv"
    print(f"玩家: {player}  牌谱屋 ID: {player_id}  模式: {','.join(modes)}")

    all_records = {}
    driver = make_driver()
    try:
        for mode in modes:
            all_records.update(scrape_mode(driver, player, player_id, mode, args.timeout))
    finally:
        driver.quit()
    save_records(output, all_records)


if __name__ == "__main__":
    main()
