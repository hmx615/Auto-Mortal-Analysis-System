# 🀄 雀魂 Mortal AI 自动分析系统

<div align="center">
**作者**: Senseless / Northwestern Polytechnical University
**项目**: Mahjong Soul Mortal AI Analysis System
**许可证**: MIT License

---

</div>

一套完整的雀魂牌谱自动化分析工具，从爬取牌谱到AI分析再到可视化展示，全流程自动化。

## 🌟 功能特点

- ✅ **全自动爬取**: 从牌谱屋API和网页获取所有历史牌谱
- ✅ **AI智能分析**: 使用Mortal AI分析每一局，给出评分和一致率
- ✅ **数据可视化**: 生成精美的交互式图表，分析你的表现
- ✅ **自动更新**: 支持定时自动爬取和分析新牌谱（可选）⭐
- ✅ **去重机制**: 智能跳过已分析的牌谱，支持中断续传
- ✅ **无人值守**: Headless模式 + 2Captcha自动验证码识别

## 📁 项目结构

```
mortal-analysis-en/
├── crawler/            # 牌谱爬取模块 (Web Crawler)
│   ├── crawl_all.py    # 爬虫主程序（API + 网页）
│   ├── run_crawl.bat   # 一键运行爬虫
│   ├── README.md       # 爬虫说明文档
│   └── 如何获取ID.md   # ID获取详细教程
│
├── analyzer/           # Mortal AI 分析模块 (AI Analyzer)
│   ├── win_mortal_analyzer_2captcha.py  # 分析主程序
│   ├── run_all_headless.bat            # 后台运行分析
│   ├── run_all_prevent_sleep.bat       # 防睡眠版本
│   └── README.md                       # 分析说明文档
│
├── visualization/      # 数据可视化模块 (Data Visualization)
│   ├── visualize_mortal.py       # 可视化主程序
│   ├── run_visualization.bat     # 一键生成报告
│   └── install_requirements.bat  # 安装依赖
│
├── auto_update/        # 自动更新模块 (Auto Update) ⭐
│   ├── auto_update.py                # 自动更新主程序
│   ├── run_auto_update.bat           # 手动启动
│   ├── install_auto_update.bat       # 安装为开机自启
│   └── 自动更新说明.md                # 详细说明
│
├── data/               # 数据文件夹（自动生成）
│   ├── paipu_list.csv           # 牌谱列表
│   └── mortal_results_temp.csv  # 分析结果
│
├── install_all_requirements.bat      # 一键安装所有依赖 ⭐
└── README.md                         # 本文件
```

## 🚀 快速开始

### 第零步: 安装依赖 ⭐

```batch
双击运行: install_all_requirements.bat
```

- 自动安装所有需要的Python包
- 使用清华源镜像（国内用户速度快）
- 只需运行一次

### 第一步: 配置玩家ID

1. 获取你的两个ID（详见 `爬虫部分/如何获取ID.md`）:
   - **PLAYER_ID**: 牌谱屋账号ID（用于API查询）
   - **REAL_MAJSOUL_ID**: 雀魂友人ID（用于Mortal分析）⭐

2. 编辑 `爬虫部分/crawl_all.py`，修改配置:
   ```python
   PLAYER_ID = 11351776          # 改为你的牌谱屋ID
   PLAYER_NAME = "Traaaaa"       # 改为你的昵称
   REAL_MAJSOUL_ID = "33734565"  # 改为你的雀魂ID⭐
   MODE = 16.12                  # 房间模式（16=王座, 12=玉, 16.12=混合）
   ```

3. **⚠️ 安全提示**:
   - 如果你fork了本项目，**不要将修改后的配置提交到GitHub**
   - `.gitignore` 已配置排除数据文件，但请注意不要修改源代码中的示例ID
   - 建议使用环境变量或单独的配置文件存储敏感信息

### 第二步: 爬取牌谱

```batch
cd crawler
双击运行: run_crawl.bat
```

- 会自动爬取所有历史牌谱
- 输出文件: `data/paipu_list.csv`
- 首次运行建议使用有线网络或VPN（更稳定）

### 第三步: 配置2Captcha API Key（可选）

2Captcha用于自动识别验证码。有**三种配置方式**（任选其一）：

#### 方式1: 设置环境变量（推荐）⭐

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

#### 方式2: 运行时传参数

