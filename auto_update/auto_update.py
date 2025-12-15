#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Update System: Periodically crawl and analyze new paipu
"""
import subprocess
import time
import os
import sys
import csv
from datetime import datetime
import io

# Fix console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
UPDATE_INTERVAL_MINUTES = 1
LOG_FILE = "auto_update.log"

def log(message):
    """Log messages"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message, flush=True)

    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')

def get_latest_count():
    """Get current analyzed paipu count"""
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    csv_path = os.path.join(parent_dir, 'data', 'mortal_results_temp.csv')
    if not os.path.exists(csv_path):
        return 0

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f) - 1
    except:
        return 0

def run_crawler():
    """Run web crawler (web-only mode)"""
    log("Starting web crawler...")

    try:
        parent_dir = os.path.dirname(os.path.dirname(__file__))
        crawler_dir = os.path.join(parent_dir, 'crawler')
        crawler_script = os.path.join(crawler_dir, 'crawl_all.py')

        # Run crawler with --web-only mode
        result = subprocess.run(
            ['python', crawler_script, '--web-only'],
            cwd=crawler_dir,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        if result.returncode == 0:
            log("Crawler completed successfully")
            return True
        else:
            log(f"Crawler failed: {result.stderr}")
            return False

    except Exception as e:
        log(f"Crawler exception: {e}")
        return False

def run_analyzer():
    """Run Mortal analyzer (analyze new paipu only)"""
    log("Starting AI analysis...")

    try:
        parent_dir = os.path.dirname(os.path.dirname(__file__))
        analyzer_dir = os.path.join(parent_dir, 'analyzer')
        analyzer_script = os.path.join(analyzer_dir, 'win_mortal_analyzer_2captcha.py')

        # Read API key from environment variable
        api_key = os.getenv('TWOCAPTCHA_API_KEY')

        # Build command arguments
        cmd_args = [
            'python', analyzer_script,
            '--limit', '99999',
            '--headless'
        ]

        # Add API key if available
        if api_key:
            cmd_args.extend(['--api-key', api_key])
        else:
            log("[WARNING] TWOCAPTCHA_API_KEY not set, will use manual mode")

        # Run analyzer in headless mode
        result = subprocess.run(
            cmd_args,
            cwd=analyzer_dir,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        if result.returncode == 0:
            log("AI analysis completed successfully")
            return True
        else:
            log(f"AI analysis failed: {result.stderr}")
            return False

    except Exception as e:
        log(f"AI analysis exception: {e}")
        return False

def auto_update_once():
    """Execute one complete update cycle"""
    log("="*60)
    log("Starting auto update...")

    # Record count before update
    count_before = get_latest_count()
    log(f"Currently analyzed: {count_before} games")

    # 1. Crawl latest paipu
    if not run_crawler():
        log("Crawler failed, skipping this update")
        return False

    # 2. Run AI analysis
    if not run_analyzer():
        log("AI analysis failed, skipping this update")
        return False

    # 3. Calculate new additions
    count_after = get_latest_count()
    new_count = count_after - count_before

    if new_count > 0:
        log(f"Update completed: +{new_count} new analyses")
    else:
        log("Update completed: no new paipu")

    log(f"Total analyzed: {count_after} games")
    log("Auto update finished")
    log("="*60)

    return True

def main():
    """Main loop"""
    log("="*60)
    log("Auto Update System Started")
    log(f"Update interval: {UPDATE_INTERVAL_MINUTES} minutes")
    log("Press Ctrl+C to stop")
    log("="*60)

    # Execute immediately once
    auto_update_once()

    # Scheduled loop
    while True:
        try:
            # Wait for specified time
            log(f"\nNext update in: {UPDATE_INTERVAL_MINUTES} minutes")
            time.sleep(UPDATE_INTERVAL_MINUTES * 60)

            # Execute update
            auto_update_once()

        except KeyboardInterrupt:
            log("\nUser interrupted, exiting...")
            break
        except Exception as e:
            log(f"Unexpected error: {e}")
            log("Retrying in 5 minutes...")
            time.sleep(300)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f"Fatal error: {e}")
        input("\nPress Enter to exit...")
