# 🀄 Mortal AI 分析结果可视化

自动生成交互式图表，分析雀魂对局表现。

## 📊 功能特性

- **Rating 趋势分析** - 随时间变化的Rating曲线
- **一致率分布** - 与Mortal AI的决策一致性统计
- **排名统计** - 各名次的出现频率
- **得分分析** - 得分与Rating的关系
- **每日对局量** - 对局活跃度统计
- **关联分析** - Rating与一致率的相关性

## 🚀 快速开始

### 1. 安装依赖（首次使用）

双击运行：
```
install_requirements.bat
```

这会安装：
- pandas - 数据分析
- plotly - 交互式图表

### 2. Test with Mock Data (Recommended)

Double-click to run:
```
test_visualization.bat
```

使用60条模拟数据快速预览效果，无需等待真实数据收集！
Use 60 mock records to preview the visualization instantly!

### 3. Generate Report with Real Data

Double-click to run:
```
run_visualization.bat
```

程序会：
1. 自动读取 `mortal_results_temp.csv` 或 `mortal_results.csv`
2. 生成交互式图表
3. 创建 `mortal_dashboard.html`
4. 自动在浏览器中打开

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `visualize_mortal.py` | 核心可视化脚本 / Core visualization script |
| `test_visualization.bat` | 使用模拟数据快速测试 / Test with mock data |
| `run_visualization.bat` | 使用真实数据生成报告 / Generate report with real data |
| `install_requirements.bat` | 依赖安装脚本 / Install dependencies |
| `mock_data.csv` | 模拟数据（60条记录） / Mock data (60 records) |
| `mortal_dashboard.html` | 生成的可视化报告（运行后） / Generated HTML report |

## 📈 可视化内容

### 数据过滤

- **自动过滤异常数据**: 默认情况下，Rating < 80 的对局将被排除，确保分析质量
- **自定义过滤阈值**: 可通过命令行参数调整过滤标准

#### 自定义 Rating 阈值

如果想自定义过滤阈值，可以使用命令行参数：

```batch
# 使用默认阈值（rating >= 80）
python visualize_mortal.py

# 只统计 rating >= 85 的数据
python visualize_mortal.py --min-rating 85

# 统计所有数据，不过滤
python visualize_mortal.py --min-rating 0

# 查看帮助
python visualize_mortal.py --help
```

**修改 bat 文件**: 也可以编辑 `run_visualization.bat`，将第13行改为：
```batch
python visualize_mortal.py --min-rating 85
```

### 4个核心图表

1. **📈 Rating趋势** - 了解水平随时间的变化
2. **🏆 排名分布** - 评估各名次的稳定性
3. **📊 每日对局数** - 追踪对局活跃度
4. **🔍 Rating vs 一致率** - 分析决策质量与水平的关系

### 统计摘要

- 总对局数
- 平均/最高/最低 Rating
- 平均一致率
- 各名次占比
- 平均得分

### 详细数据表

可交互的完整数据表格，包含：
- 对局时间
- 得分
- 排名
- Rating
- 一致率

## 💡 使用建议

1. **定期分析** - 每完成一批对局后运行一次
2. **趋势观察** - 关注Rating曲线是否上升
3. **一致率提升** - 一致率低的对局值得复盘
4. **排名优化** - 分析不同排名下的表现差异

## 🔧 故障排除

### 问题1: "缺少pandas模块"
解决：运行 `install_requirements.bat`

### 问题2: "找不到CSV文件"
解决：确保上级目录有 `mortal_results_temp.csv` 或 `mortal_results.csv`

### 问题3: "没有数据"
解决：先运行爬虫脚本收集数据

## 📞 技术支持

生成的报告是纯HTML文件，可以：
- 在任何浏览器中打开
- 分享给他人查看
- 离线使用
- 图表完全交互（缩放、悬停查看详情等）

---

**提示**: 数据越多，分析结果越准确！建议至少收集30+场对局数据。
