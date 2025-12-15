# Auto Update System

Automatically crawl and analyze new paipu periodically.

## Features

- **Fully Automatic**: Background silent operation
- **Smart Deduplication**: Only analyze new paipu
- **Scheduled Execution**: Auto check every 30 minutes
- **Continuous Monitoring**: Can start on boot
- **Log Recording**: All operations logged

## Quick Start

### Method 1: Manual Start (with window)

```batch
Double click: run_auto_update.bat
```

- Display running window
- See real-time output
- Press Ctrl+C to stop

### Method 2: Background Start (no window) ⭐

```batch
Double click: run_auto_update_silent.bat
```

- Completely background operation
- No window displayed
- Check log: auto_update.log
- Stop: Task Manager, end pythonw.exe process

### Method 3: Auto Start on Boot (Most convenient) ⭐⭐⭐

**Installation:**

```batch
Right click "Run as administrator": install_auto_update_task.bat
```

**After installation:**
- Auto start on boot
- Completely background (no window)
- Auto check and analyze new paipu every 30 minutes
- Check log: auto_update.log

**Uninstall:**
1. Open "Task Scheduler"
2. Find "MortalAutoUpdate"
3. Right click → Delete

## Configuration

### Change Update Interval

Edit `auto_update.py`, modify:

```python
UPDATE_INTERVAL_MINUTES = 30  # Change to your desired minutes
```

Examples:
- `10` - Every 10 minutes (frequent)
- `30` - Every 30 minutes (default)
- `60` - Every 1 hour (moderate)
- `120` - Every 2 hours (low frequency)

### Change API Key

If 2Captcha balance is insufficient, edit `auto_update.py`:

```python
'--api-key', 'YOUR_NEW_API_KEY',  # Replace with your new API Key
```

## Workflow

```
Every 30 minutes:
1. Crawl latest web data (--web-only mode, fast!)
2. Auto deduplication (skip analyzed)
3. AI analysis on new paipu (Headless mode)
4. Save results to CSV
5. Record to log
```

## Log File

All operations are recorded in `auto_update.log`:

```
[2025-12-14 10:00:00] Starting auto update...
[2025-12-14 10:00:00] Currently analyzed: 129 games
[2025-12-14 10:00:05] Starting crawler...
[2025-12-14 10:00:15] ✓ Crawler completed
[2025-12-14 10:00:15] Starting AI analysis...
[2025-12-14 10:05:30] ✓ AI analysis completed
[2025-12-14 10:05:30] ✓ This update: +3 new analyses
[2025-12-14 10:05:30] Total analyzed: 132 games
[2025-12-14 10:05:30] Auto update completed
[2025-12-14 10:05:30] Next update in: 30 minutes
```

## Notes

### System Requirements
- Windows 10/11
- Python installed
- Edge browser (for Selenium)
- Stable network connection

### Resource Usage
- **CPU**: Low (slightly higher during analysis)
- **Memory**: ~200-500MB (Headless browser)
- **Network**: ~5-20MB per update
- **Disk**: Log file grows gradually (can be manually cleaned)

### Sleep Prevention
If computer enters sleep, task will pause. Recommend:
- Set "Never sleep" (Power options)
- Or use desktop PC running 24/7

### 2Captcha Cost
- ~1 captcha per game analysis
- ~$0.002 USD per captcha
- 100 games ≈ $0.20 USD
- 1000 games ≈ $2.00 USD

## FAQ

### Q: How to confirm it's running?
**A**:
1. Check Task Manager for pythonw.exe process
2. Check auto_update.log latest log time
3. Check mortal_results_temp.csv file modification time

### Q: How to stop auto update?
**A**:
- Method 1 (temporary): Task Manager, end pythonw.exe
- Method 2 (permanent): Task Scheduler, delete "MortalAutoUpdate"

### Q: Why no new data?
**A**:
- Maybe you haven't played new games
- Or web hasn't updated yet (usually a few minutes delay)
- Check log for specific reason

### Q: Log file too large?
**A**: Can periodically delete or clear auto_update.log, won't affect operation

### Q: Can run manual analysis at same time?
**A**: Not recommended. May cause CSV file conflicts. Suggest stop auto update first.

## Best Practices

### Recommended Setup:
1. **Install auto-start on boot** - Set and forget
2. **Set 30 minutes interval** - Balance between real-time and resources
3. **Check log periodically** - Ensure normal operation
4. **Sufficient 2Captcha balance** - At least $3+

### Use Cases:
- ✅ Desktop PC 24/7 on - Perfect
- ✅ Laptop daily use - Good
- ❌ Frequent shutdown/sleep - Not recommended

---

💡 **Tip**: First time use, recommend manually run `run_auto_update.bat` once to confirm workflow, then install auto-start.

For detailed Chinese documentation, see: [自动更新说明.md](./自动更新说明.md)
