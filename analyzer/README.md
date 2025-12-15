# 📊 Mortal AI 分析模块

使用 Mortal AI 自动分析雀魂牌谱，生成详细的对局分析报告。

## 🚀 快速开始

### 1. 确认数据准备
确保 `../data/paipu_list.csv` 已由爬虫模块生成，包含待分析的牌谱列表。

### 2. 选择运行方式

#### 方式A：普通运行（推荐短时间任务）
```batch
run_all_headless.bat
```
- ✅ 后台无窗口运行
- ✅ 自动跳过已分析记录
- ✅ 使用 2Captcha 自动验证码识别
- ⚠️ 系统睡眠会暂停任务

#### 方式B：防睡眠运行（推荐长时间任务）
```batch
run_all_prevent_sleep.bat
```
- ✅ 所有普通运行的功能
- ✅ 自动禁用系统睡眠
- ✅ 可安全锁定账户或关闭显示器
- ℹ️ 完成后需手动恢复睡眠设置

## 📁 输出文件

### 主要输出
- `../data/mortal_results_temp.csv` - 分析结果（实时更新）
- `../data/mortal_results.csv` - 最终结果

### 文件字段
| 字段 | 说明 |
|------|------|
| uuid | 牌谱唯一标识 |
| start_time | 对局时间 |
| score | 得分 |
| rank | 位次 (1-4) |
| room | 房间类型（王座之间/玉之间/金之间） |
| rating | Mortal AI 评分 |
| match_rate | 与 Mortal 决策一致率 (%) |
| matches | 一致决策数 |
| total | 总决策数 |
| paipu_url | 牌谱链接 |
| report_url | Mortal 分析报告链接 |

## 🎯 进度追踪

运行时会实时显示：
- ✓ 剩余待分析数量
- ✓ 当前进度百分比
- ✓ 预计剩余时间
- ✓ 最新分析结果

## ⚙️ 配置说明

### 2Captcha API Key 配置

2Captcha用于自动识别验证码。有**三种配置方式**（任选其一）：

#### 方式1: 环境变量（推荐）⭐

**Windows 永久设置**：
1. 右键"此电脑" → 属性 → 高级系统设置 → 环境变量
2. 在"用户变量"中点击"新建"
3. 变量名: `TWOCAPTCHA_API_KEY`
4. 变量值: 你的API Key（从 https://2captcha.com 获取）
5. 确定保存并**重启命令行窗口**

**临时设置（仅当前窗口有效）**：
```batch
set TWOCAPTCHA_API_KEY=你的API_KEY
```

设置后，直接运行bat文件即可：
```batch
run_all_headless.bat
```

#### 方式2: 命令行参数

```batch
python win_mortal_analyzer_2captcha.py --api-key 你的API_KEY --headless
```

#### 方式3: 手动模式

如果不配置API Key，程序会使用**手动模式**：
- 每次遇到验证码时会弹出浏览器窗口
- 需要你手动点击完成验证
- 不推荐用于大批量分析

**注意**: 使用 `run_all_headless.bat` 时，如果未配置API Key，会自动切换到手动模式。

---

### 分析数量限制
默认处理所有记录，如需限制：
```python
python win_mortal_analyzer_2captcha.py --limit 100
```

## 🔄 去重机制

程序自动跳过已分析的牌谱：
- 读取 `mortal_results_temp.csv` 中的 UUID
- 仅分析新增的牌谱
- 支持中断后继续运行

## ⚠️ 注意事项

### 运行环境
- ✅ 锁定账户 - 程序继续运行
- ✅ 关闭显示器 - 程序继续运行
- ❌ 系统睡眠 - 程序暂停（除非使用防睡眠版本）

### 网络要求

分析数量限制

**推荐使用梯子运行脚本，时间会缩短一倍左右**

- 需要稳定的网络连接
- 访问 mjai.ekyu.moe（Mortal AI 服务）
- 访问 2captcha.com（验证码服务）

### 性能
- 平均分析速度：约 30-60 秒/局
- 建议后台运行，不影响日常使用
- Headless 模式内存占用较低

---

## 🆘 常见问题

**Q: 如何中断运行？**
A: 直接关闭命令行窗口或 Ctrl+C

**Q: 中断后如何继续？**
A: 直接重新运行，程序会自动跳过已分析记录

**Q: 为什么有些记录显示"分析失败"？**
A: 可能是网络问题、验证码识别失败或牌谱页面加载超时

**Q: 2Captcha 额度不足怎么办？**
A: 访问 https://2captcha.com 充值，或更换 API Key  跑1000谱需要约2美元 网站最低充值3美元

---

💡 **提示**: 首次运行建议先用 `--limit 10` 测试，确认流程正常后再运行全量分析。