```batch
cd analyzer
python win_mortal_analyzer_2captcha.py --api-key 你的API_KEY --headless
```

#### 方式3: 手动模式

如果不配置API Key，程序会使用手动模式，需要你手动输入验证码（不推荐）。

---

### 第四步: AI分析

```batch
cd analyzer
双击运行: run_all_headless.bat
```

- 自动分析所有牌谱（跳过已分析的）
- 输出文件: `data/mortal_results_temp.csv`
- 建议使用VPN，速度快一倍左右
- 费用: 1000局约$2 USD（2Captcha验证码费用）
- **注意**: 如果未配置API Key，将使用手动模式

### 第五步: 可视化

```batch
cd visualization
双击运行: run_visualization.bat
```

- 自动生成交互式HTML报告
- 包含3个图表: 位次分布、Rating/一致率趋势、Rating vs位次分析
- 浏览器自动打开报告

### （可选）第六步: 开启自动更新 ⭐

如果想要实现持续自动监控和分析：

```batch
cd auto_update
右键"以管理员身份运行": install_auto_update.bat
```

安装时可选择更新间隔：
- 每6小时（推荐）
- 每12小时（默认）
- 每24小时
- 自定义间隔

安装后：
- 开机自动启动
- 后台静默运行
- 自动爬取新牌谱并分析
- 日志保存在 `auto_update.log`

详见 [自动更新说明.md](./自动更新部分/自动更新说明.md)

---

## 📊 输出说明

### 1. 牌谱列表 (`data/paipu_list.csv`)

| 字段 | 说明 |
|------|------|
| uuid | 牌谱唯一标识 |
| paipu_url | 雀魂牌谱链接 |
| start_time | 对局时间 |
| score | 得分 |
| rank | 位次 (1-4) |
| room | 房间类型（王座之间/玉之间/金之间） |

### 2. 分析结果 (`data/mortal_results_temp.csv`)

| 字段 | 说明 |
|------|------|
| uuid | 牌谱唯一标识 |
| start_time | 对局时间 |
| score | 得分 |
| rank | 位次 |
| room | 房间类型 |
| rating | Mortal AI 评分 (0-100) |
| match_rate | 与Mortal决策一致率 (%) |
| matches | 一致决策数 |
| total | 总决策数 |
| paipu_url | 牌谱链接 |
| report_url | Mortal分析报告链接 |

### 3. 可视化报告 (`可视化部分/mortal_dashboard.html`)

- **位次分布**: 饼图展示1st/2nd/3rd/4th占比
- **Rating & 一致率趋势**: 双轴时间序列图，展示Rating和一致率变化
- **Rating vs 位次**: 散点图+线性回归，分析Rating与位次的相关性
- **详细数据表**: 可按时间/Rating排序，支持点击链接查看Mortal分析

---

## ⚙️ 系统要求

### ⚠️ 重要: 文件路径要求
- **必须使用纯英文路径**: 项目文件夹路径中不能包含中文字符
- **Windows任务计划程序限制**: 中文路径会导致自动更新功能无法正常运行
- **推荐路径示例**: `C:\mortal-analysis\` 或 `D:\Projects\mortal-analysis\`
- **错误路径示例**: `C:\Users\用户名\Desktop\雀魂分析\` ❌

### 必需:
- **操作系统**: Windows 10/11
- **Python**: 3.8 - 3.12（⚠️ 不支持 3.13+，存在兼容性问题）
- **浏览器**: Microsoft Edge
- **网络**: 稳定的互联网连接

### 可选:
- **VPN/梯子**: 强烈推荐，速度提升约50%
- **2Captcha账号**: 用于自动验证码识别（需自行注册，见第三步配置说明）

### Python依赖:

**一键安装所有依赖**（推荐）⭐:
```batch
双击运行: install_all_requirements.bat
```
这将自动安装所有模块需要的依赖包（使用清华源，适合国内用户）

**或分别安装各模块依赖**:

#### 爬虫部分:
```batch
cd crawler
双击运行: install_requirements.bat
```
安装包: requests, selenium

#### 分析部分:
```batch
cd analyzer
双击运行: install_requirements.bat
```
安装包: selenium, requests, pandas

#### 可视化部分:
```batch
cd visualization
双击运行: install_requirements.bat
```
安装包: pandas, plotly, numpy, scipy

#### 自动更新部分:
```batch
cd auto_update
双击运行: install_requirements.bat
```
安装包: requests, selenium, pandas

---

## 💡 使用技巧

### 1. 如何只分析特定房间？

编辑 `爬虫部分/crawl_all.py`:
```python
MODE = 16      # 只分析王座之间
MODE = 12      # 只分析玉之间
MODE = 16.12   # 分析王座+玉（混合模式）
```

### 2. 如何中断后继续？

直接重新运行，程序会自动跳过已分析的牌谱。

### 3. 如何防止电脑睡眠？

使用防睡眠版本:
```batch
cd analyzer
双击运行: run_all_prevent_sleep.bat
```

### 4. 如何查看分析进度？

运行窗口会实时显示:
- 剩余待分析数量
- 当前进度百分比
- 预计剩余时间
- 最新分析结果

### 5. 如何开启自动更新？

详见 [自动更新说明.md](./自动更新部分/自动更新说明.md)，支持:
- 手动启动
- 后台静默运行
- 开机自启

---

## 📈 性能参考

| 项目 | 时间/费用 |
|------|-----------|
| 爬取1000局牌谱 | 约5-10分钟 |
| 分析1局牌谱 | 约30-60秒 |
| 分析1000局牌谱 | 约8-16小时 |
| 2Captcha费用 | 1000局约$2 USD |
| 生成可视化报告 | 约5-10秒 |

**优化建议**:
- 使用VPN/梯子 → 速度提升约50%
- Headless模式 → 节省内存约30%
- 防睡眠模式 → 可放心离开电脑

---

## ⚠️ 常见问题

### Q: 需要付费吗？
**A**:
- 工具本身完全免费
- 仅2Captcha验证码识别服务收费（约$0.002/次）
- 需自行注册2Captcha账号并配置API Key（见第三步）

### Q: 2Captcha额度不足怎么办？
**A**:
- 访问 https://2captcha.com 充值
- 最低充值$3，可分析约1500局
- 配置方法详见"第三步: 配置2Captcha API Key"

### Q: 可以分析别人的牌谱吗？
**A**:
- 可以！只需修改配置中的两个ID
- 前提是对方牌谱公开

### Q: 为什么有些牌谱分析失败？
**A**:
- 网络问题（建议使用VPN）
- 验证码识别失败（2Captcha偶尔会失败，重试即可）
- 牌谱页面加载超时（程序会自动跳过）

### Q: 数据安全吗？
**A**:
- 所有数据存储在本地
- 不上传到任何服务器
- 仅访问公开的牌谱数据

### Q: Python 3.13 运行报错怎么办？
**A**:
- Python 3.13 是较新版本，部分依赖库（如 2captcha-python、selenium）可能存在兼容性问题
- 错误表现：`2Captcha 解决失败：timeout 120.0 exteded` 或空错误信息 `错误： Message：`
- **解决方案**：降级到 Python 3.10 - 3.12 版本
- 推荐使用 Python 3.11 或 3.12（稳定性最佳）

---

## 🔗 相关链接

- **牌谱屋**: https://amae-koromo.sapk.ch
- **雀魂官网**: https://game.maj-soul.com
- **Mortal AI**: https://mjai.ekyu.moe
- **2Captcha**: https://2captcha.com

---

## 📝 更新日志

### v1.1 (2025-12-18)
- 🐛 修复 2Captcha 验证码超时后未正确处理的问题
- 🐛 修复提交按钮未启用时只等待2秒的问题（改为最多30秒）
- ✅ 添加验证码失败后的自动重试机制（最多重试2次）
- ✅ 改进错误日志输出，空错误信息现在会显示具体原因
- ✅ 添加超时错误的自动重试
- ⚠️ 明确 Python 版本要求：3.8 - 3.12（不支持 3.13+）

### v1.0 (2025-12-16)
- ✅ 完整的爬虫功能（API + 网页）
- ✅ Mortal AI自动分析
- ✅ 交互式可视化报告
- ✅ 自动更新系统 ⭐
- ✅ 完善的文档

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## 📄 许可证

MIT License - 自由使用，欢迎分享

---

## 💖 捐赠支持

如果这个项目对你有帮助，欢迎通过支付宝请我喝杯咖啡！☕（毕业论文期间临时肝出来的项目

您的支持是我持续维护和改进项目的动力！

 <img src="https://s2.loli.net/2025/12/16/aFn7lhTEBGHJyLb.png" alt="支付宝" />

